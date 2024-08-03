# join_append/forms.py

from django import forms

class ActionForm(forms.Form):
    ACTION_CHOICES = [
        ('join', 'Join'),
        ('append', 'Append'),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES, label='Select Action')


from django import forms

class JoinForm(forms.Form):
    column1 = forms.ChoiceField(label='Select column from first dataset')
    column2 = forms.ChoiceField(label='Select column from second dataset')
    join_type = forms.ChoiceField(
        choices=[
            ('inner', 'Inner Join'),
            ('outer', 'Outer Join'),
            ('left', 'Left Join'),
            ('right', 'Right Join'),
        ],
        label='Select Join Type'
    )

    def set_choices(self, columns1, columns2):
        self.fields['column1'].choices = [(col, col) for col in columns1]
        self.fields['column2'].choices = [(col, col) for col in columns2]
# dashboards/forms.py


# join_append/forms.py


from django import forms
from dashboards.models import Dataset

class UploadFileForm(forms.Form):
    file = forms.FileField(required=False)
    existing_dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.none(), 
        required=False, 
        label="Select Existing Dataset"
    )

    class Meta:
        model = Dataset
        fields = ['file', 'existing_dataset']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.fields['existing_dataset'].queryset = Dataset.objects.filter(user=user).order_by('name')
        self.fields['existing_dataset'].label_from_instance = lambda obj: f"{obj.name} - Uploaded on {obj.upload_date.strftime('%Y-%m-%d %H:%M:%S')}"

    def set_choices(self, columns_1, columns_2):
        self.fields['on_column1'].choices = [(col, col) for col in columns_1]
        self.fields['on_column2'].choices = [(col, col) for col in columns_2]



class ColumnSelectionForm(forms.Form):
    column_1 = forms.ChoiceField(choices=[])
    column_2 = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        columns_1 = kwargs.pop('columns_1', [])
        columns_2 = kwargs.pop('columns_2', [])
        super().__init__(*args, **kwargs)
        self.fields['column_1'].choices = [(col, col) for col in columns_1]
        self.fields['column_2'].choices = [(col, col) for col in columns_2]


from django import forms
from dashboards.models import Dataset

class UploadFileForm2(forms.Form):
    file1 = forms.FileField(required=False)
    file2 = forms.FileField(required=False)
    existing_dataset1 = forms.ModelChoiceField(queryset=Dataset.objects.none(), required=False, label="Existing Dataset 1")
    existing_dataset2 = forms.ModelChoiceField(queryset=Dataset.objects.none(), required=False, label="Existing Dataset 2")

    class Meta:
        model = Dataset
        fields = ['file1', 'file2', 'existing_dataset1', 'existing_dataset2']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(UploadFileForm2, self).__init__(*args, **kwargs)
        self.fields['existing_dataset1'].queryset = Dataset.objects.filter(user=user)
        self.fields['existing_dataset2'].queryset = Dataset.objects.filter(user=user)
        self.fields['existing_dataset1'].label_from_instance = lambda obj: obj.name
        self.fields['existing_dataset2'].label_from_instance = lambda obj: obj.name

 
