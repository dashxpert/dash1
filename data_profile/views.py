import hashlib
import pandas as pd
from django.shortcuts import render, redirect
from django.views import View
from dashboards.forms import UploadFileForm
from dashboards.models import Dataset
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from dashboards.models import Activity, Profile  # Import the Activity and Profile models
import logging

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class DataProfileView(View):

    def get(self, request):
        """
        Displays the form for uploading a file or selecting an existing dataset.
        """
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm(user=request.user)
        return render(request, 'data_profile.html', {'form': form})

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
                    return render(request, 'data_profile.html', {'form': form})

                # Save the new dataset
                dataset = Dataset(user=request.user, name=file.name, file=file, file_hash=file_hash)
                dataset.save()
                logger.info(f"New dataset saved with ID: {dataset.id}")
                Activity.objects.create(user=request.user, activity_type='File Uploaded', dataset=dataset, uploaded_file=None)

            elif existing_dataset:
                dataset = existing_dataset
                logger.info(f"Using existing dataset with ID: {dataset.id}")
                Activity.objects.create(user=request.user, activity_type='Existing Dataset Selected', dataset=dataset, uploaded_file=None)
            else:
                form.add_error(None, 'You must either upload a new dataset or select an existing one.')
                return render(request, 'data_profile.html', {'form': form})

            try:
                # Attempt to read the dataset with different encodings
                data = self.read_csv_with_encodings(dataset.file.path)
                logger.info(f"Data read from dataset:\n{data.head()}")
                profile_data = self.generate_profile(data)
                
                # Increment service usage count
                if not profile.has_active_subscription():
                    profile.service_usage_count += 1
                    profile.save()

                Activity.objects.create(user=request.user, activity_type='Data Profile Generated', dataset=dataset, uploaded_file=None)
                return render(request, 'data_profile_result.html', {'profile': profile_data})
            except Exception as e:
                form.add_error(None, f'Error reading dataset: {e}')
                Activity.objects.create(user=request.user, activity_type='Read Dataset Failed', dataset=dataset, uploaded_file=None)
                return render(request, 'data_profile.html', {'form': form})

        # Output form errors for debugging
        logger.error(f"Form is not valid. Errors: {form.errors}")
        Activity.objects.create(user=request.user, activity_type='Form Submission Failed', dataset=None, uploaded_file=None)
        return render(request, 'data_profile.html', {'form': form})

    def read_csv_with_encodings(self, file_path):
        """
        Attempts to read a CSV file with multiple encodings.
        """
        encodings = ['utf-8', 'ISO-8859-1', 'latin1']
        for encoding in encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except UnicodeDecodeError:
                continue
        # If all encodings fail, raise an exception
        raise UnicodeDecodeError("Failed to read the CSV file with available encodings.")

    def generate_profile(self, data):
        """
        Generates a profile of the dataset including statistics and data types.
        """
        profile = {
            'num_rows': data.shape[0],
            'num_columns': data.shape[1],
            'shape': data.shape,
            'size': data.size,
            'describe': data.describe().to_html(classes='table table-striped'),
            'head': data.head().to_html(classes='table table-striped'),
            'dimension_fields': list(data.select_dtypes(include=['object']).columns),
            'measure_fields': list(data.select_dtypes(include=['number']).columns),
            'null_values': data.isnull().sum().to_dict(),
        }
        return profile

    def generate_file_hash(self, file):
        """
        Generates a SHA-256 hash of the file content for duplicate checking.
        """
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()
