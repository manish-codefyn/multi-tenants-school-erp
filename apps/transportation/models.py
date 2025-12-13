import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel, TenantAwareModel


class Vehicle(BaseModel, TenantAwareModel):
    """
    School Vehicles
    """
    VEHICLE_TYPE_CHOICES = (
        ("BUS", _("Bus")),
        ("VAN", _("Van")),
        ("CAR", _("Car")),
        ("MINI_BUS", _("Mini Bus")),
        ("OTHER", _("Other")),
    )

    FUEL_TYPE_CHOICES = (
        ("PETROL", _("Petrol")),
        ("DIESEL", _("Diesel")),
        ("CNG", _("CNG")),
        ("ELECTRIC", _("Electric")),
        ("HYBRID", _("Hybrid")),
    )

    vehicle_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Vehicle Number")
    )
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        default="BUS",
        verbose_name=_("Vehicle Type")
    )
    make = models.CharField(max_length=50, verbose_name=_("Make"))
    model = models.CharField(max_length=50, verbose_name=_("Model"))
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2030)],
        verbose_name=_("Manufacturing Year")
    )
    color = models.CharField(max_length=30, verbose_name=_("Color"))
    fuel_type = models.CharField(
        max_length=20,
        choices=FUEL_TYPE_CHOICES,
        verbose_name=_("Fuel Type")
    )
    
    # Capacity
    seating_capacity = models.PositiveIntegerField(verbose_name=_("Seating Capacity"))
    
    # Registration
    registration_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Registration Number")
    )
    registration_date = models.DateField(verbose_name=_("Registration Date"))
    registration_expiry = models.DateField(verbose_name=_("Registration Expiry"))
    
    # Insurance
    insurance_company = models.CharField(max_length=100, verbose_name=_("Insurance Company"))
    insurance_number = models.CharField(max_length=100, verbose_name=_("Insurance Number"))
    insurance_expiry = models.DateField(verbose_name=_("Insurance Expiry"))
    
    # Fitness
    fitness_certificate_number = models.CharField(
        max_length=100,
        verbose_name=_("Fitness Certificate Number")
    )
    fitness_expiry = models.DateField(verbose_name=_("Fitness Expiry"))
    
    # Driver
    driver = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_vehicle",
        limit_choices_to={'role': 'driver'},
        verbose_name=_("Driver")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    under_maintenance = models.BooleanField(default=False, verbose_name=_("Under Maintenance"))

    class Meta:
        db_table = "transportation_vehicles"
        verbose_name = _("Vehicle")
        verbose_name_plural = _("Vehicles")
        ordering = ["vehicle_number"]

    def __str__(self):
        return f"{self.vehicle_number} - {self.make} {self.model}"

    @property
    def is_registration_valid(self):
        return self.registration_expiry >= timezone.now().date()

    @property
    def is_insurance_valid(self):
        return self.insurance_expiry >= timezone.now().date()

    @property
    def is_fitness_valid(self):
        return self.fitness_expiry >= timezone.now().date()

    @property
    def is_roadworthy(self):
        return all([
            self.is_registration_valid,
            self.is_insurance_valid,
            self.is_fitness_valid,
            not self.under_maintenance
        ])


class Route(BaseModel, TenantAwareModel):
    """
    Transportation Routes
    """
    name = models.CharField(max_length=200, verbose_name=_("Route Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Route Code"))
    start_point = models.CharField(max_length=200, verbose_name=_("Start Point"))
    end_point = models.CharField(max_length=200, verbose_name=_("End Point"))
    total_distance = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=_("Total Distance (km)")
    )
    estimated_duration = models.PositiveIntegerField(
        verbose_name=_("Estimated Duration (minutes)")
    )
    
    # Stops
    stops = models.JSONField(
        default=list,
        verbose_name=_("Route Stops"),
        help_text=_("List of stops with sequence and timing")
    )
    
    # Vehicle
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="routes",
        verbose_name=_("Assigned Vehicle")
    )
    
    # Driver
    driver = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_routes",
        limit_choices_to={'role': 'driver'},
        verbose_name=_("Driver")
    )
    
    # Attendant
    attendant = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendant_routes",
        limit_choices_to={'role': 'attendant'},
        verbose_name=_("Attendant")
    )
    
    # Fees
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Monthly Transport Fee")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "transportation_routes"
        verbose_name = _("Route")
        verbose_name_plural = _("Routes")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.start_point} to {self.end_point})"

    @property
    def student_count(self):
        return self.students.filter(is_active=True).count()

    @property
    def available_seats(self):
        if self.vehicle:
            return self.vehicle.seating_capacity - self.student_count
        return 0

    @property
    def can_accommodate_more(self):
        return self.available_seats > 0


class RouteStop(BaseModel, TenantAwareModel):
    """
    Detailed route stops with timing
    """
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="route_stops",
        verbose_name=_("Route")
    )
    stop_name = models.CharField(max_length=200, verbose_name=_("Stop Name"))
    sequence = models.PositiveIntegerField(verbose_name=_("Sequence Number"))
    pickup_time = models.TimeField(verbose_name=_("Pickup Time"))
    drop_time = models.TimeField(verbose_name=_("Drop Time"))
    landmark = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Landmark")
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_("Latitude")
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_("Longitude")
    )

    class Meta:
        db_table = "transportation_route_stops"
        verbose_name = _("Route Stop")
        verbose_name_plural = _("Route Stops")
        unique_together = [['route', 'sequence']]
        ordering = ["route", "sequence"]

    def __str__(self):
        return f"{self.route.name} - {self.stop_name}"

    def clean(self):
        if self.drop_time <= self.pickup_time:
            raise ValidationError(_("Drop time must be after pickup time"))


class TransportAllocation(BaseModel, TenantAwareModel):
    """
    Student transport allocation
    """
    student = models.OneToOneField(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="transport_allocation",
        verbose_name=_("Student")
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="students",
        verbose_name=_("Route")
    )
    pickup_stop = models.ForeignKey(
        RouteStop,
        on_delete=models.CASCADE,
        related_name="pickup_students",
        verbose_name=_("Pickup Stop")
    )
    drop_stop = models.ForeignKey(
        RouteStop,
        on_delete=models.CASCADE,
        related_name="drop_students",
        verbose_name=_("Drop Stop")
    )
    
    # Allocation Dates
    allocation_date = models.DateField(default=timezone.now, verbose_name=_("Allocation Date"))
    valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Valid Until")
    )
    
    # Fees
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Monthly Fee")
    )
    is_fee_paid = models.BooleanField(default=False, verbose_name=_("Is Fee Paid"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "transportation_allocations"
        verbose_name = _("Transport Allocation")
        verbose_name_plural = _("Transport Allocations")
        ordering = ["route", "student"]

    def __str__(self):
        return f"{self.student} - {self.route}"

    @property
    def pickup_time(self):
        return self.pickup_stop.pickup_time

    @property
    def drop_time(self):
        return self.drop_stop.drop_time


class TransportAttendance(BaseModel, TenantAwareModel):
    """
    Transport attendance tracking
    """
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="transport_attendances",
        verbose_name=_("Student")
    )
    date = models.DateField(default=timezone.now, verbose_name=_("Date"))
    trip_type = models.CharField(
        max_length=10,
        choices=(
            ("PICKUP", _("Pickup")),
            ("DROP", _("Drop")),
        ),
        verbose_name=_("Trip Type")
    )
    status = models.CharField(
        max_length=20,
        choices=(
            ("PRESENT", _("Present")),
            ("ABSENT", _("Absent")),
            ("LATE", _("Late")),
            ("ON_LEAVE", _("On Leave")),
        ),
        default="PRESENT",
        verbose_name=_("Status")
    )
    actual_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Actual Time")
    )
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))
    marked_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="marked_transport_attendances",
        verbose_name=_("Marked By")
    )

    class Meta:
        db_table = "transportation_attendance"
        verbose_name = _("Transport Attendance")
        verbose_name_plural = _("Transport Attendances")
        unique_together = [['student', 'date', 'trip_type']]
        ordering = ["-date", "trip_type"]

    def __str__(self):
        return f"{self.student} - {self.date} - {self.trip_type} - {self.status}"


class MaintenanceRecord(BaseModel, TenantAwareModel):
    """
    Vehicle maintenance records
    """
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="maintenance_records",
        verbose_name=_("Vehicle")
    )
    maintenance_type = models.CharField(
        max_length=50,
        choices=(
            ("ROUTINE", _("Routine Maintenance")),
            ("BREAKDOWN", _("Breakdown Repair")),
            ("ACCIDENT", _("Accident Repair")),
            ("INSPECTION", _("Inspection")),
            ("OTHER", _("Other")),
        ),
        verbose_name=_("Maintenance Type")
    )
    description = models.TextField(verbose_name=_("Description"))
    maintenance_date = models.DateField(default=timezone.now, verbose_name=_("Maintenance Date"))
    next_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Next Maintenance Date")
    )
    
    # Workshop
    workshop_name = models.CharField(max_length=200, verbose_name=_("Workshop Name"))
    workshop_contact = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Workshop Contact")
    )
    
    # Costs
    labor_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Labor Cost")
    )
    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Parts Cost")
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Cost")
    )
    
    # Odometer
    odometer_reading = models.PositiveIntegerField(verbose_name=_("Odometer Reading"))
    
    # Status
    is_completed = models.BooleanField(default=True, verbose_name=_("Is Completed"))

    class Meta:
        db_table = "transportation_maintenance"
        verbose_name = _("Maintenance Record")
        verbose_name_plural = _("Maintenance Records")
        ordering = ["-maintenance_date"]

    def __str__(self):
        return f"{self.vehicle} - {self.maintenance_type} - {self.maintenance_date}"

    def save(self, *args, **kwargs):
        self.total_cost = self.labor_cost + self.parts_cost
        super().save(*args, **kwargs)


class FuelRecord(BaseModel, TenantAwareModel):
    """
    Vehicle fuel consumption records
    """
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="fuel_records",
        verbose_name=_("Vehicle")
    )
    date = models.DateField(default=timezone.now, verbose_name=_("Date"))
    fuel_type = models.CharField(max_length=20, verbose_name=_("Fuel Type"))
    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Quantity (Liters)")
    )
    rate_per_liter = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Rate per Liter")
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total Cost")
    )
    odometer_reading = models.PositiveIntegerField(verbose_name=_("Odometer Reading"))
    station_name = models.CharField(max_length=200, verbose_name=_("Fuel Station"))
    receipt_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Receipt Number")
    )

    class Meta:
        db_table = "transportation_fuel_records"
        verbose_name = _("Fuel Record")
        verbose_name_plural = _("Fuel Records")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.vehicle} - {self.date} - {self.quantity}L"

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.rate_per_liter
        super().save(*args, **kwargs)

    @property
    def mileage(self):
        """Calculate mileage if previous record exists"""
        previous = FuelRecord.objects.filter(
            vehicle=self.vehicle,
            date__lt=self.date
        ).order_by('-date').first()
        
        if previous:
            distance = self.odometer_reading - previous.odometer_reading
            if distance > 0 and self.quantity > 0:
                return distance / self.quantity
        return 0