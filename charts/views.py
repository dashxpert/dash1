import hashlib
import io
import pandas as pd
from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from dashboards.forms import UploadFileForm
from dashboards.models import Dataset
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from django.utils.decorators import method_decorator


from django.shortcuts import render, redirect
from django.views import View
from dashboards.forms import UploadFileForm
from dashboards.models import Dataset
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from dashboards.models import Profile, Activity  # Import the Activity model
import pandas as pd
import hashlib
import logging

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class UploadFileView(View):
    def get(self, request):
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm(user=request.user)
        return render(request, 'upload.html', {'form': form})

    def post(self, request):
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            existing_dataset = form.cleaned_data['existing_dataset']

            if file:
                file_hash = self.generate_file_hash(file)
                if Dataset.objects.filter(file_hash=file_hash, user=request.user).exists():
                    form.add_error('file', 'This dataset has already been uploaded.')
                    Activity.objects.create(user=request.user, activity_type='Upload Failed', dataset=None, uploaded_file=None)
                    return render(request, 'upload.html', {'form': form})

                dataset = Dataset(user=request.user, name=file.name, file=file, file_hash=file_hash)
                dataset.save()
                logger.info("New dataset saved with ID: %s", dataset.id)
                Activity.objects.create(user=request.user, activity_type='Chart Creation', dataset=dataset, uploaded_file=None)

            elif existing_dataset:
                dataset = existing_dataset
                logger.info("Using existing dataset with ID: %s", dataset.id)
                Activity.objects.create(user=request.user, activity_type='Chart creation', dataset=dataset, uploaded_file=None)
            else:
                form.add_error(None, 'You must either upload a new dataset or select an existing one.')
                return render(request, 'upload.html', {'form': form})

            try:
                data = pd.read_csv(dataset.file.path)
                logger.info("Data read from dataset: %s", data.head())
                csv_data = data.to_csv(index=False)
                request.session['csv_data'] = csv_data
                request.session['dataset_id'] = dataset.id
                
                # Increment usage count
                if not profile.has_active_subscription():
                    profile.service_usage_count += 1
                    profile.save()

                return redirect('chart_options')
            except Exception as e:
                logger.error("Error reading dataset: %s", e)
                form.add_error(None, f'Error reading dataset: {e}')
                Activity.objects.create(user=request.user, activity_type='Read Dataset Failed', dataset=dataset, uploaded_file=None)
                return render(request, 'upload.html', {'form': form})

        logger.warning("Form is not valid. Errors: %s", form.errors)
        Activity.objects.create(user=request.user, activity_type='Form Submission Failed', dataset=None, uploaded_file=None)
        return render(request, 'upload.html', {'form': form})

    def generate_file_hash(self, file):
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()

@method_decorator(login_required, name='dispatch')
class ChartOptionsView(View):
    def get(self, request):
        csv_data = request.session.get('csv_data')
        if not csv_data:
            return render(request, 'error.html', {'message': 'No data available.'})
        
        # Convert CSV data to DataFrame
        data = pd.read_csv(io.StringIO(csv_data))
        columns = data.columns
        request.session['data'] = csv_data  # Store CSV data in session for chart generation
        
        return render(request, 'chart_options.html', {'columns': columns})

    def post(self, request):
        x_axis = request.POST.get('x_axis')
        y_axis = request.POST.get('y_axis')
        chart_type = request.POST.get('chart_type')

        if not x_axis or not y_axis or not chart_type:
            return render(request, 'chart_options.html', {'error': 'All fields are required.'})

        request.session['x_axis'] = x_axis
        request.session['y_axis'] = y_axis
        request.session['chart_type'] = chart_type
        return redirect('generate_chart')


@login_required
def generate_chart(request):
    csv_data = request.session.get('csv_data')
    x_axis = request.session.get('x_axis')
    y_axis = request.session.get('y_axis')
    chart_type = request.session.get('chart_type')

    if not csv_data:
        return render(request, 'error.html', {'message': 'No data available to generate the chart.'})

    # Convert CSV data to DataFrame
    data = pd.read_csv(io.StringIO(csv_data))

    if data.empty:
        return render(request, 'error.html', {'message': 'Data is empty.'})

    if chart_type == 'Bar':
        fig = px.bar(data, x=x_axis, y=y_axis, color=x_axis, text=y_axis, color_discrete_sequence=px.colors.qualitative.Set1)
        fig.update_traces(textposition='outside')
    elif chart_type == 'Line':
        fig = px.line(data, x=x_axis, y=y_axis, color=x_axis, text=y_axis, color_discrete_sequence=px.colors.qualitative.Set1)
        fig.update_traces(textposition='top center')
    elif chart_type == 'Scatter':
        fig = px.scatter(data, x=x_axis, y=y_axis, color=x_axis, text=y_axis, color_discrete_sequence=px.colors.qualitative.Set1)
        fig.update_traces(textposition='top center')
    elif chart_type == 'Pie':
        fig = px.pie(data, names=x_axis, values=y_axis, color=x_axis, color_discrete_sequence=px.colors.qualitative.Set1)
        fig.update_traces(textinfo='percent+label')
    elif chart_type == 'Histogram':
        fig = px.histogram(data, x=x_axis, color=x_axis, text_auto=True, color_discrete_sequence=px.colors.qualitative.Set1)
    elif chart_type == 'Box':
        fig = px.box(data, x=x_axis, y=y_axis, color=x_axis, color_discrete_sequence=px.colors.qualitative.Set1)
    else:
        return render(request, 'error.html', {'message': 'Invalid chart type selected.'})

    chart_html = fig.to_html(full_html=False)
    return render(request, 'dashboard.html', {'chart': chart_html})
