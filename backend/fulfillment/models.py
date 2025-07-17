"""Models for order fulfillment tracking."""

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from order.models import SalesOrder, SalesOrderLineItem
from part.models import Part
from stock.models import StockItem


class OrderFulfillmentSession(models.Model):
    """Track order fulfillment sessions."""
    
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='fulfillment_sessions',
        verbose_name=_('Sales Order')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('User')
    )
    
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created Date')
    )
    
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Completed Date')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    class Meta:
        """Meta options for OrderFulfillmentSession."""
        
        verbose_name = _('Order Fulfillment Session')
        verbose_name_plural = _('Order Fulfillment Sessions')

    def __str__(self):
        """String representation."""
        return f"Fulfillment {self.sales_order.reference} - {self.user.username}"


class FulfillmentLineItem(models.Model):
    """Track individual line item fulfillment."""
    
    session = models.ForeignKey(
        OrderFulfillmentSession,
        on_delete=models.CASCADE,
        related_name='line_items',
        verbose_name=_('Fulfillment Session')
    )
    
    line_item = models.ForeignKey(
        SalesOrderLineItem,
        on_delete=models.CASCADE,
        verbose_name=_('Sales Order Line Item')
    )
    
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Stock Item')
    )
    
    substituted_part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Substituted Part'),
        help_text=_('Part used as substitute for original')
    )
    
    quantity_fulfilled = models.DecimalField(
        max_digits=15,
        decimal_places=5,
        default=0,
        verbose_name=_('Quantity Fulfilled')
    )
    
    is_substitution = models.BooleanField(
        default=False,
        verbose_name=_('Is Substitution')
    )
    
    is_unavailable = models.BooleanField(
        default=False,
        verbose_name=_('Marked Unavailable')
    )
    
    scanned_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Scanned Date')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    class Meta:
        """Meta options for FulfillmentLineItem."""
        
        verbose_name = _('Fulfillment Line Item')
        verbose_name_plural = _('Fulfillment Line Items')

    def __str__(self):
        """String representation."""
        return f"Fulfillment {self.line_item.part.name} - {self.quantity_fulfilled}"