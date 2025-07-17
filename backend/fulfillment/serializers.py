"""Serializers for fulfillment app."""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from order.models import SalesOrder, SalesOrderLineItem
from part.models import Part
from stock.models import StockItem
from InvenTree.serializers import InvenTreeModelSerializer

from .models import OrderFulfillmentSession, FulfillmentLineItem


class SimpleSalesOrderSerializer(InvenTreeModelSerializer):
    """Simplified serializer for sales orders in fulfillment context."""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    line_items_count = serializers.IntegerField(source='line_items', read_only=True)
    total_items = serializers.SerializerMethodField()
    fulfilled_items = serializers.SerializerMethodField()
    
    class Meta:
        """Meta options."""
        model = SalesOrder
        fields = [
            'pk',
            'reference',
            'customer_name',
            'description',
            'status',
            'status_custom_key',
            'line_items_count',
            'total_items',
            'fulfilled_items',
            'creation_date',
            'target_date'
        ]
    
    def get_total_items(self, obj):
        """Get total quantity of items in order."""
        return sum(line.quantity for line in obj.lines.all())
    
    def get_fulfilled_items(self, obj):
        """Get total quantity of fulfilled items."""
        return sum(line.shipped for line in obj.lines.all())


class FulfillmentLineItemSerializer(InvenTreeModelSerializer):
    """Serializer for fulfillment line items."""
    
    part_detail = serializers.SerializerMethodField()
    stock_item_detail = serializers.SerializerMethodField()
    substituted_part_detail = serializers.SerializerMethodField()
    line_item_detail = serializers.SerializerMethodField()
    
    class Meta:
        """Meta options."""
        model = FulfillmentLineItem
        fields = [
            'pk',
            'line_item',
            'stock_item',
            'substituted_part',
            'quantity_fulfilled',
            'is_substitution',
            'is_unavailable',
            'scanned_date',
            'notes',
            'part_detail',
            'stock_item_detail',
            'substituted_part_detail',
            'line_item_detail'
        ]
    
    def get_part_detail(self, obj):
        """Get part details."""
        part = obj.substituted_part or obj.line_item.part
        return {
            'pk': part.pk,
            'name': part.name,
            'description': part.description,
            'IPN': part.IPN,
            'image': part.image.url if part.image else None
        }
    
    def get_stock_item_detail(self, obj):
        """Get stock item details."""
        if not obj.stock_item:
            return None
        return {
            'pk': obj.stock_item.pk,
            'quantity': obj.stock_item.quantity,
            'serial': obj.stock_item.serial,
            'batch': obj.stock_item.batch
        }
    
    def get_substituted_part_detail(self, obj):
        """Get substituted part details."""
        if not obj.substituted_part:
            return None
        return {
            'pk': obj.substituted_part.pk,
            'name': obj.substituted_part.name,
            'description': obj.substituted_part.description
        }
    
    def get_line_item_detail(self, obj):
        """Get line item details."""
        return {
            'pk': obj.line_item.pk,
            'quantity': obj.line_item.quantity,
            'shipped': obj.line_item.shipped,
            'part_name': obj.line_item.part.name
        }


class OrderFulfillmentSessionSerializer(InvenTreeModelSerializer):
    """Serializer for order fulfillment sessions."""
    
    sales_order_detail = SimpleSalesOrderSerializer(source='sales_order', read_only=True)
    line_items = FulfillmentLineItemSerializer(many=True, read_only=True)
    user_detail = serializers.SerializerMethodField()
    
    class Meta:
        """Meta options."""
        model = OrderFulfillmentSession
        fields = [
            'pk',
            'sales_order',
            'user',
            'created_date',
            'completed_date',
            'is_active',
            'notes',
            'sales_order_detail',
            'line_items',
            'user_detail'
        ]
    
    def get_user_detail(self, obj):
        """Get user details."""
        return {
            'pk': obj.user.pk,
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name
        }


class ScanItemSerializer(serializers.Serializer):
    """Serializer for scanning items during fulfillment."""
    
    barcode = serializers.CharField(
        required=True,
        help_text=_('Scanned barcode data')
    )
    
    session_id = serializers.IntegerField(
        required=True,
        help_text=_('Fulfillment session ID')
    )
    
    line_item_id = serializers.IntegerField(
        required=False,
        help_text=_('Specific line item ID to fulfill')
    )


class SubstituteItemSerializer(serializers.Serializer):
    """Serializer for substituting items during fulfillment."""
    
    session_id = serializers.IntegerField(
        required=True,
        help_text=_('Fulfillment session ID')
    )
    
    line_item_id = serializers.IntegerField(
        required=True,
        help_text=_('Line item ID to substitute')
    )
    
    substitute_part_id = serializers.IntegerField(
        required=True,
        help_text=_('Part ID to use as substitute')
    )
    
    stock_item_id = serializers.IntegerField(
        required=False,
        help_text=_('Stock item ID to use')
    )
    
    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=5,
        required=True,
        help_text=_('Quantity to substitute')
    )
    
    confirmation = serializers.BooleanField(
        required=True,
        help_text=_('Confirmation that substitution is intentional')
    )
    
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Notes about the substitution')
    )


class MarkUnavailableSerializer(serializers.Serializer):
    """Serializer for marking items as unavailable."""
    
    session_id = serializers.IntegerField(
        required=True,
        help_text=_('Fulfillment session ID')
    )
    
    line_item_id = serializers.IntegerField(
        required=True,
        help_text=_('Line item ID to mark unavailable')
    )
    
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Notes about unavailability')
    )