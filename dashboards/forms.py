from django import forms
from .models import UploadedFile, Dataset




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
















class URLForm(forms.Form):
    url = forms.URLField(label='Enter the URL to scrape')





# forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
