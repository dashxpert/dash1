# join_append/urls.py

from django.urls import path
from .views import UploadFilesForJoinView, UploadFilesForAppendView,DownloadJoinedCSVView,SelectSecondDatasetView, SelectColumnsView, JoinSuccessView, table_action, upload_files_for_join

urlpatterns = [
    path('upload-files-for-join/', UploadFilesForJoinView.as_view(), name='upload_files_for_join'),
    path('select-second-dataset/', SelectSecondDatasetView.as_view(), name='select_second_dataset'),
    path('select-columns/', SelectColumnsView.as_view(), name='select_columns'),
    path('join-success/', JoinSuccessView.as_view(), name='join_success'),
    path('table-action/', table_action, name='table_action'),
    path('join-tables/', upload_files_for_join, name='join_tables'),
    path('download-joined-csv/', DownloadJoinedCSVView.as_view(), name='download_joined_csv'),
    path('upload_files_for_append/', UploadFilesForAppendView.as_view(), name='upload_files_for_append'),
]
