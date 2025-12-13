from django.contrib import admin
from .models import (
    Library, Author, Publisher, BookCategory, Book,
    BookCopy, BookIssue
)

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'librarian', 'location', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'contact_person', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'parent_category', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

class BookCopyInline(admin.TabularInline):
    model = BookCopy
    extra = 1

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'isbn', 'category', 'author_list', 'publisher', 'total_copies', 'available_copies')
    list_filter = ('category', 'is_active', 'language')
    search_fields = ('title', 'isbn', 'authors__name')
    inlines = [BookCopyInline]

    def author_list(self, obj):
        return ", ".join([a.name for a in obj.authors.all()])
    author_list.short_description = 'Authors'

@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ('book', 'copy_number', 'barcode', 'accession_number', 'status', 'condition')
    list_filter = ('status', 'condition')
    search_fields = ('book__title', 'barcode', 'accession_number')

@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ('issue_number', 'member', 'book_copy', 'issue_date', 'due_date', 'status')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('issue_number', 'member__first_name', 'member__last_name', 'book_copy__barcode')
    date_hierarchy = 'issue_date'
