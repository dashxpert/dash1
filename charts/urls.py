
from django.urls import path
from .views import  UploadFileView,ChartOptionsView
from . import views  # Import views


urlpatterns = [
   path('upload/', UploadFileView.as_view(), name='upload'),
    
    path('chart-options/', ChartOptionsView.as_view(), name='chart_options'),
   
     path('generate-chart/', views.generate_chart, name='generate_chart'),
 

       
]

