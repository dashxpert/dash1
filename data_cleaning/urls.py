from django.urls import path
from .views import (UploadFileView, ChangeDataTypeView, download_csv, DataCleaningView, 
                    DataCleaningOptionsView, ConcatenationView, DropNAView, FillNAView,
                    ReplaceBlankView, RemoveNullView,RemoveDuplicatesView, FindReplaceView,
                    ExtractView
)
urlpatterns = [
    path('upload_file/', UploadFileView.as_view(), name='upload_file'),
    path('change_data_type/', ChangeDataTypeView.as_view(), name='change_data_type'),
    path('download_csv/', download_csv, name='download_csv'),
    path('data_cleaning/', DataCleaningView.as_view(), name='data_cleaning'),
    path('data_cleaning_options/', DataCleaningOptionsView.as_view(), name='data_cleaning_options'),
    path('concatenation/', ConcatenationView.as_view(), name='concatenation'),
    path('drop_na/', DropNAView.as_view(), name='drop_na'),
    path('fill_na/', FillNAView.as_view(), name='fill_na'),
    path('replace_blank/', ReplaceBlankView.as_view(), name='replace_blank'),
    path('remove_null/', RemoveNullView.as_view(), name='remove_null'),
    path('remove_duplicates/', RemoveDuplicatesView.as_view(), name='remove_duplicates'),
    path('find_replace/', FindReplaceView.as_view(), name='find_replace'),
    path('extract/', ExtractView.as_view(), name='extract'),
]

