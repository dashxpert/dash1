# pivot_service/forms.py


from django import forms
from dashboards.models import Dataset

class FileUploadForm(forms.ModelForm):
    data_file = forms.FileField(required=False, label="Upload CSV File")
    existing_dataset = forms.ModelChoiceField(queryset=Dataset.objects.none(), required=False, label="Select Existing Dataset")

    class Meta:
        model = Dataset
        fields = ['data_file', 'existing_dataset']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['existing_dataset'].queryset = Dataset.objects.filter(user=user)
            self.fields['existing_dataset'].label_from_instance = lambda obj: obj.name


class PivotTableForm(forms.Form):
    rows = forms.ChoiceField(label='Rows', required=False)
    columns = forms.ChoiceField(label='Columns', required=False)
    values = forms.ChoiceField(label='Values')
    aggregation = forms.ChoiceField(
        label='Aggregation Function',
        choices=[('sum', 'Sum'),  ('count', 'count'),  ('min', 'Min'), ('max', 'Max'), ('avg', 'Average'), ('mul', 'Multiply'), ('div', 'Divide')]
    )

    def __init__(self, *args, **kwargs):
        column_choices = kwargs.pop('column_choices', [])
        super().__init__(*args, **kwargs)
        column_choices.insert(0, ('None', 'None'))
        self.fields['rows'].choices = column_choices
        self.fields['columns'].choices = column_choices
        self.fields['values'].choices = column_choices
