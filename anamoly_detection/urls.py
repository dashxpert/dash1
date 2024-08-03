from django.urls import path
from .views import (UploadFileView, ChangeDataTypeView, download_csv, DataCleaningView, 
                    DataCleaningOptionsView 
)
urlpatterns = [
    path('upload_file/', UploadFileView.as_view(), name='upload_file1'),
    path('change_data_type/', ChangeDataTypeView.as_view(), name='change_data_type1'),
    path('download_csv/', download_csv, name='download_csv1'),
    path('data_cleaning/', DataCleaningView.as_view(), name='data_cleaning1'),
    path('data_cleaning_options/', DataCleaningOptionsView.as_view(), name='data_cleaning_options1'),

]