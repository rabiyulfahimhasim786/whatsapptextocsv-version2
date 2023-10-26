from django import forms
from .models import Resume, candidateprofile, candidateobjective, candidateprofessional, candidateeducation, candidateskill, candidateexperience, candidatereference, candidatecertificate, candidatereparser, candidateaward, candidatehobbies 

class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ('file',)

class candidateprofileForm(forms.ModelForm):
    class Meta:
        model=candidateprofile
        fields="__all__"

class candidateobjectiveForm(forms.ModelForm):
    class Meta:
        model=candidateobjective
        fields="__all__"

class candidateprofessionalForm(forms.ModelForm):
    class Meta:
        model=candidateprofessional
        fields="__all__"

class candidateeducationForm(forms.ModelForm):
    class Meta:
        model=candidateeducation
        fields="__all__"

class candidateskillForm(forms.ModelForm):
    class Meta:
        model=candidateskill
        fields="__all__"

class candidateexperienceForm(forms.ModelForm):
    class Meta:
        model=candidateexperience
        fields="__all__"

class candidatereferenceForm(forms.ModelForm):
    class Meta:
        model=candidatereference
        fields="__all__"

class candidatecertificateForm(forms.ModelForm):
    class Meta:
        model=candidatecertificate
        fields="__all__"


class candidateawardForm(forms.ModelForm):
    class Meta:
        model=candidateaward
        fields="__all__"


class candidatehobbiesForm(forms.ModelForm):
    class Meta:
        model=candidatehobbies
        fields="__all__"