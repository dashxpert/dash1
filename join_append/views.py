# join_append/views.py

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import ActionForm, JoinForm

import pandas as pd
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import UploadFileForm
from dashboards.models import Dataset
import plotly.express as px
import hashlib
from io import StringIO
import logging
from django.http import HttpResponse


from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import UploadFileForm, ColumnSelectionForm
from dashboards.models import Dataset,Activity, Profile
import pandas as pd
import hashlib
import pandas as pd
from .forms import UploadFileForm


logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class UploadFilesForJoinView(View):
    def get(self, request):
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm(user=request.user)
        return render(request, 'join_append/upload_files_for_join.html', {'form': form})

    def post(self, request):
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            file = form.cleaned_data.get('file')
            existing_dataset = form.cleaned_data.get('existing_dataset')

            if file:
                file_hash = self.generate_file_hash(file)
                if Dataset.objects.filter(file_hash=file_hash, user=request.user).exists():
                    form.add_error('file', 'This dataset has already been uploaded.')
                    Activity.objects.create(user=request.user, activity_type='Upload Failed', dataset=None)
                    return render(request, 'join_append/upload_files_for_join.html', {'form': form})

                dataset = Dataset(user=request.user, name=file.name, file=file, file_hash=file_hash)
                dataset.save()
                Activity.objects.create(user=request.user, activity_type='File Uploaded', dataset=dataset)
            
            elif existing_dataset:
                dataset = existing_dataset
                logger.info("Using existing dataset with ID: %s", dataset.id)
                Activity.objects.create(user=request.user, activity_type='Existing Dataset Selected', dataset=dataset, uploaded_file=None)
            else:
                form.add_error(None, 'You must either upload a new dataset or select an existing one.')
                return render(request, 'join_append/upload_files_for_join.html', {'form': form})

            try:
                data = pd.read_csv(dataset.file.path)
                csv_data = data.to_csv(index=False)
                request.session['csv_data'] = csv_data
                request.session['dataset_id'] = dataset.id
                request.session['columns'] = data.columns.tolist()

                if not profile.has_active_subscription():
                    profile.service_usage_count += 1
                    profile.save()

                Activity.objects.create(user=request.user, activity_type='Table joined', dataset=dataset)
                return redirect('select_second_dataset')
            except Exception as e:
                form.add_error(None, f'Error reading dataset: {e}')
                Activity.objects.create(user=request.user, activity_type='Read Dataset Failed', dataset=dataset)
                return render(request, 'join_append/upload_files_for_join.html', {'form': form})

        Activity.objects.create(user=request.user, activity_type='Form Submission Failed', dataset=None)
        return render(request, 'join_append/upload_files_for_join.html', {'form': form})

    def generate_file_hash(self, file):
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()

@method_decorator(login_required, name='dispatch')
class SelectSecondDatasetView(View):
    def get(self, request):
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm(user=request.user)
        return render(request, 'join_append/select_second_dataset.html', {'form': form})

    def post(self, request):
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            file = form.cleaned_data.get('file')
            existing_dataset = form.cleaned_data.get('existing_dataset')

            if file:
                file_hash = self.generate_file_hash(file)
                if Dataset.objects.filter(file_hash=file_hash, user=request.user).exists():
                    form.add_error('file', 'This dataset has already been uploaded.')
                    Activity.objects.create(user=request.user, activity_type='Upload Failed', dataset=None)
                    return render(request, 'join_append/select_second_dataset.html', {'form': form})

                dataset = Dataset(user=request.user, name=file.name, file=file, file_hash=file_hash)
                dataset.save()
                Activity.objects.create(user=request.user, activity_type='File Uploaded', dataset=dataset)
            elif existing_dataset:
                dataset = existing_dataset
                Activity.objects.create(user=request.user, activity_type='Existing Dataset Selected', dataset=dataset)
            else:
                form.add_error(None, 'You must either upload a new dataset or select an existing one.')
                return render(request, 'join_append/select_second_dataset.html', {'form': form})

            try:
                data = pd.read_csv(dataset.file.path)
                csv_data = data.to_csv(index=False)
                request.session['csv_data_2'] = csv_data
                request.session['dataset_id_2'] = dataset.id
                request.session['columns_2'] = data.columns.tolist()

                if not profile.has_active_subscription():
                    profile.service_usage_count += 1
                    profile.save()

                Activity.objects.create(user=request.user, activity_type='Data Read', dataset=dataset)
                return redirect('select_columns')
            except Exception as e:
                form.add_error(None, f'Error reading dataset: {e}')
                Activity.objects.create(user=request.user, activity_type='Read Dataset Failed', dataset=dataset)
                return render(request, 'join_append/select_second_dataset.html', {'form': form})

        Activity.objects.create(user=request.user, activity_type='Form Submission Failed', dataset=None)
        return render(request, 'join_append/select_second_dataset.html', {'form': form})

    def generate_file_hash(self, file):
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()



@method_decorator(login_required, name='dispatch')
class SelectColumnsView(View):
    def get(self, request):
        columns_1 = request.session.get('columns', [])
        columns_2 = request.session.get('columns_2', [])
        form = ColumnSelectionForm(columns_1=columns_1, columns_2=columns_2)
        return render(request, 'join_append/select_columns.html', {'form': form})

    def post(self, request):
        columns_1 = request.session.get('columns', [])
        columns_2 = request.session.get('columns_2', [])
        form = ColumnSelectionForm(columns_1=columns_1, columns_2=columns_2, data=request.POST)
        if form.is_valid():
            column_1 = form.cleaned_data.get('column_1')
            column_2 = form.cleaned_data.get('column_2')

            csv_data_1 = request.session.get('csv_data')
            csv_data_2 = request.session.get('csv_data_2')
            df1 = pd.read_csv(StringIO(csv_data_1))
            df2 = pd.read_csv(StringIO(csv_data_2))

            try:
                merged_df = pd.merge(df1, df2, left_on=column_1, right_on=column_2)
                merged_csv = merged_df.to_csv(index=False)
                request.session['merged_csv'] = merged_csv
                return redirect('join_success')
            except Exception as e:
                form.add_error(None, f'Error joining datasets: {e}')
                return render(request, 'join_append/select_columns.html', {'form': form})

        return render(request, 'join_append/select_columns.html', {'form': form})




@method_decorator(login_required, name='dispatch')
class JoinSuccessView(View):
    def get(self, request):
        merged_csv = request.session.get('merged_csv')
        if merged_csv:
            return render(request, 'join_append/join_success.html', {'merged_csv': merged_csv})
        return redirect('upload_files_for_join')

def table_action(request):
    if request.method == 'POST':
        form = ActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data.get('action')
            if action == 'join':
                return redirect('upload_files_for_join')
            elif action == 'append':
                return redirect('upload_files_for_append')
    else:
        form = ActionForm()

    return render(request, 'join_append/table_action.html', {'form': form})


from django.http import HttpResponse
from io import StringIO
import pandas as pd
from .forms import UploadFileForm

def upload_files_for_join(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, files=request.FILES)
        if form.is_valid():
            table1 = request.FILES['table1']
            table2 = request.FILES['table2']
            on_column1 = form.cleaned_data['on_column1']
            on_column2 = form.cleaned_data['on_column2']
            join_type = form.cleaned_data['join_type']

            df1 = pd.read_csv(table1)
            df2 = pd.read_csv(table2)

            joined_df = pd.merge(df1, df2, left_on=on_column1, right_on=on_column2, how=join_type)

            csv_buffer = StringIO()
            joined_df.to_csv(csv_buffer, index=False)
            response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="joined_table.csv"'
            return response
    else:
        form = UploadFileForm()
        if 'table1' in request.FILES and 'table2' in request.FILES:
            table1 = request.FILES['table1']
            table2 = request.FILES['table2']
            df1 = pd.read_csv(table1)
            df2 = pd.read_csv(table2)
            form.set_choices(df1.columns, df2.columns)

    return render(request, 'join_append/upload_files_for_join.html', {'form': form})


from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

@method_decorator(login_required, name='dispatch')
class DownloadJoinedCSVView(View):
    def get(self, request):
        merged_csv = request.session.get('merged_csv', '')
        if merged_csv:
            response = HttpResponse(merged_csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="joined_table.csv"'
            return response
        else:
            return HttpResponse("No data available for download.", status=404)



from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import UploadFileForm2
from dashboards.models import Dataset, Activity, Profile
import pandas as pd
import hashlib
import logging
from io import StringIO
from django.http import HttpResponse

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class UploadFilesForAppendView(View):
    def get(self, request):
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm2(user=request.user)
        return render(request, 'join_append/upload_files_for_append.html', {'form': form})

    def post(self, request):
        profile = request.user.profile
        if not profile.has_active_subscription() and profile.service_usage_count >= 5:
            return redirect('prompt_payment')

        form = UploadFileForm2(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            file1 = form.cleaned_data.get('file1')
            file2 = form.cleaned_data.get('file2')
            existing_dataset1 = form.cleaned_data.get('existing_dataset1')
            existing_dataset2 = form.cleaned_data.get('existing_dataset2')

            df1, df2 = None, None

            if file1:
                df1 = pd.read_csv(file1)
            elif existing_dataset1:
                df1 = pd.read_csv(existing_dataset1.file.path)

            if file2:
                df2 = pd.read_csv(file2)
            elif existing_dataset2:
                df2 = pd.read_csv(existing_dataset2.file.path)

            if df1 is not None and df2 is not None:
                try:
                    appended_df = pd.concat([df1, df2])
                    csv_buffer = StringIO()
                    appended_df.to_csv(csv_buffer, index=False)
                    response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename="appended_table.csv"'

                    if not profile.has_active_subscription():
                        profile.service_usage_count += 1
                        profile.save()

                    Activity.objects.create(user=request.user, activity_type='Tables Appended', dataset=None)
                    return response
                except Exception as e:
                    form.add_error(None, f'Error appending tables: {e}')
                    Activity.objects.create(user=request.user, activity_type='Append Failed', dataset=None)
                    return render(request, 'join_append/upload_files_for_append.html', {'form': form})

            form.add_error(None, 'You must provide both tables (either as new uploads or existing datasets).')
            Activity.objects.create(user=request.user, activity_type='Form Submission Failed', dataset=None)
            return render(request, 'join_append/upload_files_for_append.html', {'form': form})

        Activity.objects.create(user=request.user, activity_type='Form Submission Failed', dataset=None)
        return render(request, 'join_append/upload_files_for_append.html', {'form': form})


