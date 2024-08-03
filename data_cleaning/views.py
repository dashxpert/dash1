import hashlib
import pandas as pd
from io import StringIO
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import DataCleaningForm, ExtractForm,ChangeDataTypeForm, UploadFileForm, ConcatenationForm, DataCleaningForm, RemoveNullForm, ReplaceBlankForm, FillNAForm, DropNAForm, ConcatenationForm,RemoveDuplicatesForm,FindReplaceForm

from dashboards.models import Dataset
from django.http import HttpResponse
import logging



import hashlib
import pandas as pd
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from dashboards.forms import UploadFileForm
from dashboards.models import Dataset
from dashboards.models import Activity, Profile  # Import the Activity and Profile models
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
        return render(request, 'upload_file.html', {'form': form})

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
                    return render(request, 'upload_file.html', {'form': form})

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
                return render(request, 'upload_file.html', {'form': form})

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

                Activity.objects.create(user=request.user, activity_type='Data Cleaning', dataset=dataset, uploaded_file=None)
                return redirect('data_cleaning_options')
            except Exception as e:
                logger.error("Error reading dataset: %s", e)
                form.add_error(None, f'Error reading dataset: {e}')
                Activity.objects.create(user=request.user, activity_type='Read Dataset Failed', dataset=dataset, uploaded_file=None)
                return render(request, 'upload_file.html', {'form': form})

        logger.warning("Form is not valid. Errors: %s", form.errors)
        Activity.objects.create(user=request.user, activity_type='Form Submission Failed', dataset=None, uploaded_file=None)
        return render(request, 'upload_file.html', {'form': form})

    def generate_file_hash(self, file):
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()



@method_decorator(login_required, name='dispatch')
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



@method_decorator(login_required, name='dispatch')
class ConcatenationView(View):
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

        form = ConcatenationForm()
        string_columns = [(col, col) for col in data.select_dtypes(include=['object']).columns]
        form.fields['concatenation_col1'].choices = string_columns
        form.fields['concatenation_col2'].choices = string_columns

        return render(request, 'concatenation.html', {'form': form})

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

        form = ConcatenationForm(request.POST)
        string_columns = [(col, col) for col in data.select_dtypes(include=['object']).columns]
        form.fields['concatenation_col1'].choices = string_columns
        form.fields['concatenation_col2'].choices = string_columns

        if form.is_valid():
            try:
                concat_col1 = form.cleaned_data['concatenation_col1']
                concat_col2 = form.cleaned_data['concatenation_col2']

                if concat_col1 and concat_col2:
                    data['concat'] = data[concat_col1].astype(str) + data[concat_col2].astype(str)

                cleaned_file = data.to_csv(index=False)
                request.session['cleaned_data'] = cleaned_file
                return redirect('data_cleaning')
            except Exception as e:
                logger.error("Error processing data cleaning: %s", e)
                form.add_error(None, 'Error processing the data. Please try again.')

        return render(request, 'concatenation.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class DropNAView(View):
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

        form = DropNAForm()
        all_columns = [(col, col) for col in data.columns]
        form.fields['drop_na'].choices = all_columns

        return render(request, 'drop_na.html', {'form': form})

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

        form = DropNAForm(request.POST)
        all_columns = [(col, col) for col in data.columns]
        form.fields['drop_na'].choices = all_columns

        if form.is_valid():
            try:
                drop_na_cols = form.cleaned_data['drop_na']
                data.dropna(subset=drop_na_cols, inplace=True)

                cleaned_file = data.to_csv(index=False)
                request.session['cleaned_data'] = cleaned_file
                return redirect('data_cleaning')
            except Exception as e:
                logger.error("Error processing data cleaning: %s", e)
                form.add_error(None, 'Error processing the data. Please try again.')

        return render(request, 'drop_na.html', {'form': form})


from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
import pandas as pd
from io import StringIO
import logging

from .forms import FillNAForm

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class FillNAView(View):
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

        form = FillNAForm()
        all_columns = [(col, col) for col in data.columns]
        form.fields['fill_na_col'].choices = all_columns

        return render(request, 'fill_na.html', {'form': form})

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

        form = FillNAForm(request.POST)
        all_columns = [(col, col) for col in data.columns]
        form.fields['fill_na_col'].choices = all_columns

        if form.is_valid():
            try:
                fill_na_cols = form.cleaned_data['fill_na_col']
                fill_na_value = form.cleaned_data['fill_na_value']

                # Fill NaN values in selected columns
                for col in fill_na_cols:
                    data[col].fillna(fill_na_value, inplace=True)

                cleaned_file = data.to_csv(index=False)
                request.session['cleaned_data'] = cleaned_file
                return redirect('data_cleaning')
            except Exception as e:
                logger.error("Error processing data cleaning: %s", e)
                form.add_error(None, 'Error processing the data. Please try again.')

        return render(request, 'fill_na.html', {'form': form})

from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
import pandas as pd
from io import StringIO
import logging

from .forms import ReplaceBlankForm

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class ReplaceBlankView(View):
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

        form = ReplaceBlankForm()
        all_columns = [(col, col) for col in data.columns]
        form.fields['replace_blank'].choices = all_columns

        return render(request, 'replace_blank.html', {'form': form})

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

        form = ReplaceBlankForm(request.POST)
        all_columns = [(col, col) for col in data.columns]
        form.fields['replace_blank'].choices = all_columns

        if form.is_valid():
            try:
                replace_blank_cols = form.cleaned_data['replace_blank']
                for col in replace_blank_cols:
                    data[col] = data[col].replace('', '0').replace(' ', '0').fillna('0')

                cleaned_file = data.to_csv(index=False)
                request.session['cleaned_data'] = cleaned_file
                return redirect('data_cleaning')
            except Exception as e:
                logger.error("Error processing data cleaning: %s", e)
                form.add_error(None, 'Error processing the data. Please try again.')

        return render(request, 'replace_blank.html', {'form': form})



@method_decorator(login_required, name='dispatch')
class RemoveNullView(View):
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

        form = RemoveNullForm()
        all_columns = [(col, col) for col in data.columns]
        form.fields['remove_null'].choices = all_columns

        return render(request, 'remove_null.html', {'form': form})

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

        form = RemoveNullForm(request.POST)
        all_columns = [(col, col) for col in data.columns]
        form.fields['remove_null'].choices = all_columns

        if form.is_valid():
            try:
                remove_null_cols = form.cleaned_data['remove_null']
                data.dropna(subset=remove_null_cols, inplace=True)

                cleaned_file = data.to_csv(index=False)
                request.session['cleaned_data'] = cleaned_file
                return redirect('data_cleaning')
            except Exception as e:
                logger.error("Error processing data cleaning: %s", e)
                form.add_error(None, 'Error processing the data. Please try again.')

        return render(request, 'remove_null.html', {'form': form})



@method_decorator(login_required, name='dispatch')
class RemoveDuplicatesView(View):
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

        form = RemoveDuplicatesForm()
        all_columns = [(col, col) for col in data.columns]
        form.fields['remove_duplicates_cols'].choices = all_columns

        return render(request, 'remove_duplicates.html', {'form': form})

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

        form = RemoveDuplicatesForm(request.POST)
        all_columns = [(col, col) for col in data.columns]
        form.fields['remove_duplicates_cols'].choices = all_columns

        if form.is_valid():
            try:
                remove_duplicates_cols = form.cleaned_data['remove_duplicates_cols']
                data.drop_duplicates(subset=remove_duplicates_cols, inplace=True)

                cleaned_file = data.to_csv(index=False)
                request.session['cleaned_data'] = cleaned_file
                return redirect('data_cleaning')
            except Exception as e:
                logger.error("Error processing data cleaning: %s", e)
                form.add_error(None, 'Error processing the data. Please try again.')

        return render(request, 'remove_duplicates.html', {'form': form})



@method_decorator(login_required, name='dispatch')
class FindReplaceView(View):
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

        form = FindReplaceForm()
        all_columns = [(col, col) for col in data.columns]
        form.fields['column'].choices = all_columns

        return render(request, 'find_replace.html', {'form': form})

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

        form = FindReplaceForm(request.POST)
        all_columns = [(col, col) for col in data.columns]
        form.fields['column'].choices = all_columns

        if form.is_valid():
            try:
                column = form.cleaned_data['column']
                find = form.cleaned_data['find']
                replace = form.cleaned_data['replace']

                # Perform find and replace
                data[column] = data[column].str.replace(find, replace, regex=False)

                cleaned_file = data.to_csv(index=False)
                request.session['cleaned_data'] = cleaned_file
                return redirect('data_cleaning')
            except Exception as e:
                logger.error("Error processing data cleaning: %s", e)
                form.add_error(None, 'Error processing the data. Please try again.')

        return render(request, 'find_replace.html', {'form': form})



from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponse
import pandas as pd
from io import StringIO
import logging

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class ExtractView(View):
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

        form = ExtractForm(columns=data.columns)
        return render(request, 'extract.html', {'form': form})

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

        form = ExtractForm(request.POST, columns=data.columns)
        if form.is_valid():
            try:
                column = form.cleaned_data['column']
                pattern = form.cleaned_data['pattern']

                # Perform extract operation
                extracted_data = data[column].str.extract(pattern, expand=True)

                # Add the extracted columns to the original data
                data = pd.concat([data, extracted_data], axis=1)

                cleaned_file = data.to_csv(index=False)
                request.session['cleaned_data'] = cleaned_file
                return redirect('data_cleaning')
            except Exception as e:
                logger.error("Error processing data extraction: %s", e)
                form.add_error(None, 'Error processing the data. Please try again.')

        return render(request, 'extract.html', {'form': form})
