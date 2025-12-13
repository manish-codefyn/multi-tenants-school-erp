import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel


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
    amenities = models.JSONField(
        default=list,
        verbose_name=_("Amenities"),
        help_text=_("List of available amenities")
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
    facilities = models.JSONField(
        default=list,
        verbose_name=_("Room Facilities")
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
        "users.User",
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


class MessMenu(BaseModel):
    """
    Hostel Mess Menu
    """
    MEAL_TYPE_CHOICES = (
        ("BREAKFAST", _("Breakfast")),
        ("LUNCH", _("Lunch")),
        ("SNACKS", _("Snacks")),
        ("DINNER", _("Dinner")),
    )

    DAY_CHOICES = (
        ("MONDAY", _("Monday")),
        ("TUESDAY", _("Tuesday")),
        ("WEDNESDAY", _("Wednesday")),
        ("THURSDAY", _("Thursday")),
        ("FRIDAY", _("Friday")),
        ("SATURDAY", _("Saturday")),
        ("SUNDAY", _("Sunday")),
    )

    hostel = models.ForeignKey(
        Hostel,
        on_delete=models.CASCADE,
        related_name="mess_menus",
        verbose_name=_("Hostel")
    )
    day = models.CharField(max_length=10, choices=DAY_CHOICES, verbose_name=_("Day"))
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPE_CHOICES, verbose_name=_("Meal Type"))
    items = models.JSONField(
        default=list,
        verbose_name=_("Menu Items"),
        help_text=_("List of food items in JSON format")
    )
    special_note = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Special Note")
    )
    effective_from = models.DateField(default=timezone.now, verbose_name=_("Effective From"))
    effective_to = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Effective To")
    )

    class Meta:
        db_table = "hostel_mess_menus"
        verbose_name = _("Mess Menu")
        verbose_name_plural = _("Mess Menus")
        unique_together = [['hostel', 'day', 'meal_type', 'effective_from']]
        ordering = ["day", "meal_type"]

    def __str__(self):
        return f"{self.hostel} - {self.day} - {self.meal_type}"

    @property
    def is_current(self):
        today = timezone.now().date()
        if self.effective_to:
            return self.effective_from <= today <= self.effective_to
        return self.effective_from <= today