import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel


class Library(BaseModel):
    """
    Library information and configuration
    """
    name = models.CharField(max_length=200, verbose_name=_("Library Name"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Library Code"))
    
    # Contact Information
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Phone"))
    
    # Location
    location = models.CharField(max_length=200, verbose_name=_("Location"))
    building = models.CharField(max_length=100, blank=True, verbose_name=_("Building"))
    floor = models.CharField(max_length=50, blank=True, verbose_name=_("Floor"))
    
    # Librarian
    librarian = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_libraries",
        limit_choices_to={'role__in': ['teacher', 'staff']},
        verbose_name=_("Librarian")
    )
    
    # Library Configuration
    max_books_per_student = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Maximum Books Per Student")
    )
    max_books_per_staff = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Maximum Books Per Staff")
    )
    issue_duration_students = models.PositiveIntegerField(
        default=14,
        verbose_name=_("Issue Duration for Students (days)")
    )
    issue_duration_staff = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Issue Duration for Staff (days)")
    )
    fine_per_day = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=5.00,
        verbose_name=_("Fine Per Day (₹)")
    )
    max_fine_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=500.00,
        verbose_name=_("Maximum Fine Amount (₹)")
    )
    
    # Timings
    opening_time = models.TimeField(default="09:00", verbose_name=_("Opening Time"))
    closing_time = models.TimeField(default="17:00", verbose_name=_("Closing Time"))
    working_days = models.JSONField(
        default=list,
        verbose_name=_("Working Days"),
        help_text=_("List of working days (0=Monday, 6=Sunday)")
    )
    
    # Rules and Policies
    rules_regulations = models.TextField(blank=True, verbose_name=_("Rules & Regulations"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "library_libraries"
        verbose_name = _("Library")
        verbose_name_plural = _("Libraries")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def total_books(self):
        return self.books.filter(is_active=True).count()

    @property
    def available_books(self):
        return self.books.filter(
            is_active=True,
            total_copies__gt=models.F('issued_copies')
        ).count()

    @property
    def issued_books(self):
        return self.books.filter(
            is_active=True,
            issued_copies__gt=0
        ).aggregate(total=models.Sum('issued_copies'))['total'] or 0

    def is_open(self):
        """Check if library is currently open"""
        now = timezone.now()
        current_time = now.time()
        current_day = now.weekday()
        
        return (
            self.opening_time <= current_time <= self.closing_time and
            current_day in self.working_days and
            self.is_active
        )


class Author(BaseModel):
    """
    Book authors
    """
    name = models.CharField(max_length=200, verbose_name=_("Author Name"))
    biography = models.TextField(blank=True, verbose_name=_("Biography"))
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date of Birth")
    )
    date_of_death = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date of Death")
    )
    nationality = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Nationality")
    )
    website = models.URLField(blank=True, verbose_name=_("Website"))
    photo = models.ImageField(
        upload_to='library/authors/',
        null=True,
        blank=True,
        verbose_name=_("Photo")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "library_authors"
        verbose_name = _("Author")
        verbose_name_plural = _("Authors")
        ordering = ["name"]
        indexes = [
            models.Index(fields=['name', 'is_active']),
        ]

    def __str__(self):
        return self.name

    @property
    def books_count(self):
        return self.books.count()

    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class Publisher(BaseModel):
    """
    Book publishers
    """
    name = models.CharField(max_length=200, verbose_name=_("Publisher Name"))
    address = models.TextField(blank=True, verbose_name=_("Address"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Phone"))
    website = models.URLField(blank=True, verbose_name=_("Website"))
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Contact Person")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "library_publishers"
        verbose_name = _("Publisher")
        verbose_name_plural = _("Publishers")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def books_count(self):
        return self.books.count()


class BookCategory(BaseModel):
    """
    Book categories and genres
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
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "library_categories"
        verbose_name = _("Book Category")
        verbose_name_plural = _("Book Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def books_count(self):
        return self.books.filter(is_active=True).count()


class Book(BaseModel):
    """
    Book catalog and inventory
    """
    LANGUAGE_CHOICES = (
        ("ENGLISH", _("English")),
        ("HINDI", _("Hindi")),
        ("BENGALI", _("Bengali")),
        ("TAMIL", _("Tamil")),
        ("TELUGU", _("Telugu")),
        ("MARATHI", _("Marathi")),
        ("URDU", _("Urdu")),
        ("GUJARATI", _("Gujarati")),
        ("KANNADA", _("Kannada")),
        ("MALAYALAM", _("Malayalam")),
        ("OTHER", _("Other")),
    )

    BOOK_TYPE_CHOICES = (
        ("TEXTBOOK", _("Textbook")),
        ("REFERENCE", _("Reference Book")),
        ("FICTION", _("Fiction")),
        ("NON_FICTION", _("Non-Fiction")),
        ("MAGAZINE", _("Magazine")),
        ("JOURNAL", _("Journal")),
        ("DICTIONARY", _("Dictionary")),
        ("ENCYCLOPEDIA", _("Encyclopedia")),
        ("COMIC", _("Comic")),
        ("OTHER", _("Other")),
    )

    BINDING_CHOICES = (
        ("HARDCOVER", _("Hardcover")),
        ("PAPERBACK", _("Paperback")),
        ("SPIRAL", _("Spiral Bound")),
        ("EBOOK", _("E-Book")),
        ("AUDIO", _("Audio Book")),
    )

    isbn = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name=_("ISBN")
    )
    title = models.CharField(max_length=500, verbose_name=_("Book Title"))
    subtitle = models.CharField(max_length=500, blank=True, verbose_name=_("Subtitle"))
    
    # Classification
    category = models.ForeignKey(
        BookCategory,
        on_delete=models.CASCADE,
        related_name="books",
        verbose_name=_("Category")
    )
    book_type = models.CharField(
        max_length=20,
        choices=BOOK_TYPE_CHOICES,
        default="TEXTBOOK",
        verbose_name=_("Book Type")
    )
    
    # Authors and Publisher
    authors = models.ManyToManyField(
        Author,
        related_name="books",
        verbose_name=_("Authors")
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name="books",
        verbose_name=_("Publisher")
    )
    
    # Publication Details
    publication_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1000), MaxValueValidator(2100)],
        verbose_name=_("Publication Year")
    )
    edition = models.CharField(max_length=50, blank=True, verbose_name=_("Edition"))
    volume = models.CharField(max_length=50, blank=True, verbose_name=_("Volume"))
    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default="ENGLISH",
        verbose_name=_("Language")
    )
    
    # Physical Details
    binding = models.CharField(
        max_length=20,
        choices=BINDING_CHOICES,
        default="PAPERBACK",
        verbose_name=_("Binding")
    )
    pages = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Number of Pages")
    )
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Dimensions")
    )
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Weight (grams)")
    )
    
    # Content Details
    description = models.TextField(blank=True, verbose_name=_("Description"))
    table_of_contents = models.TextField(blank=True, verbose_name=_("Table of Contents"))
    keywords = models.TextField(
        blank=True,
        verbose_name=_("Keywords"),
        help_text=_("Comma-separated keywords for search")
    )
    
    # Inventory
    total_copies = models.PositiveIntegerField(default=1, verbose_name=_("Total Copies"))
    available_copies = models.PositiveIntegerField(default=1, verbose_name=_("Available Copies"))
    issued_copies = models.PositiveIntegerField(default=0, verbose_name=_("Issued Copies"))
    reserved_copies = models.PositiveIntegerField(default=0, verbose_name=_("Reserved Copies"))
    
    # Location
    shelf_number = models.CharField(max_length=50, verbose_name=_("Shelf Number"))
    rack_number = models.CharField(max_length=50, blank=True, verbose_name=_("Rack Number"))
    
    # Acquisition
    acquisition_date = models.DateField(
        default=timezone.now,
        verbose_name=_("Acquisition Date")
    )
    acquisition_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Acquisition Price")
    )
    source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Acquisition Source")
    )
    
    # Status
    is_reference = models.BooleanField(default=False, verbose_name=_("Is Reference Book"))
    is_damaged = models.BooleanField(default=False, verbose_name=_("Is Damaged"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    
    # Additional Information
    cover_image = models.ImageField(
        upload_to='library/books/covers/',
        null=True,
        blank=True,
        verbose_name=_("Cover Image")
    )
    digital_copy = models.FileField(
        upload_to='library/books/digital/',
        null=True,
        blank=True,
        verbose_name=_("Digital Copy")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "library_books"
        verbose_name = _("Book")
        verbose_name_plural = _("Books")
        ordering = ["title"]
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['title']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['available_copies']),
        ]

    def __str__(self):
        return f"{self.title} - {self.isbn}"

    def clean(self):
        if self.total_copies < (self.issued_copies + self.reserved_copies):
            raise ValidationError(_("Total copies cannot be less than issued + reserved copies"))
        
        self.available_copies = self.total_copies - self.issued_copies - self.reserved_copies

    def save(self, *args, **kwargs):
        # Calculate available copies
        self.available_copies = self.total_copies - self.issued_copies - self.reserved_copies
        super().save(*args, **kwargs)

    @property
    def can_be_issued(self):
        return (
            self.available_copies > 0 and
            not self.is_reference and
            not self.is_damaged and
            self.is_active
        )

    @property
    def authors_display(self):
        return ", ".join(author.name for author in self.authors.all())

    def issue_book(self):
        """Issue one copy of the book"""
        if self.available_copies > 0:
            self.issued_copies += 1
            self.save()

    def return_book(self):
        """Return one copy of the book"""
        if self.issued_copies > 0:
            self.issued_copies -= 1
            self.save()

    def reserve_book(self):
        """Reserve one copy of the book"""
        if self.available_copies > 0:
            self.reserved_copies += 1
            self.save()

    def cancel_reservation(self):
        """Cancel one reservation"""
        if self.reserved_copies > 0:
            self.reserved_copies -= 1
            self.save()


class BookCopy(BaseModel):
    """
    Individual book copies with unique identifiers
    """
    COPY_STATUS_CHOICES = (
        ("AVAILABLE", _("Available")),
        ("ISSUED", _("Issued")),
        ("RESERVED", _("Reserved")),
        ("DAMAGED", _("Damaged")),
        ("LOST", _("Lost")),
        ("UNDER_MAINTENANCE", _("Under Maintenance")),
        ("WITHDRAWN", _("Withdrawn")),
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="copies",
        verbose_name=_("Book")
    )
    copy_number = models.CharField(max_length=50, verbose_name=_("Copy Number"))
    barcode = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name=_("Barcode")
    )
    accession_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Accession Number")
    )
    
    # Copy Details
    purchase_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Purchase Price")
    )
    purchase_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Purchase Date")
    )
    supplier = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Supplier")
    )
    
    # Physical Condition
    condition = models.CharField(
        max_length=20,
        choices=(
            ("EXCELLENT", _("Excellent")),
            ("GOOD", _("Good")),
            ("FAIR", _("Fair")),
            ("POOR", _("Poor")),
            ("DAMAGED", _("Damaged")),
        ),
        default="GOOD",
        verbose_name=_("Condition")
    )
    notes = models.TextField(blank=True, verbose_name=_("Condition Notes"))
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=COPY_STATUS_CHOICES,
        default="AVAILABLE",
        verbose_name=_("Status")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "library_book_copies"
        verbose_name = _("Book Copy")
        verbose_name_plural = _("Book Copies")
        unique_together = [['book', 'copy_number']]
        ordering = ["book", "copy_number"]
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['accession_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.book.title} - Copy {self.copy_number}"

    @property
    def can_be_issued(self):
        return (
            self.status == "AVAILABLE" and
            not self.book.is_reference and
            self.is_active
        )

    def issue(self):
        """Mark copy as issued"""
        if self.status == "AVAILABLE":
            self.status = "ISSUED"
            self.save()

    def return_copy(self):
        """Mark copy as available"""
        if self.status == "ISSUED":
            self.status = "AVAILABLE"
            self.save()

    def mark_damaged(self, notes=""):
        """Mark copy as damaged"""
        self.status = "DAMAGED"
        self.condition = "DAMAGED"
        self.notes = notes
        self.save()

    def mark_lost(self):
        """Mark copy as lost"""
        self.status = "LOST"
        self.save()


class BookIssue(BaseModel):
    """
    Book issue and return transactions
    """
    ISSUE_STATUS_CHOICES = (
        ("ISSUED", _("Issued")),
        ("RETURNED", _("Returned")),
        ("OVERDUE", _("Overdue")),
        ("LOST", _("Lost")),
        ("DAMAGED", _("Damaged")),
    )

    member = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="book_issues",
        verbose_name=_("Member")
    )
    book_copy = models.ForeignKey(
        BookCopy,
        on_delete=models.CASCADE,
        related_name="issues",
        verbose_name=_("Book Copy")
    )
    issue_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Issue Number")
    )
    
    # Issue Details
    issue_date = models.DateField(default=timezone.now, verbose_name=_("Issue Date"))
    due_date = models.DateField(verbose_name=_("Due Date"))
    actual_return_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Actual Return Date")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=ISSUE_STATUS_CHOICES,
        default="ISSUED",
        verbose_name=_("Status")
    )
    
    # Fine Information
    fine_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Fine Amount")
    )
    fine_paid = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Fine Paid")
    )
    fine_waived = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Fine Waived")
    )
    
    # Renewal Information
    renewal_count = models.PositiveIntegerField(default=0, verbose_name=_("Renewal Count"))
    last_renewal_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Last Renewal Date")
    )
    
    # Issued By
    issued_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="issued_books",
        verbose_name=_("Issued By")
    )
    received_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_books",
        verbose_name=_("Received By")
    )
    
    # Notes
    issue_notes = models.TextField(blank=True, verbose_name=_("Issue Notes"))
    return_notes = models.TextField(blank=True, verbose_name=_("Return Notes"))

    class Meta:
        db_table = "library_book_issues"
        verbose_name = _("Book Issue")
        verbose_name_plural = _("Book Issues")
        ordering = ["-issue_date"]
        indexes = [
            models.Index(fields=['issue_number']),
            models.Index(fields=['member', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]

    def __str__(self):
        return f"{self.issue_number} - {self.member} - {self.book_copy}"

    def save(self, *args, **kwargs):
        if not self.issue_number:
            self.issue_number = self.generate_issue_number()
        
        # Set due date based on member type
        if not self.due_date:
            library = Library.objects.filter(tenant=self.tenant, is_active=True).first()
            if library:
                if self.member.role == 'student':
                    days = library.issue_duration_students
                else:
                    days = library.issue_duration_staff
                self.due_date = self.issue_date + timezone.timedelta(days=days)
        
        super().save(*args, **kwargs)

    def generate_issue_number(self):
        """Generate unique issue number"""
        prefix = f"LIB-{timezone.now().year}-{self.tenant.schema_name.upper()}-"
        last_issue = BookIssue.objects.filter(
            issue_number__startswith=prefix,
            tenant=self.tenant
        ).order_by('issue_number').last()
        
        if last_issue:
            last_num = int(last_issue.issue_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"{prefix}{new_num:05d}"

    @property
    def is_overdue(self):
        return self.status == "ISSUED" and timezone.now().date() > self.due_date

    @property
    def overdue_days(self):
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0

    @property
    def calculated_fine(self):
        """Calculate fine based on overdue days"""
        if self.is_overdue:
            library = Library.objects.filter(tenant=self.tenant, is_active=True).first()
            if library:
                fine = self.overdue_days * library.fine_per_day
                return min(fine, library.max_fine_amount)
        return 0

    @property
    def pending_fine(self):
        return self.fine_amount - self.fine_paid - self.fine_waived

    def calculate_fine(self):
        """Calculate and update fine amount"""
        self.fine_amount = self.calculated_fine
        self.save()

    def renew(self, renewed_by):
        """Renew the book issue"""
        library = Library.objects.filter(tenant=self.tenant, is_active=True).first()
        if library:
            if self.member.role == 'student':
                days = library.issue_duration_students
            else:
                days = library.issue_duration_staff
            
            self.due_date = timezone.now().date() + timezone.timedelta(days=days)
            self.renewal_count += 1
            self.last_renewal_date = timezone.now().date()
            self.issued_by = renewed_by
            self.save()

    def return_book(self, received_by, condition_notes=""):
        """Return the book"""
        self.status = "RETURNED"
        self.actual_return_date = timezone.now().date()
        self.received_by = received_by
        self.return_notes = condition_notes
        
        # Calculate final fine
        self.calculate_fine()
        self.save()
        
        # Update book copy status
        self.book_copy.return_copy()

    def mark_lost(self, notes=""):
        """Mark book as lost"""
        self.status = "LOST"
        self.return_notes = notes
        
        # Calculate replacement cost as fine
        self.fine_amount = self.book_copy.purchase_price or 500  # Default ₹500
        self.save()
        
        # Update book copy status
        self.book_copy.mark_lost()


class Reservation(BaseModel):
    """
    Book reservations by members
    """
    RESERVATION_STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("AVAILABLE", _("Available for Pickup")),
        ("ISSUED", _("Issued")),
        ("CANCELLED", _("Cancelled")),
        ("EXPIRED", _("Expired")),
    )

    member = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="book_reservations",
        verbose_name=_("Member")
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name=_("Book")
    )
    reservation_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Reservation Date")
    )
    expiry_date = models.DateTimeField(verbose_name=_("Expiry Date"))
    status = models.CharField(
        max_length=20,
        choices=RESERVATION_STATUS_CHOICES,
        default="PENDING",
        verbose_name=_("Status")
    )
    priority = models.PositiveIntegerField(default=1, verbose_name=_("Priority"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "library_reservations"
        verbose_name = _("Reservation")
        verbose_name_plural = _("Reservations")
        ordering = ["priority", "reservation_date"]
        indexes = [
            models.Index(fields=['member', 'status']),
            models.Index(fields=['book', 'status']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.member} - {self.book} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.expiry_date:
            # Set expiry to 3 days from reservation
            self.expiry_date = self.reservation_date + timezone.timedelta(days=3)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expiry_date

    def mark_available(self):
        """Mark reservation as available for pickup"""
        self.status = "AVAILABLE"
        self.save()

    def cancel(self):
        """Cancel the reservation"""
        self.status = "CANCELLED"
        self.save()
        self.book.cancel_reservation()

    def issue_book(self):
        """Issue the reserved book"""
        if self.status == "AVAILABLE" and self.book.can_be_issued:
            # Create book issue
            book_copy = self.book.copies.filter(status="AVAILABLE").first()
            if book_copy:
                BookIssue.objects.create(
                    member=self.member,
                    book_copy=book_copy,
                    issued_by=self.member,  # Should be librarian in practice
                    status="ISSUED"
                )
                self.status = "ISSUED"
                self.save()


class Fine(BaseModel):
    """
    Library fines and payments
    """
    FINE_TYPE_CHOICES = (
        ("OVERDUE", _("Overdue Fine")),
        ("LOST_BOOK", _("Lost Book")),
        ("DAMAGE", _("Damage Fine")),
        ("OTHER", _("Other")),
    )

    PAYMENT_STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("PARTIALLY_PAID", _("Partially Paid")),
        ("PAID", _("Paid")),
        ("WAIVED", _("Waived")),
        ("CANCELLED", _("Cancelled")),
    )

    member = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="library_fines",
        verbose_name=_("Member")
    )
    book_issue = models.ForeignKey(
        BookIssue,
        on_delete=models.CASCADE,
        related_name="fines",
        verbose_name=_("Book Issue")
    )
    fine_type = models.CharField(
        max_length=20,
        choices=FINE_TYPE_CHOICES,
        verbose_name=_("Fine Type")
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Amount")
    )
    paid_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Paid Amount")
    )
    waived_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Waived Amount")
    )
    due_date = models.DateField(verbose_name=_("Due Date"))
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="PENDING",
        verbose_name=_("Status")
    )
    reason = models.TextField(verbose_name=_("Reason"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    imposed_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="imposed_fines",
        verbose_name=_("Imposed By")
    )
    waived_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waived_fines",
        verbose_name=_("Waived By")
    )

    class Meta:
        db_table = "library_fines"
        verbose_name = _("Fine")
        verbose_name_plural = _("Fines")
        ordering = ["-due_date"]
        indexes = [
            models.Index(fields=['member', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]

    def __str__(self):
        return f"{self.member} - {self.amount} - {self.fine_type}"

    @property
    def pending_amount(self):
        return self.amount - self.paid_amount - self.waived_amount

    @property
    def is_overdue(self):
        return self.status == "PENDING" and timezone.now().date() > self.due_date

    def add_payment(self, amount, received_by):
        """Add payment towards fine"""
        if amount <= 0:
            raise ValidationError(_("Payment amount must be greater than 0"))
        
        if amount > self.pending_amount:
            raise ValidationError(_("Payment amount exceeds pending amount"))
        
        self.paid_amount += amount
        
        if self.pending_amount == 0:
            self.status = "PAID"
        
        self.save()
        
        # Create payment record
        FinePayment.objects.create(
            fine=self,
            amount=amount,
            received_by=received_by
        )

    def waive_amount(self, amount, waived_by, reason=""):
        """Waive part of the fine"""
        if amount <= 0:
            raise ValidationError(_("Waiver amount must be greater than 0"))
        
        if amount > self.pending_amount:
            raise ValidationError(_("Waiver amount exceeds pending amount"))
        
        self.waived_amount += amount
        
        if self.pending_amount == 0:
            self.status = "WAIVED"
        
        self.waived_by = waived_by
        self.notes = f"{self.notes}\nWaiver: {reason}"
        self.save()


class FinePayment(BaseModel):
    """
    Fine payment transactions
    """
    fine = models.ForeignKey(
        Fine,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name=_("Fine")
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Amount")
    )
    payment_date = models.DateTimeField(default=timezone.now, verbose_name=_("Payment Date"))
    payment_method = models.CharField(
        max_length=20,
        choices=(
            ("CASH", _("Cash")),
            ("ONLINE", _("Online")),
            ("CHEQUE", _("Cheque")),
            ("OTHER", _("Other")),
        ),
        default="CASH",
        verbose_name=_("Payment Method")
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Reference Number")
    )
    received_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="received_fine_payments",
        verbose_name=_("Received By")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        db_table = "library_fine_payments"
        verbose_name = _("Fine Payment")
        verbose_name_plural = _("Fine Payments")
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.fine} - {self.amount}"


class LibraryMember(BaseModel):
    """
    Library member information and statistics
    """
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="library_member",
        verbose_name=_("User")
    )
    member_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("Member ID")
    )
    membership_date = models.DateField(
        default=timezone.now,
        verbose_name=_("Membership Date")
    )
    membership_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Membership Expiry")
    )
    
    # Statistics
    total_books_issued = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Books Issued")
    )
    total_fines_paid = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Total Fines Paid")
    )
    current_books_issued = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Current Books Issued")
    )
    pending_fines = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Pending Fines")
    )
    
    # Restrictions
    is_blacklisted = models.BooleanField(default=False, verbose_name=_("Is Blacklisted"))
    blacklist_reason = models.TextField(blank=True, verbose_name=_("Blacklist Reason"))
    blacklist_until = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Blacklist Until")
    )
    
    # Preferences
    preferred_language = models.CharField(
        max_length=20,
        choices=Book.LANGUAGE_CHOICES,
        blank=True,
        verbose_name=_("Preferred Language")
    )
    preferred_categories = models.ManyToManyField(
        BookCategory,
        blank=True,
        related_name="preferred_by",
        verbose_name=_("Preferred Categories")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        db_table = "library_members"
        verbose_name = _("Library Member")
        verbose_name_plural = _("Library Members")
        ordering = ["member_id"]
        indexes = [
            models.Index(fields=['member_id']),
            models.Index(fields=['is_active', 'is_blacklisted']),
        ]

    def __str__(self):
        return f"{self.member_id} - {self.user.get_full_name()}"

    @property
    def can_issue_more_books(self):
        """Check if member can issue more books"""
        if self.is_blacklisted:
            return False
        
        library = Library.objects.filter(tenant=self.tenant, is_active=True).first()
        if library:
            if self.user.role == 'student':
                return self.current_books_issued < library.max_books_per_student
            else:
                return self.current_books_issued < library.max_books_per_staff
        return False

    @property
    def is_membership_valid(self):
        """Check if membership is valid"""
        if self.membership_expiry:
            return timezone.now().date() <= self.membership_expiry
        return True  # No expiry means permanent membership

    def blacklist(self, reason, until_date=None):
        """Blacklist the member"""
        self.is_blacklisted = True
        self.blacklist_reason = reason
        self.blacklist_until = until_date
        self.save()

    def remove_blacklist(self):
        """Remove from blacklist"""
        self.is_blacklisted = False
        self.blacklist_reason = ""
        self.blacklist_until = None
        self.save()


class LibraryReport(BaseModel):
    """
    Library reports and analytics
    """
    REPORT_TYPE_CHOICES = (
        ("ISSUE_SUMMARY", _("Issue Summary")),
        ("OVERDUE_BOOKS", _("Overdue Books")),
        ("POPULAR_BOOKS", _("Popular Books")),
        ("MEMBER_ACTIVITY", _("Member Activity")),
        ("FINE_COLLECTION", _("Fine Collection")),
        ("BOOK_ACQUISITION", _("Book Acquisition")),
        ("CATEGORY_WISE", _("Category-wise Analysis")),
        ("INVENTORY_STATUS", _("Inventory Status")),
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
        "users.User",
        on_delete=models.CASCADE,
        related_name="library_reports",
        verbose_name=_("Generated By")
    )
    generated_at = models.DateTimeField(default=timezone.now, verbose_name=_("Generated At"))
    
    # Export
    export_file = models.FileField(
        upload_to='library/reports/',
        null=True,
        blank=True,
        verbose_name=_("Export File")
    )

    class Meta:
        db_table = "library_reports"
        verbose_name = _("Library Report")
        verbose_name_plural = _("Library Reports")
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.report_name} - {self.period_start} to {self.period_end}"