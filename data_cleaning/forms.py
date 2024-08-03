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
        ('replace_blank', 'Replace Blank Values with zero'),
        ('remove_null', 'Remove Null Values'),
        ('find_replace', 'Find and Replace any string'),
        ('extract', 'Extract Substring'),  # Ensure this matches the URL pattern   # Ensure this matches the URL pattern
    ])



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


from django import forms

class ConcatenationForm(forms.Form):
    concatenation_col1 = forms.ChoiceField(
        choices=[],  # Populate this with your column choices dynamically
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})  # Add Bootstrap class if using Bootstrap
    )
    concatenation_col2 = forms.ChoiceField(
        choices=[],  # Populate this with your column choices dynamically
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})  # Add Bootstrap class if using Bootstrap
    )


from django import forms

class DropNAForm(forms.Form):
    drop_na = forms.MultipleChoiceField(
        choices=[],  # Populate this with your column choices dynamically
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
from django import forms

class FillNAForm(forms.Form):
    fill_na_col = forms.MultipleChoiceField(
        choices=[],  # Will be populated dynamically in the view
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    fill_na_value = forms.CharField(required=True)


from django import forms

class ReplaceBlankForm(forms.Form):
    replace_blank = forms.MultipleChoiceField(
        choices=[],  # Will be populated dynamically in the view
        widget=forms.CheckboxSelectMultiple,
        required=True
    )


from django import forms

class RemoveNullForm(forms.Form):
    remove_null = forms.MultipleChoiceField(
        choices=[],  # Will be populated dynamically in the view
        widget=forms.CheckboxSelectMultiple,
        required=True
    )



class RemoveDuplicatesForm(forms.Form):
    remove_duplicates_cols = forms.MultipleChoiceField(
        choices=[],  # Populate this with your column choices dynamically
        widget=forms.CheckboxSelectMultiple,
        required=True
    )


# pivot_service/forms.py
from django import forms

class FindReplaceForm(forms.Form):
    column = forms.ChoiceField(label='Column')
    find = forms.CharField(label='Find', max_length=100)
    replace = forms.CharField(label='Replace', max_length=100)

    def __init__(self, *args, **kwargs):
        columns = kwargs.pop('columns', [])
        super().__init__(*args, **kwargs)
        self.fields['column'].choices = [(col, col) for col in columns]

# pivot_service/forms.py
from django import forms

class ExtractForm(forms.Form):
    column = forms.ChoiceField(label='Column')
    pattern = forms.CharField(label='Pattern', max_length=100)

    def __init__(self, *args, **kwargs):
        columns = kwargs.pop('columns', [])
        super().__init__(*args, **kwargs)
        self.fields['column'].choices = [(col, col) for col in columns]
