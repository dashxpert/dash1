# pivot_service/urls.py
from django.urls import path
from .views import UploadFileView1, pivot_column_selection_view, pivot_table_results_view

urlpatterns = [
    path('upload_pivot/', UploadFileView1.as_view(), name='upload_file1'),
    path('pivot/', pivot_column_selection_view, name='pivot_column_selection'),
    path('pivot_result/', pivot_table_results_view, name='pivot_result'),
]
