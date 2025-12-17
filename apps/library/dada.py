from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count
from apps.core.permissions.mixins import PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import Library, Book, Author, Publisher, BookCategory, BookIssue

class LibraryDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'library/dashboard.html'
    permission_required = 'library.view_book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_books'] = Book.objects.filter(tenant=tenant, is_active=True).count()
        context['available_books'] = Book.objects.filter(tenant=tenant, is_active=True, available_copies__gt=0).count()
        context['issued_books'] = BookIssue.objects.filter(tenant=tenant, status='ISSUED').count()
        context['overdue_books'] = BookIssue.objects.filter(tenant=tenant, status='OVERDUE').count()
        
        return context

# ==================== BOOK ====================

class BookListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Book
    template_name = 'library/book_list.html'
    context_object_name = 'books'
    permission_required = 'library.view_book'

class BookDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Book
    template_name = 'library/book_detail.html'
    context_object_name = 'book'
    permission_required = 'library.view_book'

class BookCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Book
    fields = ['isbn', 'title', 'subtitle', 'category', 'book_type', 'publisher', 
              'publication_year', 'edition', 'language', 'binding', 'pages', 
              'description', 'total_copies', 'shelf_number', 'rack_number', 
              'acquisition_date', 'acquisition_price', 'is_reference', 'is_active']
    template_name = 'library/book_form.html'
    success_url = reverse_lazy('library:book_list')
    permission_required = 'library.add_book'

    def form_valid(self, form):
        messages.success(self.request, "Book created successfully.")
        return super().form_valid(form)

class BookUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Book
    fields = ['isbn', 'title', 'subtitle', 'category', 'book_type', 'publisher', 
              'publication_year', 'edition', 'language', 'binding', 'pages', 
              'description', 'total_copies', 'shelf_number', 'rack_number', 
              'acquisition_date', 'acquisition_price', 'is_reference', 'is_active']
    template_name = 'library/book_form.html'
    success_url = reverse_lazy('library:book_list')
    permission_required = 'library.change_book'

    def form_valid(self, form):
        messages.success(self.request, "Book updated successfully.")
        return super().form_valid(form)

class BookDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = 'library/confirm_delete.html'
    success_url = reverse_lazy('library:book_list')
    permission_required = 'library.delete_book'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Book deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== AUTHOR ====================

class AuthorListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Author
    template_name = 'library/author_list.html'
    context_object_name = 'authors'
    permission_required = 'library.view_author'

class AuthorCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Author
    fields = ['name', 'biography', 'date_of_birth', 'nationality', 'website', 'is_active']
    template_name = 'library/author_form.html'
    success_url = reverse_lazy('library:author_list')
    permission_required = 'library.add_author'

    def form_valid(self, form):
        messages.success(self.request, "Author created successfully.")
        return super().form_valid(form)

class AuthorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Author
    fields = ['name', 'biography', 'date_of_birth', 'nationality', 'website', 'is_active']
    template_name = 'library/author_form.html'
    success_url = reverse_lazy('library:author_list')
    permission_required = 'library.change_author'

    def form_valid(self, form):
        messages.success(self.request, "Author updated successfully.")
        return super().form_valid(form)

class AuthorDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Author
    template_name = 'library/confirm_delete.html'
    success_url = reverse_lazy('library:author_list')
    permission_required = 'library.delete_author'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Author deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== BOOK ISSUE ====================

class BookIssueListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = BookIssue
    template_name = 'library/book_issue_list.html'
    context_object_name = 'issues'
    permission_required = 'library.view_bookissue'

class BookIssueCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = BookIssue
    fields = ['member', 'book_copy', 'issue_date', 'due_date', 'issue_notes']
    template_name = 'library/book_issue_form.html'
    success_url = reverse_lazy('library:book_issue_list')
    permission_required = 'library.add_bookissue'

    def form_valid(self, form):
        form.instance.issued_by = self.request.user
        messages.success(self.request, "Book issued successfully.")
        return super().form_valid(form)
