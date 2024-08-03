import os
import pandas as pd
import hashlib
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import PivotTableForm, FileUploadForm
from dashboards.models import Dataset, Activity
import logging

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class UploadFileView1(View):
    def get(self, request):
        """
        Displays the form for uploading a file or selecting an existing dataset.
        """
        form = FileUploadForm(user=request.user)
        return render(request, 'pivot_service/upload_file.html', {'form': form})

    def post(self, request):
        """
        Handles the form submission to upload a new file or use an existing dataset.
        """
        form = FileUploadForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            data_file = form.cleaned_data.get('data_file')
            existing_dataset = form.cleaned_data.get('existing_dataset')

            if data_file:
                # Check for duplicate dataset by file hash
                file_hash = self.generate_file_hash(data_file)
                existing_dataset = Dataset.objects.filter(file_hash=file_hash, user=request.user).first()

                if existing_dataset:
                    form.add_error('data_file', 'This dataset has already been uploaded.')
                    Activity.objects.create(user=request.user, activity_type='Upload Failed', dataset=None, uploaded_file=None)
                    return render(request, 'pivot_service/upload_file.html', {'form': form})

                # Save the new dataset
                dataset = Dataset(user=request.user, name=data_file.name, file=data_file, file_hash=file_hash)
                dataset.save()
                logger.info("New dataset saved with ID: %s", dataset.id)
                Activity.objects.create(user=request.user, activity_type='File Uploaded', dataset=dataset, uploaded_file=None)

            elif existing_dataset:
                dataset = existing_dataset
                logger.info("Using existing dataset with ID: %s", dataset.id)
                Activity.objects.create(user=request.user, activity_type='Existing Dataset Selected', dataset=dataset, uploaded_file=None)
            else:
                form.add_error(None, 'You must either upload a new dataset or select an existing one.')
                return render(request, 'pivot_service/upload_file.html', {'form': form})

            # Process the dataset
            try:
                data = pd.read_csv(dataset.file.path)
                request.session['csv_data'] = data.to_csv(index=False)
                request.session['dataset_id'] = dataset.id

                Activity.objects.create(user=request.user, activity_type='Pivot_operation', dataset=dataset, uploaded_file=None)
                return redirect('pivot_column_selection')
            except Exception as e:
                logger.error("Error reading dataset: %s", e)
                form.add_error(None, f'Error reading dataset: {e}')
                Activity.objects.create(user=request.user, activity_type='Read Dataset Failed', dataset=dataset, uploaded_file=None)
                return render(request, 'pivot_service/upload_file.html', {'form': form})

        logger.warning("Form is not valid. Errors: %s", form.errors)
        Activity.objects.create(user=request.user, activity_type='Form Submission Failed', dataset=None, uploaded_file=None)
        return render(request, 'pivot_service/upload_file.html', {'form': form})

    def generate_file_hash(self, file):
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()


def pivot_column_selection_view(request):
    dataset_id = request.session.get('dataset_id')
    if not dataset_id:
        return redirect('upload_file')

    try:
        dataset = Dataset.objects.get(id=dataset_id)
    except Dataset.DoesNotExist:
        return redirect('upload_file')

    file_path = dataset.file.path
    if not os.path.exists(file_path):
        return redirect('upload_file')

    df = pd.read_csv(file_path)
    column_choices = [(col, col) for col in df.columns]

    if request.method == 'POST':
        form = PivotTableForm(request.POST, column_choices=column_choices)
        if form.is_valid():
            rows = form.cleaned_data['rows']
            columns = form.cleaned_data['columns']
            values = form.cleaned_data['values']
            aggregation = form.cleaned_data['aggregation']

            if rows == 'None':
                rows = []
            else:
                rows = [rows]

            if columns == 'None':
                columns = []
            else:
                columns = [columns]

            if aggregation == 'sum':
                aggfunc = 'sum'
            elif aggregation == 'count':
                aggfunc = 'count'
            elif aggregation == 'min':
                aggfunc = 'min'
            elif aggregation == 'max':
                aggfunc = 'max'
            elif aggregation == 'avg':
                aggfunc = 'mean'
            elif aggregation == 'mul':
                aggfunc = 'prod'
            elif aggregation == 'div':
                aggfunc = lambda x: x.prod() if 0 not in x else 0

            pivot_df = pd.pivot_table(df, index=rows, columns=columns, values=values, aggfunc=aggfunc)

            # Save the pivot table to the session with index included
            request.session['pivot_table_csv'] = pivot_df.to_csv(index=True)  # Ensure index is included
            request.session['pivot_table_html'] = pivot_df.to_html()

            return redirect('pivot_result')
    else:
        form = PivotTableForm(column_choices=column_choices)

    return render(request, 'pivot_service/pivot_column_selection.html', {'form': form})

from django.shortcuts import render, redirect
from django.http import HttpResponse

def pivot_table_results_view(request):
    pivot_html = request.session.get('pivot_table_html')
    if not pivot_html:
        return redirect('pivot_column_selection')

    if request.method == 'POST' and 'download_csv' in request.POST:
        csv_data = request.session.get('pivot_table_csv')
        if not csv_data:
            return redirect('pivot_column_selection')
        
        # Create the HttpResponse for downloading the CSV
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=pivot_table.csv'
        return response

    return render(request, 'pivot_service/pivot_result.html', {'pivot_table': pivot_html})
