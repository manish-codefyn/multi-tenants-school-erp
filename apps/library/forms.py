from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Author, Publisher, BookCategory, Book, BookCopy, BookIssue, Library
from apps.core.forms import TenantAwareModelForm
from apps.core.utils.form_helpers import DateInput, SelectWithSearch, TimeInput, SelectMultipleWithSearch

class LibraryForm(TenantAwareModelForm):
    class Meta:
        model = Library
        fields = ['name', 'code', 'email', 'phone', 'location', 'building', 'floor', 
                  'librarian', 'opening_time', 'closing_time', 'rules_regulations']
        widgets = {
            'opening_time': TimeInput(),
            'closing_time': TimeInput(),
            'rules_regulations': forms.Textarea(attrs={'rows': 4}),
        }

class AuthorForm(TenantAwareModelForm):
    class Meta:
        model = Author
        fields = ['name', 'biography', 'date_of_birth', 'date_of_death', 'nationality', 'website', 'photo', 'is_active']
        widgets = {
            'date_of_birth': DateInput(),
            'date_of_death': DateInput(),
            'biography': forms.Textarea(attrs={'rows': 3}),
        }

class PublisherForm(TenantAwareModelForm):
    class Meta:
        model = Publisher
        fields = ['name', 'address', 'email', 'phone', 'website', 'contact_person', 'is_active']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class BookCategoryForm(TenantAwareModelForm):
    class Meta:
        model = BookCategory
        fields = ['name', 'code', 'description', 'parent_category', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'parent_category': SelectWithSearch(),
        }

class BookForm(TenantAwareModelForm):
    class Meta:
        model = Book
        fields = ['isbn', 'title', 'subtitle', 'category', 'book_type', 'authors', 'publisher', 
                  'publication_year', 'edition', 'volume', 'language', 'binding', 'pages', 
                  'description', 'total_copies', 'shelf_number', 'rack_number', 
                  'acquisition_date', 'acquisition_price', 'is_reference', 'is_active',
                  'cover_image', 'digital_copy', 'notes']
        widgets = {
            'category': SelectWithSearch(),
            'authors': SelectMultipleWithSearch(),
            'publisher': SelectWithSearch(),
            'acquisition_date': DateInput(),
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class BookCopyForm(TenantAwareModelForm):
    class Meta:
        model = BookCopy
        fields = ['book', 'copy_number', 'barcode', 'accession_number', 'purchase_price', 
                  'purchase_date', 'supplier', 'condition', 'status', 'is_active']
        widgets = {
            'book': SelectWithSearch(),
            'purchase_date': DateInput(),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class BookIssueForm(TenantAwareModelForm):
    class Meta:
        model = BookIssue
        fields = ['member', 'book_copy', 'issue_date', 'due_date', 'issue_notes']
        widgets = {
            'member': SelectWithSearch(),
            'book_copy': SelectWithSearch(),
            'issue_date': DateInput(),
            'due_date': DateInput(),
            'issue_notes': forms.Textarea(attrs={'rows': 2}),
        }
