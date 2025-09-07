"""
URL configuration for Books domain.
"""
from django.urls import path

from .views import BookInfoView, BookListView, ChaptersByBookView

app_name = "books"

urlpatterns = [
    path("", BookListView.as_view(), name="books_list"),
    path("<str:book_name>/chapters/", ChaptersByBookView.as_view(), name="book_chapters"),
    path("<str:book_name>/info/", BookInfoView.as_view(), name="book_info"),
]
