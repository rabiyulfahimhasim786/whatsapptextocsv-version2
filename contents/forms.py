from django import forms

from . models import Customwebcontent, blogbenchsales
# import django_filters

class CustomwebcontentForm(forms.ModelForm):
    class Meta:
        model = Customwebcontent
        fields = '__all__'

class blogbenchsalesForm(forms.ModelForm):
    class Meta:
        model=blogbenchsales
        fields="__all__"