from django.urls import path, include
from . import views

app_name = 'library'

urlpatterns = [
    path('dashboard/', views.LibraryDashboardView.as_view(), name='dashboard'),
    
    # Authors
    path('authors/', include([
        path('', views.AuthorListView.as_view(), name='author_list'),
        path('create/', views.AuthorCreateView.as_view(), name='author_create'),
        path('<uuid:pk>/', include([
            path('update/', views.AuthorUpdateView.as_view(), name='author_update'),
            path('delete/', views.AuthorDeleteView.as_view(), name='author_delete'),
        ])),
    ])),

    # Publishers
    path('publishers/', include([
        path('', views.PublisherListView.as_view(), name='publisher_list'),
        path('create/', views.PublisherCreateView.as_view(), name='publisher_create'),
        path('<uuid:pk>/', include([
            path('update/', views.PublisherUpdateView.as_view(), name='publisher_update'),
            path('delete/', views.PublisherDeleteView.as_view(), name='publisher_delete'),
        ])),
    ])),
    
    # Categories
    path('categories/', include([
        path('', views.BookCategoryListView.as_view(), name='category_list'),
        path('create/', views.BookCategoryCreateView.as_view(), name='category_create'),
        path('<uuid:pk>/', include([
            path('update/', views.BookCategoryUpdateView.as_view(), name='category_update'),
            path('delete/', views.BookCategoryDeleteView.as_view(), name='category_delete'),
        ])),
    ])),

    # Books
    path('books/', include([
        path('', views.BookListView.as_view(), name='book_list'),
        path('create/', views.BookCreateView.as_view(), name='book_create'),
        path('<uuid:pk>/', include([
            path('', views.BookDetailView.as_view(), name='book_detail'),
            path('update/', views.BookUpdateView.as_view(), name='book_update'),
            path('delete/', views.BookDeleteView.as_view(), name='book_delete'),
        ])),
    ])),

    # Book Copies
    path('copies/', include([
        path('', views.BookCopyListView.as_view(), name='copy_list'),
        path('create/', views.BookCopyCreateView.as_view(), name='copy_create'),
        path('<uuid:pk>/', include([
            path('update/', views.BookCopyUpdateView.as_view(), name='copy_update'),
            path('delete/', views.BookCopyDeleteView.as_view(), name='copy_delete'),
        ])),
    ])),

    # Issues
    path('issues/', include([
        path('', views.BookIssueListView.as_view(), name='issue_list'),
        path('create/', views.BookIssueCreateView.as_view(), name='issue_create'),
        path('<uuid:pk>/', include([
            path('', views.BookIssueDetailView.as_view(), name='issue_detail'),
            path('update/', views.BookIssueUpdateView.as_view(), name='issue_update'),
            path('delete/', views.BookIssueDeleteView.as_view(), name='issue_delete'),
        ])),
    ])),
]
