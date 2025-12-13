from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('dashboard/', views.LibraryDashboardView.as_view(), name='dashboard'),
    
    # Books
    path('books/', views.BookListView.as_view(), name='book_list'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('books/create/', views.BookCreateView.as_view(), name='book_create'),
    path('books/<int:pk>/update/', views.BookUpdateView.as_view(), name='book_update'),
    path('books/<int:pk>/delete/', views.BookDeleteView.as_view(), name='book_delete'),
    
    # Authors
    path('authors/', views.AuthorListView.as_view(), name='author_list'),
    path('authors/create/', views.AuthorCreateView.as_view(), name='author_create'),
    path('authors/<int:pk>/update/', views.AuthorUpdateView.as_view(), name='author_update'),
    path('authors/<int:pk>/delete/', views.AuthorDeleteView.as_view(), name='author_delete'),
    
    # Book Issues
    path('issues/', views.BookIssueListView.as_view(), name='book_issue_list'),
    path('issues/create/', views.BookIssueCreateView.as_view(), name='book_issue_create'),
]
