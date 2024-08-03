from django import forms

class DataCleaningForm(forms.Form):
    file = forms.FileField()

class ChangeDataTypeForm(forms.Form):
    data_type = forms.ChoiceField(choices=[('int_to_str', 'Integer to String'), ('str_to_int', 'String to Integer'), ('str_to_date', 'String to Date')])
    data_type_cols = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)



class DataCleaningForm(forms.Form):
    data = forms.ChoiceField(choices=[
        ('change_data_type', 'Change Data Type'),
        ('concatenation', 'Concatenate Columns'),
        ('drop_na', 'Drop NA Values'),
        ('fill_na', 'Fill NA Values'),
        ('remove_duplicates', 'Remove Duplicates'),
        ('replace_blank', 'Replace Blank Values'),
        ('remove_null', 'Remove Null Values'),
        ('Find_and_Replace', 'Find and Replace any'),

    ], required=True)



from django import forms
from dashboards.models import Dataset

class UploadFileForm(forms.ModelForm):
    file = forms.FileField(required=False)  # Adjust according to your needs
    existing_dataset = forms.ModelChoiceField(queryset=Dataset.objects.none(), required=False)

    class Meta:
        model = Dataset
        fields = ['file', 'existing_dataset']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['existing_dataset'].queryset = Dataset.objects.filter(user=user)
            self.fields['existing_dataset'].label_from_instance = lambda obj: obj.name


class ConcatenationForm(forms.Form):
    concatenation_col1 = forms.ChoiceField(choices=[], required=True)
    concatenation_col2 = forms.ChoiceField(choices=[], required=True)

class DropNAForm(forms.Form):
    drop_na = forms.MultipleChoiceField(choices=[], required=True)

class FillNAForm(forms.Form):
    fill_na_col = forms.ChoiceField(choices=[], required=True)
    fill_na_value = forms.CharField(required=True)

class ReplaceBlankForm(forms.Form):
    replace_blank = forms.ChoiceField(choices=[], required=True)

class RemoveNullForm(forms.Form):
    remove_null = forms.ChoiceField(choices=[], required=True)

