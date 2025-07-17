"""Views and utilities for order fulfillment functionality."""

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.response import Response

from InvenTree.mixins import ListAPI, CreateAPI
from InvenTree.permissions import RolePermission
from order.models import SalesOrder, SalesOrderLineItem
from order.serializers import SalesOrderSerializer
from order.status_codes import SalesOrderStatusGroups
from stock.models import StockItem
from part.models import Part


class FulfillmentSalesOrderSerializer(SalesOrderSerializer):
    """Simplified serializer for sales orders in fulfillment view."""
    
    class Meta:
        model = SalesOrder
        fields = [
            'pk',
            'reference', 
            'customer',
            'customer_detail',
            'status',
            'status_custom_key',
            'line_items',
            'completed_lines',
            'description'
        ]
        
    customer_detail = serializers.SerializerMethodField()
    
    def get_customer_detail(self, obj):
        """Return customer details."""
        if obj.customer:
            return {
                'pk': obj.customer.pk,
                'name': obj.customer.name,
                'image': obj.customer.image.url if obj.customer.image else None
            }
        return None


class FulfillmentScanSerializer(serializers.Serializer):
    """Serializer for scanning items during fulfillment."""
    
    barcode = serializers.CharField(
        required=True,
        help_text=_('Scanned barcode data')
    )
    
    sales_order = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrder.objects.all(),
        required=True,
        help_text=_('Sales order to fulfill')
    )
    
    line_item = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrderLineItem.objects.all(),
        required=False,
        allow_null=True,
        help_text=_('Specific line item to fulfill')
    )
    
    override_part = serializers.PrimaryKeyRelatedField(
        queryset=Part.objects.all(),
        required=False,
        allow_null=True,
        help_text=_('Override part for substitution')
    )
    
    confirm_substitution = serializers.BooleanField(
        default=False,
        help_text=_('Confirm that substitution is intentional')
    )


class FulfillmentMarkUnavailableSerializer(serializers.Serializer):
    """Serializer for marking line items as unavailable."""
    
    line_item = serializers.PrimaryKeyRelatedField(
        queryset=SalesOrderLineItem.objects.all(),
        required=True,
        help_text=_('Line item to mark as unavailable')
    )
    
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Notes about why item is unavailable')
    )


class FulfillmentSalesOrderList(ListAPI):
    """List view for sales orders that need fulfillment."""
    
    queryset = SalesOrder.objects.all()
    serializer_class = FulfillmentSalesOrderSerializer
    permission_classes = [RolePermission]
    
    role_required = 'sales_order.view'
    
    def get_queryset(self):
        """Return only sales orders that need fulfillment."""
        queryset = super().get_queryset()
        
        # Only show orders that are in progress and not fully shipped
        queryset = queryset.filter(
            status__in=SalesOrderStatusGroups.OPEN
        ).exclude(
            completed_lines__gte=models.F('line_items')
        )
        
        return queryset.prefetch_related('customer')


class FulfillmentScanView(CreateAPI):
    """Handle barcode scanning for order fulfillment."""
    
    serializer_class = FulfillmentScanSerializer
    permission_classes = [RolePermission]
    
    role_required = 'sales_order.change'
    
    def create(self, request, *args, **kwargs):
        """Process scanned barcode for fulfillment."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        barcode = serializer.validated_data['barcode']
        sales_order = serializer.validated_data['sales_order']
        line_item = serializer.validated_data.get('line_item')
        override_part = serializer.validated_data.get('override_part')
        confirm_substitution = serializer.validated_data.get('confirm_substitution', False)
        
        # Try to find stock item from barcode
        try:
            # First try to find by barcode hash
            from InvenTree.helpers import hash_barcode
            barcode_hash = hash_barcode(barcode)
            stock_item = StockItem.objects.filter(barcode_hash=barcode_hash).first()
            
            if not stock_item:
                # Try to parse as JSON barcode
                import json
                try:
                    barcode_data = json.loads(barcode)
                    if 'stockitem' in barcode_data:
                        stock_item = StockItem.objects.get(pk=barcode_data['stockitem'])
                except (json.JSONDecodeError, StockItem.DoesNotExist):
                    pass
            
            if not stock_item:
                return Response({
                    'error': _('No stock item found for barcode'),
                    'barcode': barcode
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': _('Error processing barcode: {}').format(str(e)),
                'barcode': barcode
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if stock item is available
        if not stock_item.in_stock or stock_item.quantity <= 0:
            return Response({
                'error': _('Stock item is not available'),
                'stock_item': stock_item.pk,
                'quantity': stock_item.quantity
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find matching line item if not specified
        if not line_item:
            # Look for line items that match the scanned part
            matching_lines = sales_order.lines.filter(
                part=stock_item.part,
                shipped__lt=models.F('quantity')
            )
            
            if not matching_lines.exists():
                # Check if this is a substitution
                if override_part:
                    if not confirm_substitution:
                        return Response({
                            'error': _('Substitution requires confirmation'),
                            'requires_confirmation': True,
                            'original_part': stock_item.part.pk,
                            'override_part': override_part.pk
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Find line item for override part
                    matching_lines = sales_order.lines.filter(
                        part=override_part,
                        shipped__lt=models.F('quantity')
                    )
                    
                    if not matching_lines.exists():
                        return Response({
                            'error': _('No matching line item found for override part'),
                            'override_part': override_part.pk
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'error': _('Scanned item does not match any line items in this order'),
                        'stock_item': stock_item.pk,
                        'part': stock_item.part.pk,
                        'suggest_override': True
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            line_item = matching_lines.first()
        
        # Check if line item belongs to the sales order
        if line_item.order != sales_order:
            return Response({
                'error': _('Line item does not belong to this sales order')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate quantity to fulfill
        remaining_quantity = line_item.quantity - line_item.shipped
        fulfill_quantity = min(stock_item.quantity, remaining_quantity)
        
        if fulfill_quantity <= 0:
            return Response({
                'error': _('Line item is already fully fulfilled')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Create allocation if needed
                from order.models import SalesOrderAllocation
                
                allocation, created = SalesOrderAllocation.objects.get_or_create(
                    line=line_item,
                    item=stock_item,
                    defaults={'quantity': fulfill_quantity}
                )
                
                if not created:
                    # Update existing allocation
                    allocation.quantity = min(
                        allocation.quantity + fulfill_quantity,
                        remaining_quantity
                    )
                    allocation.save()
                
                # If substitution was made, update the line item
                if override_part and confirm_substitution:
                    line_item.part = override_part
                    line_item.save()
                
                return Response({
                    'success': _('Item scanned and allocated successfully'),
                    'stock_item': stock_item.pk,
                    'line_item': line_item.pk,
                    'allocated_quantity': allocation.quantity,
                    'substitution_made': bool(override_part and confirm_substitution)
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                'error': _('Error processing fulfillment: {}').format(str(e))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FulfillmentMarkUnavailableView(CreateAPI):
    """Mark line items as unavailable."""
    
    serializer_class = FulfillmentMarkUnavailableSerializer
    permission_classes = [RolePermission]
    
    role_required = 'sales_order.change'
    
    def create(self, request, *args, **kwargs):
        """Mark a line item as unavailable."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        line_item = serializer.validated_data['line_item']
        notes = serializer.validated_data.get('notes', '')
        
        try:
            # Add a note to the line item about unavailability
            if notes:
                current_notes = line_item.notes or ''
                unavailable_note = f"UNAVAILABLE: {notes}"
                if current_notes:
                    line_item.notes = f"{current_notes}\n{unavailable_note}"
                else:
                    line_item.notes = unavailable_note
                line_item.save()
            
            return Response({
                'success': _('Line item marked as unavailable'),
                'line_item': line_item.pk
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': _('Error marking item as unavailable: {}').format(str(e))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)