from django import forms

from . models import whatsapp,Film, Emailbenchsales, Emailleadoppurtunities, Emailsample, Customleads, CustomizeEmailLeads, CustomizeBenchsalesLeads, Customemailleads, Custombenchsales
# import django_filters

class WhatsappForm(forms.ModelForm):
    class Meta:
        model = whatsapp
        fields = ('chat',)

class CustomizeEmailLeadsForm(forms.ModelForm):
    class Meta:
        model = CustomizeEmailLeads
        fields = ('Fileupload',)

class CustomizeBenchsalesLeadsForm(forms.ModelForm):
    class Meta:
        model = CustomizeBenchsalesLeads
        fields = ('BenchsalesFile',)

class FilmForm(forms.ModelForm):
    class Meta:
        model=Film
        fields="__all__"


# class EmailleadForm(forms.ModelForm):
#     class Meta:
#         model=Emaillead
#         fields="__all__"

class EmailbenchsalesForm(forms.ModelForm):
    class Meta:
        model=Emailbenchsales
        fields="__all__"

class CustomleadsForm(forms.ModelForm):
    class Meta:
        model=Customleads
        fields="__all__"


class EmailleadoppurtunitiesForm(forms.ModelForm):
    class Meta:
        model=Emailleadoppurtunities
        fields="__all__"

class EmailsampleForm(forms.ModelForm):
    class Meta:
        model=Emailsample
        fields="__all__"


class LocationChoiceField(forms.Form):

    locations = forms.ModelChoiceField(
        queryset=Film.objects.values_list("checkstatus", flat=True).distinct(),
        #empty_label=None
    )


class LabelChoiceField(forms.Form):

    label = forms.ModelChoiceField(
        queryset=Film.objects.values_list("dropdownlist", flat=True).distinct(),
        #empty_label=None
    )


class DateChoiceField(forms.Form):

    datesdata = forms.ModelChoiceField(
        queryset=Film.objects.values_list("title", flat=True).distinct(),
        #empty_label=None
    )

class UploadFileForm(forms.ModelForm):
    OPTION_CHOICES = (
        ('whatsapp', 'Whatsapp'),
        # ('email leads', 'Email Leads'),
        # ('email benchsales', 'Email Benchsales'),
        ('email opportunities', 'Email Opportunities'),
    )
    option = forms.ChoiceField(choices=OPTION_CHOICES)

    class Meta:
        model = whatsapp
        fields = ('option', 'chat')
        # fields = "__all__"

# class EventFilterForm(forms.Form):
#     # date = forms.DateField()

#     def filter_events(self):
#         filtered_date = self.cleaned_data['title']
#         events = Film.objects.filter(date=filtered_date)
#         return events

class CustomemailleadsForm(forms.ModelForm):
    class Meta:
        model=Customemailleads
        fields="__all__"


class CustombenchsalesForm(forms.ModelForm):
    class Meta:
        model=Custombenchsales
        fields="__all__"