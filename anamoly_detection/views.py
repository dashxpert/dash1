import hashlib
import pandas as pd
from io import StringIO
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import DataCleaningForm, ChangeDataTypeForm, UploadFileForm, ConcatenationForm, DataCleaningForm, RemoveNullForm, ReplaceBlankForm, FillNAForm, DropNAForm, ConcatenationForm

from dashboards.models import Dataset
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class UploadFileView(View):
    def get(self, request):
        form = UploadFileForm(user=request.user)
        return render(request, 'upload_file.html', {'form': form})

    def post(self, request):
        form = UploadFileForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            file = form.cleaned_data.get('file')
            existing_dataset = form.cleaned_data.get('existing_dataset')

            if file:
                file_hash = self.generate_file_hash(file)
                if Dataset.objects.filter(file_hash=file_hash, user=request.user).exists():
                    form.add_error('file', 'This dataset has already been uploaded.')
                    return render(request, 'upload_file.html', {'form': form})

                dataset = Dataset(user=request.user, name=file.name, file=file, file_hash=file_hash)
                dataset.save()
                logger.info("New dataset saved with ID: %s", dataset.id)

            elif existing_dataset:
                dataset = existing_dataset
                logger.info("Using existing dataset with ID: %s", dataset.id)
            else:
                form.add_error(None, 'You must either upload a new dataset or select an existing one.')
                return render(request, 'upload_file.html', {'form': form})

            try:
                data = pd.read_csv(dataset.file.path)
                logger.info("Data read from dataset: %s", data.head())
                csv_data = data.to_csv(index=False)
                request.session['csv_data'] = csv_data
                request.session['dataset_id'] = dataset.id
                return redirect('data_cleaning_options')
            except Exception as e:
                logger.error("Error reading dataset: %s", e)
                form.add_error(None, f'Error reading dataset: {e}')
                return render(request, 'upload_file.html', {'form': form})

        logger.warning("Form is not valid. Errors: %s", form.errors)
        return render(request, 'upload_file.html', {'form': form})

    def generate_file_hash(self, file):
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()


class DataCleaningOptionsView(View):
    def get(self, request):
        form = DataCleaningForm()
        return render(request, 'data_cleaning_options.html', {'form': form})
    
    def post(self, request):
        form = DataCleaningForm(request.POST)
        if form.is_valid():
            feature = form.cleaned_data['data']
            return redirect(feature)
        return render(request, 'data_cleaning_options.html', {'form': form})



@method_decorator(login_required, name='dispatch')
class ChangeDataTypeView(View):
    def get(self, request):
        csv_data = request.session.get('csv_data', None)
        if not csv_data:
            logger.warning("No CSV data in session. Redirecting to upload page.")
            return redirect('upload_file')

        try:
            data = pd.read_csv(StringIO(csv_data))
        except Exception as e:
            logger.error("Error reading CSV data from session: %s", e)
            return redirect('upload_file')

        form = ChangeDataTypeForm()
        all_columns = [(col, col) for col in data.columns]
        form.fields['data_type_cols'].choices = all_columns
        
        return render(request, 'change_data_type.html', {'form': form})

    def post(self, request):
        csv_data = request.session.get('csv_data', None) 
        if not csv_data:
            logger.warning("No CSV data in session. Redirecting to upload page.")
            return redirect('upload_file')

        try:
            data = pd.read_csv(StringIO(csv_data))
        except Exception as e:
            logger.error("Error reading CSV data from session: %s", e)
            return redirect('upload_file')

        form = ChangeDataTypeForm(request.POST)
        all_columns = [(col, col) for col in data.columns]
        form.fields['data_type_cols'].choices = all_columns

        if form.is_valid():
            try:
                data_type = form.cleaned_data['data_type']
                data_type_cols = form.cleaned_data['data_type_cols']

                if data_type:
                    if data_type == 'int_to_str':
                        data[data_type_cols] = data[data_type_cols].astype(str)
                    elif data_type == 'str_to_int':
                        data[data_type_cols] = data[data_type_cols].apply(pd.to_numeric, errors='coerce')
                    elif data_type == 'str_to_date':
                        data[data_type_cols] = data[data_type_cols].apply(pd.to_datetime, errors='coerce')

                cleaned_file = data.to_csv(index=False)
                request.session['cleaned_data'] = cleaned_file
                return redirect('data_cleaning')
            except Exception as e:
                logger.error("Error processing data cleaning: %s", e)
                form.add_error(None, 'Error processing the data. Please try again.')

        return render(request, 'change_data_type.html', {'form': form})

@login_required
def download_csv(request):
    cleaned_data = request.session.get('cleaned_data')
    if cleaned_data is None:
        return redirect('upload_file')

    response = HttpResponse(cleaned_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cleaned_data.csv"'
    return response

@method_decorator(login_required, name='dispatch')
class DataCleaningView(View):
    def get(self, request):
        cleaned_data = request.session.get('cleaned_data', None)
        if not cleaned_data:
            logger.warning("No cleaned data in session. Redirecting to upload page.")
            return redirect('upload_file')

        try:
            data = pd.read_csv(StringIO(cleaned_data))
        except Exception as e:
            logger.error("Error reading cleaned data from session: %s", e)
            return redirect('upload_file')

        return render(request, 'data_cleaning.html', {'data': data.head().to_html(classes='table table-striped')})


