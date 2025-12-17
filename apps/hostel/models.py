import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel

class Amenity(BaseModel):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    icon = models.CharField(max_length=50, blank=True, verbose_name=_("Icon"))
    
    class Meta:
        verbose_name = _("Amenity")
        verbose_name_plural = _("Amenities")
    
    def __str__(self):
        return self.name


class Facility(BaseModel):
    name = models.CharField(max_length=100, verbose_name=_("Facility Name"))
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Icon Class/Name"))
    category = models.CharField(
        max_length=50,
        choices=[
            ('furniture', _('Furniture')),
            ('appliances', _('Appliances')),
            ('bathroom', _('Bathroom')),
            ('storage', _('Storage')),
            ('entertainment', _('Entertainment')),
            ('safety', _('Safety')),
        ],
        default='furniture',
        verbose_name=_("Category")
    )
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    
    class Meta:
        verbose_name = _("Facility")
        verbose_name_plural = _("Facilities")
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name




class Hostel(BaseModel):
    """
    School Hostel Management
    """
    HOSTEL_TYPE_CHOICES = (
        ("BOYS", _("Boys Hostel")),
        ("GIRLS", _("Girls Hostel")),
        ("COED", _("Co-educational")),
    )

    name = models.CharField(max_length=200, verbose_name=_("Hostel Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Hostel Code"))
    hostel_type = models.CharField(
        max_length=10,
        choices=HOSTEL_TYPE_CHOICES,
        verbose_name=_("Hostel Type")
    )
    address = models.TextField(verbose_name=_("Address"))
    contact_number = models.CharField(max_length=20, verbose_name=_("Contact Number"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    
    # Capacity
    total_rooms = models.PositiveIntegerField(verbose_name=_("Total Rooms"))
    total_capacity = models.PositiveIntegerField(verbose_name=_("Total Capacity"))
    
    # Warden
    warden = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_hostels",
        limit_choices_to={'role__in': ['teacher', 'staff']},
        verbose_name=_("Hostel Warden")
    )
    
    # Fees
    hostel_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Hostel Fee (per month)")
    )
    security_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Security Deposit")
    )
    
    # Amenities
    amenities = models.ManyToManyField(
        Amenity,
        verbose_name=_("Amenities"),
        help_text=_("Select available amenities"),
        blank=True
    )
    
    # Rules
    rules_regulations = models.TextField(blank=True, verbose_name=_("Rules & Regulations"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "hostel_hostels"
        verbose_name = _("Hostel")
        verbose_name_plural = _("Hostels")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def current_occupancy(self):
        return self.rooms.aggregate(
            total=models.Sum('current_occupancy')
        )['total'] or 0

    @property
    def available_beds(self):
        return self.total_capacity - self.current_occupancy

    @property
    def occupancy_percentage(self):
        if self.total_capacity > 0:
            return (self.current_occupancy / self.total_capacity) * 100
        return 0


class Room(BaseModel):
    """
    Hostel Rooms
    """
    ROOM_TYPE_CHOICES = (
        ("SINGLE", _("Single Occupancy")),
        ("DOUBLE", _("Double Occupancy")),
        ("TRIPLE", _("Triple Occupancy")),
        ("DORMITORY", _("Dormitory")),
    )

    hostel = models.ForeignKey(
        Hostel,
        on_delete=models.CASCADE,
        related_name="rooms",
        verbose_name=_("Hostel")
    )
    room_number = models.CharField(max_length=20, verbose_name=_("Room Number"))
    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPE_CHOICES,
        verbose_name=_("Room Type")
    )
    floor = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name=_("Floor Number")
    )
    
    # Capacity
    total_beds = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name=_("Total Beds")
    )
    current_occupancy = models.PositiveIntegerField(default=0, verbose_name=_("Current Occupancy"))
    
    # Facilities
    facilities = models.ManyToManyField(
        Facility,
        verbose_name=_("Room Facilities"),
        help_text=_("Select facilities available in this room"),
        blank=True,
        related_name="rooms"
    )
    # Status
    is_available = models.BooleanField(default=True, verbose_name=_("Is Available"))
    under_maintenance = models.BooleanField(default=False, verbose_name=_("Under Maintenance"))

    class Meta:
        db_table = "hostel_rooms"
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")
        unique_together = [['hostel', 'room_number']]
        ordering = ["hostel", "floor", "room_number"]

    def __str__(self):
        return f"{self.hostel.name} - Room {self.room_number}"

    @property
    def available_beds(self):
        return self.total_beds - self.current_occupancy

    def clean(self):
        if self.current_occupancy > self.total_beds:
            raise ValidationError(_("Current occupancy cannot exceed total beds"))

    def can_accommodate(self, students_count=1):
        return self.available_beds >= students_count and self.is_available


class HostelAllocation(BaseModel):
    """
    Student hostel allocation
    """
    student = models.OneToOneField(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="hostel_allocation",
        verbose_name=_("Student")
    )
    hostel = models.ForeignKey(
        Hostel,
        on_delete=models.CASCADE,
        related_name="allocations",
        verbose_name=_("Hostel")
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="allocations",
        verbose_name=_("Room")
    )
    bed_number = models.CharField(max_length=10, verbose_name=_("Bed Number"))
    
    # Allocation Dates
    allocation_date = models.DateField(default=timezone.now, verbose_name=_("Allocation Date"))
    expected_vacate_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Expected Vacate Date")
    )
    actual_vacate_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Actual Vacate Date")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    
    # Fees
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Monthly Fee")
    )
    security_deposit_paid = models.BooleanField(default=False, verbose_name=_("Security Deposit Paid"))

    class Meta:
        db_table = "hostel_allocations"
        verbose_name = _("Hostel Allocation")
        verbose_name_plural = _("Hostel Allocations")
        ordering = ["-allocation_date"]

    def __str__(self):
        return f"{self.student} - {self.hostel} - Room {self.room.room_number}"

    @property
    def duration_stayed(self):
        if self.actual_vacate_date:
            end_date = self.actual_vacate_date
        else:
            end_date = timezone.now().date()
        return (end_date - self.allocation_date).days

    def vacate(self, vacate_date=None):
        """Vacate the room"""
        self.actual_vacate_date = vacate_date or timezone.now().date()
        self.is_active = False
        self.save()
        
        # Update room occupancy
        self.room.current_occupancy -= 1
        self.room.save()


class HostelAttendance(BaseModel):
    """
    Hostel night attendance
    """
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="hostel_attendances",
        verbose_name=_("Student")
    )
    date = models.DateField(default=timezone.now, verbose_name=_("Date"))
    status = models.CharField(
        max_length=20,
        choices=(
            ("PRESENT", _("Present")),
            ("ABSENT", _("Absent")),
            ("ON_LEAVE", _("On Leave")),
            ("LATE", _("Late Return")),
        ),
        default="PRESENT",
        verbose_name=_("Status")
    )
    check_in_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Check-in Time")
    )
    check_out_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Check-out Time")
    )
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))
    marked_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="marked_hostel_attendances",
        verbose_name=_("Marked By")
    )

    class Meta:
        db_table = "hostel_attendance"
        verbose_name = _("Hostel Attendance")
        verbose_name_plural = _("Hostel Attendances")
        unique_together = [['student', 'date']]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"


class LeaveApplication(BaseModel):
    """
    Hostel leave applications
    """
    LEAVE_TYPE_CHOICES = (
        ("SHORT", _("Short Leave (Few hours)")),
        ("OVERNIGHT", _("Overnight Leave")),
        ("WEEKEND", _("Weekend Leave")),
        ("EMERGENCY", _("Emergency Leave")),
        ("OTHER", _("Other")),
    )

    STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("APPROVED", _("Approved")),
        ("REJECTED", _("Rejected")),
        ("CANCELLED", _("Cancelled")),
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="hostel_leaves",
        verbose_name=_("Student")
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPE_CHOICES,
        verbose_name=_("Leave Type")
    )
    purpose = models.TextField(verbose_name=_("Purpose of Leave"))
    from_date = models.DateTimeField(verbose_name=_("From Date"))
    to_date = models.DateTimeField(verbose_name=_("To Date"))
    
    # Destination
    destination = models.CharField(max_length=200, verbose_name=_("Destination"))
    contact_number = models.CharField(max_length=20, verbose_name=_("Contact Number at Destination"))
    
    # Guardian Information
    guardian_name = models.CharField(max_length=100, verbose_name=_("Guardian Name"))
    guardian_contact = models.CharField(max_length=20, verbose_name=_("Guardian Contact"))
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name=_("Status")
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_hostel_leaves",
        verbose_name=_("Approved By")
    )
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Approval Date")
    )
    rejection_reason = models.TextField(blank=True, verbose_name=_("Rejection Reason"))

    class Meta:
        db_table = "hostel_leave_applications"
        verbose_name = _("Leave Application")
        verbose_name_plural = _("Leave Applications")
        ordering = ["-from_date"]

    def __str__(self):
        return f"{self.student} - {self.leave_type} - {self.from_date.date()}"

    @property
    def duration_hours(self):
        duration = self.to_date - self.from_date
        return duration.total_seconds() / 3600

    def approve(self, user):
        """Approve leave application"""
        self.status = "APPROVED"
        self.approved_by = user
        self.approval_date = timezone.now()
        self.save()

    def reject(self, user, reason):
        """Reject leave application"""
        self.status = "REJECTED"
        self.approved_by = user
        self.approval_date = timezone.now()
        self.rejection_reason = reason
        self.save()


class MessMenuCategory(BaseModel):
    """Simple categories for hostel mess items"""
    name = models.CharField(max_length=100, verbose_name=_("Category Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    display_order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    
    class Meta:
        verbose_name = _("Mess Category")
        verbose_name_plural = _("Mess Categories")
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name

class MessMenuItem(BaseModel):
    """Items available in hostel mess"""
    FOOD_TYPE_CHOICES = [
        ('veg', _('Vegetarian')),
        ('non_veg', _('Non-Vegetarian')),
        ('egg', _('Contains Egg')),
    ]
    
    name = models.CharField(max_length=200, verbose_name=_("Item Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    category = models.ForeignKey(
        MessMenuCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Category"),
        related_name="items"
    )
    food_type = models.CharField(
        max_length=20,
        choices=FOOD_TYPE_CHOICES,
        default='veg',
        verbose_name=_("Food Type")
    )
    standard_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_("Standard Price"),
        help_text=_("Default price for this item")
    )
    is_available = models.BooleanField(default=True, verbose_name=_("Available"))
    preparation_time = models.PositiveIntegerField(
        default=10,
        verbose_name=_("Prep Time (mins)"),
        help_text=_("Preparation time in minutes")
    )
    display_order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Mess Item")
        verbose_name_plural = _("Mess Items")
        ordering = ['category__display_order', 'display_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_food_type_display()})"

class DailyMessMenu(BaseModel):
    """Daily menu for hostel mess"""
    DAY_CHOICES = [
        ('monday', _('Monday')),
        ('tuesday', _('Tuesday')),
        ('wednesday', _('Wednesday')),
        ('thursday', _('Thursday')),
        ('friday', _('Friday')),
        ('saturday', _('Saturday')),
        ('sunday', _('Sunday')),
    ]
    
    MEAL_CHOICES = [
        ('breakfast', _('Breakfast (7:00-9:00 AM)')),
        ('lunch', _('Lunch (12:30-2:30 PM)')),
        ('snacks', _('Evening Snacks (4:30-6:00 PM)')),
        ('dinner', _('Dinner (8:00-10:00 PM)')),
    ]
    
    day = models.CharField(max_length=20, choices=DAY_CHOICES, verbose_name=_("Day"))
    meal = models.CharField(max_length=20, choices=MEAL_CHOICES, verbose_name=_("Meal"))
    date = models.DateField(verbose_name=_("Date"), help_text=_("Actual date for this menu"))
    items = models.ManyToManyField(
        MessMenuItem,
        through='DailyMenuItem',
        verbose_name=_("Menu Items"),
        help_text=_("Select items for this meal")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    special_note = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Special Note"),
        help_text=_("E.g., 'Special Dinner', 'Festival Meal', etc.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Daily Mess Menu")
        verbose_name_plural = _("Daily Mess Menus")
        unique_together = ['day', 'meal', 'date']
        ordering = ['date', 'meal']
    
    def __str__(self):
        return f"{self.date} - {self.get_day_display()} {self.get_meal_display()}"

class DailyMenuItem(BaseModel):
    """Items available for a specific daily menu"""
    daily_menu = models.ForeignKey(DailyMessMenu, on_delete=models.CASCADE, related_name="menu_items")
    menu_item = models.ForeignKey(MessMenuItem, on_delete=models.CASCADE, verbose_name=_("Menu Item"))
    
    # Daily specific adjustments
    price_today = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        blank=True,
        null=True,
        verbose_name=_("Today's Price"),
        help_text=_("Leave blank to use standard price")
    )
    
    # Quantity management for hostel mess
    estimated_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Estimated Quantity"),
        help_text=_("Estimated servings to prepare (0 means unlimited)")
    )
    actual_quantity_prepared = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Actual Prepared"),
        help_text=_("Actual quantity prepared")
    )
    remaining_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Remaining"),
        help_text=_("Remaining quantity after serving")
    )
    
    # Display and preferences
    display_order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"))
    is_special = models.BooleanField(default=False, verbose_name=_("Special Item"))
    is_limited = models.BooleanField(default=False, verbose_name=_("Limited Quantity"))
    
    class Meta:
        verbose_name = _("Daily Menu Item")
        verbose_name_plural = _("Daily Menu Items")
        unique_together = ['daily_menu', 'menu_item']
        ordering = ['display_order']
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.daily_menu}"
    
    @property
    def final_price(self):
        """Get the price for today"""
        return self.price_today if self.price_today else self.menu_item.standard_price
    
    @property
    def is_available(self):
        """Check if item is still available"""
        if not self.is_limited:
            return True
        return self.remaining_quantity > 0


class HostelMessSubscription(BaseModel):
    """Mess subscription plans for hostel residents"""
    PLAN_CHOICES = [
        ('full_month', _('Full Month (All meals)')),
        ('weekdays', _('Weekdays Only')),
        ('weekends', _('Weekends Only')),
        ('breakfast_only', _('Breakfast Only')),
        ('lunch_dinner', _('Lunch + Dinner')),
        ('custom', _('Custom Plan')),
    ]
    
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        verbose_name=_("Student"),
        related_name="mess_subscriptions"
    )
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, verbose_name=_("Plan Type"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    monthly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_("Monthly Rate")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    
    # Included meals
    includes_breakfast = models.BooleanField(default=True, verbose_name=_("Includes Breakfast"))
    includes_lunch = models.BooleanField(default=True, verbose_name=_("Includes Lunch"))
    includes_snacks = models.BooleanField(default=True, verbose_name=_("Includes Snacks"))
    includes_dinner = models.BooleanField(default=True, verbose_name=_("Includes Dinner"))
    

    class Meta:
        verbose_name = _("Mess Subscription")
        verbose_name_plural = _("Mess Subscriptions")
    
    def __str__(self):
        return f"{self.student} - {self.get_plan_type_display()}"

class MessAttendance(BaseModel):
    """Track student attendance/meals taken"""
    student = models.ForeignKey(
         "students.Student",
        on_delete=models.CASCADE,
        verbose_name=_("Student"),
        related_name="mess_attendances"
    )
    daily_menu = models.ForeignKey(
        DailyMessMenu,
        on_delete=models.CASCADE,
        verbose_name=_("Daily Menu"),
        related_name="attendances"
    )
    attendance_time = models.DateTimeField(auto_now_add=True, verbose_name=_("Attendance Time"))
    meal_taken = models.BooleanField(default=True, verbose_name=_("Meal Taken"))
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Amount Paid")
    )
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('subscription', _('Subscription')),
            ('cash', _('Cash')),
            ('upi', _('UPI')),
            ('card', _('Card')),
        ],
        default='subscription',
        verbose_name=_("Payment Method")
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    
    class Meta:
        verbose_name = _("Mess Attendance")
        verbose_name_plural = _("Mess Attendances")
        unique_together = ['student', 'daily_menu']
    
    def __str__(self):
        return f"{self.student} - {self.daily_menu}"

class MessFeedback(BaseModel):
    """Feedback for mess meals"""
    daily_menu = models.ForeignKey(
        DailyMessMenu,
        on_delete=models.CASCADE,
        verbose_name=_("Daily Menu"),
        related_name="feedbacks"
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Student")
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Rating (1-5)")
    )
    comments = models.TextField(blank=True, null=True, verbose_name=_("Comments"))
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Submitted At"))
    
    class Meta:
        verbose_name = _("Mess Feedback")
        verbose_name_plural = _("Mess Feedbacks")
    
    def __str__(self):
        return f"Feedback for {self.daily_menu} - {self.rating}/5"