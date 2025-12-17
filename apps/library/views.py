from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from .models import Library, Author, Publisher, BookCategory, Book, BookCopy, BookIssue
from .forms import (
    LibraryForm, AuthorForm, PublisherForm, BookCategoryForm, 
    BookForm, BookCopyForm, BookIssueForm
)
from apps.core.views import (
    BaseTemplateView, BaseListView, BaseDetailView, 
    BaseCreateView, BaseUpdateView, BaseDeleteView
)
from apps.core.utils.tenant import get_current_tenant
from django.db.models import Count, Q

# ==================== DASHBOARD ====================

class LibraryDashboardView(BaseTemplateView):
    template_name = 'library/dashboard.html'
    permission_required = 'library.view_dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_books'] = Book.objects.filter(tenant=tenant, is_active=True).count()
        context['issued_books'] = BookIssue.objects.filter(tenant=tenant, status='ISSUED').count()
        context['overdue_books'] = BookIssue.objects.filter(tenant=tenant, status='ISSUED', due_date__lt=self.request.user.date_joined.date()).count() # Mocking overdue check date
        # Note: Actual overdue check should compare with verification date, simplified here.
        
        context['recent_issues'] = BookIssue.objects.filter(tenant=tenant).order_by('-issue_date')[:5]
        return context

# ==================== AUTHORS ====================

class AuthorListView(BaseListView):
    model = Author
    template_name = 'library/author_list.html'
    context_object_name = 'authors'
    permission_required = 'library.view_author'
    filterset_fields = ['name', 'is_active']
    search_fields = ['name', 'nationality']

class AuthorCreateView(BaseCreateView):
    model = Author
    form_class = AuthorForm
    template_name = 'library/author_form.html'
    permission_required = 'library.add_author'
    success_url = reverse_lazy('library:author_list')

class AuthorUpdateView(BaseUpdateView):
    model = Author
    form_class = AuthorForm
    template_name = 'library/author_form.html'
    permission_required = 'library.change_author'
    success_url = reverse_lazy('library:author_list')

class AuthorDeleteView(BaseDeleteView):
    model = Author
    template_name = 'library/confirm_delete.html'
    permission_required = 'library.delete_author'
    success_url = reverse_lazy('library:author_list')

# ==================== PUBLISHERS ====================

class PublisherListView(BaseListView):
    model = Publisher
    template_name = 'library/publisher_list.html'
    context_object_name = 'publishers'
    permission_required = 'library.view_publisher'
    search_fields = ['name', 'contact_person', 'email']

class PublisherCreateView(BaseCreateView):
    model = Publisher
    form_class = PublisherForm
    template_name = 'library/publisher_form.html'
    permission_required = 'library.add_publisher'
    success_url = reverse_lazy('library:publisher_list')

class PublisherUpdateView(BaseUpdateView):
    model = Publisher
    form_class = PublisherForm
    template_name = 'library/publisher_form.html'
    permission_required = 'library.change_publisher'
    success_url = reverse_lazy('library:publisher_list')

class PublisherDeleteView(BaseDeleteView):
    model = Publisher
    template_name = 'library/confirm_delete.html'
    permission_required = 'library.delete_publisher'
    success_url = reverse_lazy('library:publisher_list')

# ==================== CATEGORIES ====================

class BookCategoryListView(BaseListView):
    model = BookCategory
    template_name = 'library/category_list.html'
    context_object_name = 'categories'
    permission_required = 'library.view_bookcategory'
    search_fields = ['name', 'code']

class BookCategoryCreateView(BaseCreateView):
    model = BookCategory
    form_class = BookCategoryForm
    template_name = 'library/category_form.html'
    permission_required = 'library.add_bookcategory'
    success_url = reverse_lazy('library:category_list')

class BookCategoryUpdateView(BaseUpdateView):
    model = BookCategory
    form_class = BookCategoryForm
    template_name = 'library/category_form.html'
    permission_required = 'library.change_bookcategory'
    success_url = reverse_lazy('library:category_list')

class BookCategoryDeleteView(BaseDeleteView):
    model = BookCategory
    template_name = 'library/confirm_delete.html'
    permission_required = 'library.delete_bookcategory'
    success_url = reverse_lazy('library:category_list')

# ==================== BOOKS ====================

class BookListView(BaseListView):
    model = Book
    template_name = 'library/book_list.html'
    context_object_name = 'books'
    permission_required = 'library.view_book'
    search_fields = ['title', 'isbn', 'publisher__name']
    filterset_fields = ['category', 'book_type', 'language', 'is_active']

class BookDetailView(BaseDetailView):
    model = Book
    template_name = 'library/book_detail.html'
    context_object_name = 'book'
    permission_required = 'library.view_book'

class BookCreateView(BaseCreateView):
    model = Book
    form_class = BookForm
    template_name = 'library/book_form.html'
    permission_required = 'library.add_book'
    success_url = reverse_lazy('library:book_list')

class BookUpdateView(BaseUpdateView):
    model = Book
    form_class = BookForm
    template_name = 'library/book_form.html'
    permission_required = 'library.change_book'
    success_url = reverse_lazy('library:book_list')

class BookDeleteView(BaseDeleteView):
    model = Book
    template_name = 'library/confirm_delete.html'
    permission_required = 'library.delete_book'
    success_url = reverse_lazy('library:book_list')

# ==================== BOOK COPIES ====================

class BookCopyListView(BaseListView):
    model = BookCopy
    template_name = 'library/copy_list.html'
    context_object_name = 'copies'
    permission_required = 'library.view_bookcopy'
    search_fields = ['barcode', 'accession_number', 'book__title']
    filterset_fields = ['status', 'condition', 'is_active']

class BookCopyCreateView(BaseCreateView):
    model = BookCopy
    form_class = BookCopyForm
    template_name = 'library/copy_form.html'
    permission_required = 'library.add_bookcopy'
    success_url = reverse_lazy('library:copy_list')

class BookCopyUpdateView(BaseUpdateView):
    model = BookCopy
    form_class = BookCopyForm
    template_name = 'library/copy_form.html'
    permission_required = 'library.change_bookcopy'
    success_url = reverse_lazy('library:copy_list')

class BookCopyDeleteView(BaseDeleteView):
    model = BookCopy
    template_name = 'library/confirm_delete.html'
    permission_required = 'library.delete_bookcopy'
    success_url = reverse_lazy('library:copy_list')

# ==================== ISSUES ====================

class BookIssueListView(BaseListView):
    model = BookIssue
    template_name = 'library/issue_list.html'
    context_object_name = 'issues'
    permission_required = 'library.view_bookissue'
    search_fields = ['issue_number', 'member__username', 'book_copy__barcode']
    filterset_fields = ['status']

class BookIssueCreateView(BaseCreateView):
    model = BookIssue
    form_class = BookIssueForm
    template_name = 'library/issue_form.html'
    permission_required = 'library.add_bookissue'
    success_url = reverse_lazy('library:issue_list')
    
    def form_valid(self, form):
        form.instance.issued_by = self.request.user
        return super().form_valid(form)

class BookIssueDetailView(BaseDetailView):
    model = BookIssue
    template_name = 'library/issue_detail.html'
    context_object_name = 'issue'
    permission_required = 'library.view_bookissue'

class BookIssueUpdateView(BaseUpdateView):
    model = BookIssue
    form_class = BookIssueForm
    template_name = 'library/issue_form.html'
    permission_required = 'library.change_bookissue'
    success_url = reverse_lazy('library:issue_list')

# Note: Issues are typically not deleted but returned/cancelled. 
# Implementing DeleteView for admin correction purposes.
class BookIssueDeleteView(BaseDeleteView):
    model = BookIssue
    template_name = 'library/confirm_delete.html'
    permission_required = 'library.delete_bookissue'
    success_url = reverse_lazy('library:issue_list')
