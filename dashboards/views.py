from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views import View
from .forms import UploadFileForm
from .models import UploadedFile, DashboardConfig
import pandas as pd
import plotly.express as px
from django.http import HttpResponse
import plotly.io as pio
from django.template.loader import render_to_string
import io
import plotly as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator









class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

class ServicesView(View):
    def get(self, request):
        return render(request, 'services.html')

class PricingView(View):
    def get(self, request):
        return render(request, 'pricing.html')

    
class blog(View):
    def get(self, request):
        return render(request, 'blog.html')
    

from django.shortcuts import render

def about_us(request):
    return render(request, 'about_us.html')

def contact_us(request):
    return render(request, 'contact_us.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_conditions(request):
    return render(request, 'terms_conditions.html')

def cancellation_refund_policies(request):
    return render(request, 'cancellation_refund_policies.html')




#automatic dashboard creation

import pandas as pd
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import UploadFileForm
from .models import Dataset
import plotly.express as px
import hashlib
from io import StringIO
import logging

logger = logging.getLogger(__name__)



import pandas as pd
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import UploadFileForm
from .models import Dataset, Activity, Profile  # Import the Activity and Profile models
import hashlib
import logging

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class UploadFileView(View):
    def get(self, request):
        """
        Displays the form for uploading a file or selecting an existing dataset.
        """
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm(user=request.user)
        return render(request, 'dashboards/upload-dashboard.html', {'form': form})

    def post(self, request):
        """
        Handles the form submission to upload a new file or use an existing dataset.
        """
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            file = form.cleaned_data.get('file')
            existing_dataset = form.cleaned_data.get('existing_dataset')

            if file:
                # Check for duplicate dataset by file hash
                file_hash = self.generate_file_hash(file)
                if Dataset.objects.filter(file_hash=file_hash, user=request.user).exists():
                    form.add_error('file', 'This dataset has already been uploaded.')
                    Activity.objects.create(user=request.user, activity_type='Upload Failed', dataset=None, uploaded_file=None)
                    return render(request, 'dashboards/upload-dashboard.html', {'form': form})

                # Save the new dataset
                dataset = Dataset(user=request.user, name=file.name, file=file, file_hash=file_hash)
                dataset.save()
                logger.info("New dataset saved with ID: %s", dataset.id)
                Activity.objects.create(user=request.user, activity_type='File Uploaded', dataset=dataset, uploaded_file=None)

            elif existing_dataset:
                dataset = existing_dataset
                logger.info("Using existing dataset with ID: %s", dataset.id)
                Activity.objects.create(user=request.user, activity_type='Existing Dataset Selected', dataset=dataset, uploaded_file=None)
            else:
                form.add_error(None, 'You must either upload a new dataset or select an existing one.')
                return render(request, 'dashboards/upload-dashboard.html', {'form': form})

            try:
                data = pd.read_csv(dataset.file.path)
                logger.info("Data read from dataset: %s", data.head())
                csv_data = data.to_csv(index=False)
                request.session['csv_data'] = csv_data
                request.session['dataset_id'] = dataset.id

                # Increment service usage count
                if not profile.has_active_subscription():
                    profile.service_usage_count += 1
                    profile.save()

                Activity.objects.create(user=request.user, activity_type='Automatic Dashboard creation', dataset=dataset, uploaded_file=None)
                return redirect('dashboard-chart')
            except Exception as e:
                logger.error("Error reading dataset: %s", e)
                form.add_error(None, f'Error reading dataset: {e}')
                Activity.objects.create(user=request.user, activity_type='Read Dataset Failed', dataset=dataset, uploaded_file=None)
                return render(request, 'dashboards/upload-dashboard.html', {'form': form})

        logger.warning("Form is not valid. Errors: %s", form.errors)
        Activity.objects.create(user=request.user, activity_type='Form Submission Failed', dataset=None, uploaded_file=None)
        return render(request, 'dashboards/upload-dashboard.html', {'form': form})

    def generate_file_hash(self, file):
        """
        Generates a SHA-256 hash of the file content for duplicate checking.
        """
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()



@method_decorator(login_required, name='dispatch')
class Dashboard(View):
    def get(self, request):
        csv_data = request.session.get('csv_data')
        if not csv_data:
            return render(request, 'error.html', {'message': 'No data available to generate charts.'})

        data = pd.read_csv(StringIO(csv_data))
        
        # Summary statistics
        summary_stats = {
            'Total_Records': data.shape[0],
            'Date_Range': f"{data['date'].min()} to {data['date'].max()}" if 'date' in data.columns and pd.api.types.is_datetime64_any_dtype(data['date']) else 'N/A',
            'Missing_Values': data.isnull().sum().sum(),
            'Duplicates': data.duplicated().sum()
        }

        numeric_columns = data.select_dtypes(include=['int64', 'float64']).columns
        desc_stats = data[numeric_columns].describe().round(2).to_dict()
        
        # Data quality indicators
        data_quality = {
            'Missing_Values': data.isnull().sum().to_dict(),
            'Data_Types': data.dtypes.reset_index().values.tolist()
        }

        buffer = StringIO()
        data.info(buf=buffer)
        data_info = buffer.getvalue()

        # Key performance indicators (KPIs)
        kpis = {
            'Sum': data[numeric_columns].sum().round(2).to_dict(),
            'Average': data[numeric_columns].mean().round(2).to_dict(),
            'Median': data[numeric_columns].median().round(2).to_dict(),
            'Standard Deviation': data[numeric_columns].std().round(2).to_dict()
        }

        # Charts
        charts = {}
        chart_types = ['bar', 'line', 'scatter']

        if request.GET.get('column_1_x') and request.GET.get('column_1_y'):
            for i in range(3):  # Expecting 3 chart selections
                column_x = request.GET.get(f'column_{i + 1}_x')
                column_y = request.GET.get(f'column_{i + 1}_y')
                chart_type = request.GET.get(f'chart_type_{i + 1}', 'bar')
                if column_x and column_y:
                    fig = px.bar(data, x=column_x, y=column_y) if chart_type == 'bar' else (
                        px.line(data, x=column_x, y=column_y) if chart_type == 'line' else
                        px.scatter(data, x=column_x, y=column_y)
                    )
                    charts[f'chart_{i}'] = fig.to_html(full_html=False)

        return render(request, 'dashboard-chart.html', {
            'summary_stats': summary_stats,
            'desc_stats': desc_stats,
            'data_quality': data_quality,
            'kpis': kpis,
            'data_info': data_info,
            'columns_data_types': data.dtypes.reset_index().values.tolist(),
            'charts': charts,
            'columns': data.columns
        })


# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Profile, DashboardConfig, Dataset, Activity, UploadedFile

@method_decorator(login_required, name='dispatch')
class UserProfileView(View):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect('register')  # Redirect to registration page if the user is not authenticated

        profile = get_object_or_404(Profile, user=user)
        dashboard_configs = DashboardConfig.objects.filter(user=user)
        datasets = Dataset.objects.filter(user=user)
        uploaded_files = UploadedFile.objects.all()  # assuming all files are accessible
        activities = Activity.objects.filter(user=user)

        context = {
            'profile': profile,
            'dashboard_configs': dashboard_configs,
            'datasets': datasets,
            'uploaded_files': uploaded_files,
            'activities': activities,
        }

        return render(request, 'user_profile.html', context)
