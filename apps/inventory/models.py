import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel


class Category(BaseModel):
    """
    Inventory categories for classification
    """
    name = models.CharField(max_length=200, verbose_name=_("Category Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Category Code"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_categories",
        verbose_name=_("Parent Category")
    )
    
    # Category Properties
    is_consumable = models.BooleanField(default=False, verbose_name=_("Is Consumable"))
    requires_serial_number = models.BooleanField(
        default=False,
        verbose_name=_("Requires Serial Number")
    )
    requires_maintenance = models.BooleanField(
        default=False,
        verbose_name=_("Requires Maintenance")
    )
    
    # Reordering
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        verbose_name=_("Low Stock Threshold")
    )
    reorder_quantity = models.PositiveIntegerField(
        default=50,
        verbose_name=_("Reorder Quantity")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "inventory_categories"
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]
        indexes = [
            models.Index(fields=['code', 'is_active']),
        ]

    def __str__(self):
        return self.name

    @property
    def items_count(self):
        return self.items.filter(is_active=True).count()

    @property
    def low_stock_items(self):
        return self.items.filter(
            current_stock__lte=models.F('low_stock_threshold'),
            is_active=True
        ).count()


class Supplier(BaseModel):
    """
    Inventory suppliers and vendors
    """
    SUPPLIER_TYPE_CHOICES = (
        ("LOCAL", _("Local Supplier")),
        ("NATIONAL", _("National Supplier")),
        ("INTERNATIONAL", _("International Supplier")),
        ("WHOLESALER", _("Wholesaler")),
        ("MANUFACTURER", _("Manufacturer")),
        ("DISTRIBUTOR", _("Distributor")),
    )

    name = models.CharField(max_length=200, verbose_name=_("Supplier Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Supplier Code"))
    supplier_type = models.CharField(
        max_length=20,
        choices=SUPPLIER_TYPE_CHOICES,
        default="LOCAL",
        verbose_name=_("Supplier Type")
    )
    
    # Contact Information
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Contact Person")
    )
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Phone"))
    mobile = models.CharField(max_length=20, blank=True, verbose_name=_("Mobile"))
    
    # Address
    address = models.TextField(blank=True, verbose_name=_("Address"))
    city = models.CharField(max_length=100, blank=True, verbose_name=_("City"))
    state = models.CharField(max_length=100, blank=True, verbose_name=_("State"))
    pincode = models.CharField(max_length=10, blank=True, verbose_name=_("Pincode"))
    country = models.CharField(max_length=100, default="India", verbose_name=_("Country"))
    
    # Business Information
    gst_number = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_("GST Number")
    )
    pan_number = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("PAN Number")
    )
    website = models.URLField(blank=True, verbose_name=_("Website"))
    
    # Bank Details
    bank_name = models.CharField(max_length=100, blank=True, verbose_name=_("Bank Name"))
    account_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Account Number")
    )
    ifsc_code = models.CharField(max_length=11, blank=True, verbose_name=_("IFSC Code"))
    
    # Rating and Status
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name=_("Supplier Rating")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "inventory_suppliers"
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ["name"]
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['supplier_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def total_orders(self):
        return self.purchase_orders.count()

    @property
    def total_purchases(self):
        return self.purchase_orders.filter(status="COMPLETED").aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0

    def update_rating(self):
        """Update supplier rating based on performance"""
        completed_orders = self.purchase_orders.filter(status="COMPLETED")
        if completed_orders.exists():
            total_rating = sum(order.supplier_rating or 0 for order in completed_orders)
            self.rating = total_rating / completed_orders.count()
            self.save()


class Item(BaseModel):
    """
    Inventory items and products
    """
    UNIT_CHOICES = (
        ("PIECE", _("Piece")),
        ("SET", _("Set")),
        ("DOZEN", _("Dozen")),
        ("PACK", _("Pack")),
        ("BOX", _("Box")),
        ("BOTTLE", _("Bottle")),
        ("METER", _("Meter")),
        ("KG", _("Kilogram")),
        ("LITER", _("Liter")),
        ("ROLL", _("Roll")),
        ("OTHER", _("Other")),
    )

    name = models.CharField(max_length=200, verbose_name=_("Item Name"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Item Code"))
    barcode = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        verbose_name=_("Barcode")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Category and Classification
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Category")
    )
    brand = models.CharField(max_length=100, blank=True, verbose_name=_("Brand"))
    model = models.CharField(max_length=100, blank=True, verbose_name=_("Model"))
    size = models.CharField(max_length=50, blank=True, verbose_name=_("Size"))
    color = models.CharField(max_length=50, blank=True, verbose_name=_("Color"))
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default="PIECE",
        verbose_name=_("Unit")
    )
    
    # Stock Information
    current_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Current Stock")
    )
    minimum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Minimum Stock Level")
    )
    maximum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Maximum Stock Level")
    )
    low_stock_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10.00,
        verbose_name=_("Low Stock Threshold")
    )
    reorder_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=50.00,
        verbose_name=_("Reorder Quantity")
    )
    
    # Pricing
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Cost Price")
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Selling Price")
    )
    average_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Average Price")
    )
    
    # Location
    storage_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Storage Location")
    )
    shelf_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Shelf Number")
    )
    
    # Item Properties
    is_consumable = models.BooleanField(default=False, verbose_name=_("Is Consumable"))
    is_serialized = models.BooleanField(default=False, verbose_name=_("Is Serialized"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    is_discountable = models.BooleanField(default=True, verbose_name=_("Is Discountable"))
    
    # Tax Information
    hsn_code = models.CharField(max_length=10, blank=True, verbose_name=_("HSN Code"))
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Tax Rate (%)")
    )
    
    # Additional Information
    specifications = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Specifications")
    )
    image = models.ImageField(
        upload_to='inventory/items/',
        null=True,
        blank=True,
        verbose_name=_("Item Image")
    )

    class Meta:
        db_table = "inventory_items"
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
        ordering = ["category", "name"]
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['current_stock']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def total_value(self):
        return self.current_stock * self.average_price

    @property
    def is_low_stock(self):
        return self.current_stock <= self.low_stock_threshold

    @property
    def needs_reorder(self):
        return self.current_stock <= self.minimum_stock

    @property
    def stock_status(self):
        if self.current_stock <= self.minimum_stock:
            return "CRITICAL"
        elif self.current_stock <= self.low_stock_threshold:
            return "LOW"
        else:
            return "NORMAL"

    def update_average_price(self):
        """Update average price based on recent purchases"""
        recent_purchases = self.stock_movements.filter(
            movement_type="PURCHASE",
            quantity__gt=0
        ).order_by('-created_at')[:10]  # Last 10 purchases
        
        if recent_purchases.exists():
            total_value = sum(movement.total_value for movement in recent_purchases)
            total_quantity = sum(movement.quantity for movement in recent_purchases)
            if total_quantity > 0:
                self.average_price = total_value / total_quantity
                self.save()

    def add_stock(self, quantity, unit_price, reference, movement_type="PURCHASE", notes=""):
        """Add stock to inventory"""
        if quantity <= 0:
            raise ValidationError(_("Quantity must be greater than 0"))
        
        # Create stock movement
        movement = StockMovement.objects.create(
            item=self,
            movement_type=movement_type,
            quantity=quantity,
            unit_price=unit_price,
            reference=reference,
            notes=notes
        )
        
        # Update current stock
        self.current_stock += quantity
        self.save()
        
        # Update average price if it's a purchase
        if movement_type == "PURCHASE":
            self.update_average_price()
        
        return movement

    def remove_stock(self, quantity, reference, movement_type="ISSUE", notes=""):
        """Remove stock from inventory"""
        if quantity <= 0:
            raise ValidationError(_("Quantity must be greater than 0"))
        
        if quantity > self.current_stock:
            raise ValidationError(_("Insufficient stock"))
        
        # Use average price for issues/returns
        unit_price = self.average_price
        
        # Create stock movement
        movement = StockMovement.objects.create(
            item=self,
            movement_type=movement_type,
            quantity=-quantity,  # Negative for removal
            unit_price=unit_price,
            reference=reference,
            notes=notes
        )
        
        # Update current stock
        self.current_stock -= quantity
        self.save()
        
        return movement


class StockMovement(BaseModel):
    """
    Inventory stock movements and transactions
    """
    MOVEMENT_TYPE_CHOICES = (
        ("PURCHASE", _("Purchase")),
        ("ISSUE", _("Issue")),
        ("RETURN", _("Return")),
        ("ADJUSTMENT", _("Adjustment")),
        ("TRANSFER", _("Transfer")),
        ("DAMAGE", _("Damage")),
        ("LOSS", _("Loss")),
        ("SALE", _("Sale")),
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="stock_movements",
        verbose_name=_("Item")
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES,
        verbose_name=_("Movement Type")
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Quantity")
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Unit Price")
    )
    total_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Value")
    )
    
    # Reference Information
    reference = models.CharField(max_length=100, verbose_name=_("Reference"))
    reference_id = models.UUIDField(null=True, blank=True, verbose_name=_("Reference ID"))
    
    # Location
    from_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("From Location")
    )
    to_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("To Location")
    )
    
    # Details
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    movement_date = models.DateTimeField(default=timezone.now, verbose_name=_("Movement Date"))
    
    # Performed By
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stock_movements",
        verbose_name=_("Performed By")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_movements",
        verbose_name=_("Approved By")
    )

    class Meta:
        db_table = "inventory_stock_movements"
        verbose_name = _("Stock Movement")
        verbose_name_plural = _("Stock Movements")
        ordering = ["-movement_date"]
        indexes = [
            models.Index(fields=['item', 'movement_date']),
            models.Index(fields=['movement_type', 'movement_date']),
            models.Index(fields=['reference']),
        ]

    def __str__(self):
        return f"{self.item} - {self.movement_type} - {self.quantity}"

    def save(self, *args, **kwargs):
        # Calculate total value
        self.total_value = abs(self.quantity) * self.unit_price
        super().save(*args, **kwargs)

    @property
    def is_incoming(self):
        return self.quantity > 0

    @property
    def is_outgoing(self):
        return self.quantity < 0


class PurchaseOrder(BaseModel):
    """
    Purchase orders for inventory items
    """
    PO_STATUS_CHOICES = (
        ("DRAFT", _("Draft")),
        ("PENDING_APPROVAL", _("Pending Approval")),
        ("APPROVED", _("Approved")),
        ("ORDERED", _("Ordered")),
        ("PARTIALLY_RECEIVED", _("Partially Received")),
        ("COMPLETED", _("Completed")),
        ("CANCELLED", _("Cancelled")),
    )

    po_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("PO Number")
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="purchase_orders",
        verbose_name=_("Supplier")
    )
    
    # Order Details
    order_date = models.DateField(default=timezone.now, verbose_name=_("Order Date"))
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Expected Delivery Date")
    )
    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Actual Delivery Date")
    )
    
    # Amounts
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Subtotal")
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Tax Amount")
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Discount Amount")
    )
    shipping_charges = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Shipping Charges")
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Amount")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=PO_STATUS_CHOICES,
        default="DRAFT",
        verbose_name=_("Status")
    )
    
    # Approval
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_purchase_orders",
        verbose_name=_("Requested By")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_purchase_orders",
        verbose_name=_("Approved By")
    )
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Approval Date")
    )
    
    # Terms and Conditions
    payment_terms = models.TextField(blank=True, verbose_name=_("Payment Terms"))
    delivery_terms = models.TextField(blank=True, verbose_name=_("Delivery Terms"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    
    # Supplier Rating
    supplier_rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Supplier Rating")
    )
    supplier_feedback = models.TextField(blank=True, verbose_name=_("Supplier Feedback"))

    class Meta:
        db_table = "inventory_purchase_orders"
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")
        ordering = ["-order_date"]
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['order_date']),
        ]

    def __str__(self):
        return f"{self.po_number} - {self.supplier}"

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = self.generate_po_number()
        
        # Calculate totals
        self.calculate_totals()
        super().save(*args, **kwargs)

    def generate_po_number(self):
        """Generate unique purchase order number"""
        prefix = f"PO-{timezone.now().year}-{self.tenant.schema_name.upper()}-"
        last_po = PurchaseOrder.objects.filter(
            po_number__startswith=prefix,
            tenant=self.tenant
        ).order_by('po_number').last()
        
        if last_po:
            last_num = int(last_po.po_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"{prefix}{new_num:05d}"

    def calculate_totals(self):
        """Calculate order totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.total_price for item in items)
        self.total_amount = (
            self.subtotal + 
            self.tax_amount + 
            self.shipping_charges - 
            self.discount_amount
        )

    def add_item(self, item, quantity, unit_price, tax_rate=0):
        """Add item to purchase order"""
        PurchaseOrderItem.objects.create(
            purchase_order=self,
            item=item,
            quantity=quantity,
            unit_price=unit_price,
            tax_rate=tax_rate
        )
        self.calculate_totals()
        self.save()

    def approve(self, user):
        """Approve purchase order"""
        self.status = "APPROVED"
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save()

    def mark_ordered(self):
        """Mark as ordered"""
        self.status = "ORDERED"
        self.save()

    def receive_items(self, received_items):
        """Receive items from purchase order"""
        for item_data in received_items:
            item = self.items.get(id=item_data['item_id'])
            received_quantity = item_data['received_quantity']
            
            if received_quantity > 0:
                # Update received quantity
                item.received_quantity += received_quantity
                item.save()
                
                # Add stock to inventory
                if received_quantity <= item.pending_quantity:
                    item.item.add_stock(
                        quantity=received_quantity,
                        unit_price=item.unit_price,
                        reference=self.po_number,
                        movement_type="PURCHASE",
                        notes=f"Received from {self.po_number}"
                    )
        
        # Update PO status
        total_ordered = sum(item.quantity for item in self.items.all())
        total_received = sum(item.received_quantity for item in self.items.all())
        
        if total_received == 0:
            self.status = "ORDERED"
        elif total_received < total_ordered:
            self.status = "PARTIALLY_RECEIVED"
        else:
            self.status = "COMPLETED"
            self.actual_delivery_date = timezone.now().date()
        
        self.save()


class PurchaseOrderItem(BaseModel):
    """
    Items in purchase orders
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Purchase Order")
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="purchase_order_items",
        verbose_name=_("Item")
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Ordered Quantity")
    )
    received_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Received Quantity")
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Unit Price")
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Tax Rate (%)")
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Tax Amount")
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Price")
    )

    class Meta:
        db_table = "inventory_purchase_order_items"
        verbose_name = _("Purchase Order Item")
        verbose_name_plural = _("Purchase Order Items")
        unique_together = [['purchase_order', 'item']]

    def __str__(self):
        return f"{self.purchase_order} - {self.item}"

    def save(self, *args, **kwargs):
        # Calculate prices
        self.tax_amount = (self.quantity * self.unit_price * self.tax_rate) / 100
        self.total_price = (self.quantity * self.unit_price) + self.tax_amount
        super().save(*args, **kwargs)

    @property
    def pending_quantity(self):
        return self.quantity - self.received_quantity

    @property
    def is_fully_received(self):
        return self.received_quantity >= self.quantity


class IssueRequest(BaseModel):
    """
    Inventory issue requests for departments/staff
    """
    ISSUE_STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("APPROVED", _("Approved")),
        ("ISSUED", _("Issued")),
        ("REJECTED", _("Rejected")),
        ("PARTIALLY_ISSUED", _("Partially Issued")),
    )

    issue_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Issue Number")
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issue_requests",
        verbose_name=_("Requested By")
    )
    department = models.ForeignKey(
        "hr.Department",
        on_delete=models.CASCADE,
        related_name="issue_requests",
        verbose_name=_("Department")
    )
    
    # Issue Details
    purpose = models.TextField(verbose_name=_("Purpose"))
    required_date = models.DateField(verbose_name=_("Required Date"))
    issue_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Issue Date")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=ISSUE_STATUS_CHOICES,
        default="PENDING",
        verbose_name=_("Status")
    )
    
    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_issue_requests",
        verbose_name=_("Approved By")
    )
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Approval Date")
    )
    rejection_reason = models.TextField(blank=True, verbose_name=_("Rejection Reason"))
    
    # Issued By
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_requests",
        verbose_name=_("Issued By")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "inventory_issue_requests"
        verbose_name = _("Issue Request")
        verbose_name_plural = _("Issue Requests")
        ordering = ["-required_date"]
        indexes = [
            models.Index(fields=['issue_number']),
            models.Index(fields=['department', 'status']),
            models.Index(fields=['requested_by', 'status']),
        ]

    def __str__(self):
        return f"{self.issue_number} - {self.department}"

    def save(self, *args, **kwargs):
        if not self.issue_number:
            self.issue_number = self.generate_issue_number()
        super().save(*args, **kwargs)

    def generate_issue_number(self):
        """Generate unique issue number"""
        prefix = f"ISS-{timezone.now().year}-{self.tenant.schema_name.upper()}-"
        last_issue = IssueRequest.objects.filter(
            issue_number__startswith=prefix,
            tenant=self.tenant
        ).order_by('issue_number').last()
        
        if last_issue:
            last_num = int(last_issue.issue_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"{prefix}{new_num:05d}"

    def approve(self, user):
        """Approve issue request"""
        self.status = "APPROVED"
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save()

    def reject(self, user, reason):
        """Reject issue request"""
        self.status = "REJECTED"
        self.approved_by = user
        self.approval_date = timezone.now()
        self.rejection_reason = reason
        self.save()

    def issue_items(self, issued_items, issued_by):
        """Issue items from the request"""
        for item_data in issued_items:
            issue_item = self.items.get(id=item_data['item_id'])
            issued_quantity = item_data['issued_quantity']
            
            if issued_quantity > 0 and issued_quantity <= issue_item.pending_quantity:
                # Update issued quantity
                issue_item.issued_quantity += issued_quantity
                issue_item.save()
                
                # Remove stock from inventory
                if issued_quantity <= issue_item.item.current_stock:
                    issue_item.item.remove_stock(
                        quantity=issued_quantity,
                        reference=self.issue_number,
                        movement_type="ISSUE",
                        notes=f"Issued to {self.department.name}"
                    )
        
        # Update issue status
        total_requested = sum(item.quantity for item in self.items.all())
        total_issued = sum(item.issued_quantity for item in self.items.all())
        
        if total_issued == 0:
            self.status = "APPROVED"
        elif total_issued < total_requested:
            self.status = "PARTIALLY_ISSUED"
        else:
            self.status = "ISSUED"
            self.issue_date = timezone.now().date()
            self.issued_by = issued_by
        
        self.save()


class IssueItem(BaseModel):
    """
    Items in issue requests
    """
    issue_request = models.ForeignKey(
        IssueRequest,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Issue Request")
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="issue_items",
        verbose_name=_("Item")
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Requested Quantity")
    )
    issued_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Issued Quantity")
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Unit Price")
    )
    total_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Value")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "inventory_issue_items"
        verbose_name = _("Issue Item")
        verbose_name_plural = _("Issue Items")
        unique_together = [['issue_request', 'item']]

    def __str__(self):
        return f"{self.issue_request} - {self.item}"

    def save(self, *args, **kwargs):
        # Use item's average price if not specified
        if not self.unit_price and self.item:
            self.unit_price = self.item.average_price
        
        self.total_value = self.issued_quantity * self.unit_price
        super().save(*args, **kwargs)

    @property
    def pending_quantity(self):
        return self.quantity - self.issued_quantity

    @property
    def is_fully_issued(self):
        return self.issued_quantity >= self.quantity


class Asset(BaseModel):
    """
    Fixed assets and equipment tracking
    """
    ASSET_TYPE_CHOICES = (
        ("FURNITURE", _("Furniture")),
        ("COMPUTER", _("Computer Equipment")),
        ("LAB_EQUIPMENT", _("Laboratory Equipment")),
        ("SPORTS_EQUIPMENT", _("Sports Equipment")),
        ("MUSICAL_INSTRUMENT", _("Musical Instrument")),
        ("LIBRARY_BOOK", _("Library Book")),
        ("VEHICLE", _("Vehicle")),
        ("OFFICE_EQUIPMENT", _("Office Equipment")),
        ("OTHER", _("Other")),
    )

    ASSET_STATUS_CHOICES = (
        ("ACTIVE", _("Active")),
        ("INACTIVE", _("Inactive")),
        ("UNDER_MAINTENANCE", _("Under Maintenance")),
        ("DAMAGED", _("Damaged")),
        ("LOST", _("Lost")),
        ("SOLD", _("Sold")),
        ("DISCARDED", _("Discarded")),
    )

    asset_tag = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Asset Tag")
    )
    name = models.CharField(max_length=200, verbose_name=_("Asset Name"))
    asset_type = models.CharField(
        max_length=30,
        choices=ASSET_TYPE_CHOICES,
        verbose_name=_("Asset Type")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="assets",
        verbose_name=_("Category")
    )
    
    # Asset Details
    description = models.TextField(blank=True, verbose_name=_("Description"))
    brand = models.CharField(max_length=100, blank=True, verbose_name=_("Brand"))
    model = models.CharField(max_length=100, blank=True, verbose_name=_("Model"))
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        verbose_name=_("Serial Number")
    )
    specifications = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Specifications")
    )
    
    # Purchase Information
    purchase_date = models.DateField(verbose_name=_("Purchase Date"))
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Purchase Price")
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
        verbose_name=_("Supplier")
    )
    warranty_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Warranty Expiry")
    )
    
    # Current Information
    current_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Current Value")
    )
    depreciation_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Depreciation Rate (%)")
    )
    useful_life_years = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Useful Life (Years)")
    )
    
    # Location and Assignment
    location = models.CharField(max_length=200, verbose_name=_("Location"))
    room_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Room Number")
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_assets",
        verbose_name=_("Assigned To")
    )
    assigned_department = models.ForeignKey(
        "hr.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
        verbose_name=_("Assigned Department")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=ASSET_STATUS_CHOICES,
        default="ACTIVE",
        verbose_name=_("Status")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    
    # Additional Information
    image = models.ImageField(
        upload_to='inventory/assets/',
        null=True,
        blank=True,
        verbose_name=_("Asset Image")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "inventory_assets"
        verbose_name = _("Asset")
        verbose_name_plural = _("Assets")
        ordering = ["asset_tag"]
        indexes = [
            models.Index(fields=['asset_tag']),
            models.Index(fields=['asset_type', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"{self.asset_tag} - {self.name}"

    @property
    def age_years(self):
        today = timezone.now().date()
        return today.year - self.purchase_date.year - (
            (today.month, today.day) < (self.purchase_date.month, self.purchase_date.day)
        )

    @property
    def is_under_warranty(self):
        if self.warranty_expiry:
            return timezone.now().date() <= self.warranty_expiry
        return False

    @property
    def accumulated_depreciation(self):
        years = min(self.age_years, self.useful_life_years)
        return (self.purchase_price * self.depreciation_rate * years) / 100

    @property
    def net_book_value(self):
        return self.purchase_price - self.accumulated_depreciation

    def calculate_depreciation(self):
        """Calculate current depreciation"""
        self.current_value = self.net_book_value
        self.save()


class MaintenanceRecord(BaseModel):
    """
    Asset maintenance records
    """
    MAINTENANCE_TYPE_CHOICES = (
        ("PREVENTIVE", _("Preventive Maintenance")),
        ("CORRECTIVE", _("Corrective Maintenance")),
        ("BREAKDOWN", _("Breakdown Repair")),
        ("CALIBRATION", _("Calibration")),
        ("INSPECTION", _("Inspection")),
    )

    MAINTENANCE_STATUS_CHOICES = (
        ("SCHEDULED", _("Scheduled")),
        ("IN_PROGRESS", _("In Progress")),
        ("COMPLETED", _("Completed")),
        ("CANCELLED", _("Cancelled")),
        ("OVERDUE", _("Overdue")),
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="maintenance_records",
        verbose_name=_("Asset")
    )
    maintenance_type = models.CharField(
        max_length=20,
        choices=MAINTENANCE_TYPE_CHOICES,
        verbose_name=_("Maintenance Type")
    )
    title = models.CharField(max_length=200, verbose_name=_("Maintenance Title"))
    description = models.TextField(verbose_name=_("Description"))
    
    # Schedule
    scheduled_date = models.DateField(verbose_name=_("Scheduled Date"))
    completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Completed Date")
    )
    next_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Next Maintenance Date")
    )
    
    # Costs
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Estimated Cost")
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Actual Cost")
    )
    
    # Service Provider
    service_provider = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Service Provider")
    )
    technician_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Technician Name")
    )
    contact_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Contact Number")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=MAINTENANCE_STATUS_CHOICES,
        default="SCHEDULED",
        verbose_name=_("Status")
    )
    
    # Results
    work_performed = models.TextField(blank=True, verbose_name=_("Work Performed"))
    parts_replaced = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Parts Replaced")
    )
    recommendations = models.TextField(blank=True, verbose_name=_("Recommendations"))
    
    # Approval
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_maintenance",
        verbose_name=_("Requested By")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_maintenance",
        verbose_name=_("Approved By")
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_maintenance",
        verbose_name=_("Completed By")
    )

    class Meta:
        db_table = "inventory_maintenance_records"
        verbose_name = _("Maintenance Record")
        verbose_name_plural = _("Maintenance Records")
        ordering = ["-scheduled_date"]
        indexes = [
            models.Index(fields=['asset', 'status']),
            models.Index(fields=['scheduled_date', 'status']),
        ]

    def __str__(self):
        return f"{self.asset} - {self.title} - {self.scheduled_date}"

    @property
    def is_overdue(self):
        return (self.status in ["SCHEDULED", "IN_PROGRESS"] and 
                self.scheduled_date < timezone.now().date())

    def complete(self, actual_cost, work_performed, completed_by, parts_replaced=None):
        """Complete maintenance"""
        self.status = "COMPLETED"
        self.actual_cost = actual_cost
        self.work_performed = work_performed
        self.completed_by = completed_by
        self.completed_date = timezone.now().date()
        
        if parts_replaced:
            self.parts_replaced = parts_replaced
        
        self.save()


class InventoryReport(BaseModel):
    """
    Inventory reports and analytics
    """
    REPORT_TYPE_CHOICES = (
        ("STOCK_SUMMARY", _("Stock Summary")),
        ("LOW_STOCK", _("Low Stock Alert")),
        ("STOCK_VALUATION", _("Stock Valuation")),
        ("MOVEMENT_SUMMARY", _("Movement Summary")),
        ("ASSET_REGISTER", _("Asset Register")),
        ("MAINTENANCE_SCHEDULE", _("Maintenance Schedule")),
        ("PURCHASE_ANALYSIS", _("Purchase Analysis")),
        ("ISSUE_ANALYSIS", _("Issue Analysis")),
    )

    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        verbose_name=_("Report Type")
    )
    report_name = models.CharField(max_length=200, verbose_name=_("Report Name"))
    period_start = models.DateField(verbose_name=_("Period Start"))
    period_end = models.DateField(verbose_name=_("Period End"))
    
    # Report Data
    report_data = models.JSONField(
        default=dict,
        verbose_name=_("Report Data")
    )
    summary = models.JSONField(
        default=dict,
        verbose_name=_("Report Summary")
    )
    
    # Generation
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inventory_reports",
        verbose_name=_("Generated By")
    )
    generated_at = models.DateTimeField(default=timezone.now, verbose_name=_("Generated At"))
    
    # Export
    export_file = models.FileField(
        upload_to='inventory_reports/',
        null=True,
        blank=True,
        verbose_name=_("Export File")
    )

    class Meta:
        db_table = "inventory_reports"
        verbose_name = _("Inventory Report")
        verbose_name_plural = _("Inventory Reports")
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.report_name} - {self.period_start} to {self.period_end}"