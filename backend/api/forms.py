from django import forms
from django.contrib.auth import get_user_model

from core.models import DriverProfile, UserProfile, Vehicle, VehicleModelCatalog


class RegistrationForm(forms.Form):
    company_name = forms.CharField(label='Kompaniya nomi', max_length=180)
    tin = forms.CharField(label='STIR', max_length=30, required=False)
    full_name = forms.CharField(label='Direktor F.I.Sh.', max_length=180)
    phone = forms.CharField(label='Telefon', max_length=40)
    email = forms.EmailField(label='Email')
    username = forms.CharField(label='Login', max_length=150)
    password1 = forms.CharField(label='Parol', min_length=8, widget=forms.PasswordInput)
    password2 = forms.CharField(label='Parolni tasdiqlang', widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if get_user_model().objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Bu login band.')
        return username.lower()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            self.add_error('password2', 'Parollar bir xil emas.')
        return cleaned


class DriverCreateForm(forms.Form):
    username = forms.CharField(label='Login', max_length=150)
    full_name = forms.CharField(label='F.I.Sh.', max_length=180)
    phone = forms.CharField(label='Telefon', max_length=40, required=False)
    password1 = forms.CharField(label='Parol', min_length=8, widget=forms.PasswordInput)
    password2 = forms.CharField(label='Parolni tasdiqlang', widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if get_user_model().objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Bu login band.')
        return username.lower()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            self.add_error('password2', 'Parollar bir xil emas.')
        return cleaned


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'input')


class VehicleForm(StyledModelForm):
    driver = forms.ModelChoiceField(queryset=DriverProfile.objects.none(), label='Haydovchi', required=True)
    model_catalog = forms.ModelChoiceField(queryset=VehicleModelCatalog.objects.none(), label='Model', required=True)

    class Meta:
        model = Vehicle
        fields = ['number', 'model_catalog', 'tonnage', 'current_mileage', 'avg_daily_km', 'image', 'start_date', 'active', 'note']

    def __init__(self, company, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        self.fields['tonnage'].required = False
        self.fields['driver'].queryset = DriverProfile.objects.filter(company=company, active=True).select_related('vehicle')
        self.fields['model_catalog'].queryset = VehicleModelCatalog.objects.filter(company=company, active=True)
        if self.instance and self.instance.pk:
            self.fields['model_catalog'].initial = self.instance.model_catalog_id
            self.fields['driver'].initial = getattr(self.instance, 'driver_id', None)

    def clean_driver(self):
        driver = self.cleaned_data['driver']
        if driver.company_id != self.company.id:
            raise forms.ValidationError('Haydovchi shu kompaniyaga tegishli bo‘lishi kerak.')
        if driver.vehicle_id and driver.vehicle_id != self.instance.pk:
            raise forms.ValidationError('Bu haydovchiga boshqa avtomobil biriktirilgan.')
        return driver

    def save(self, commit=True):
        obj = super().save(commit=False)
        catalog = self.cleaned_data['model_catalog']
        driver = self.cleaned_data['driver']
        obj.model_catalog = catalog
        obj.model = catalog.name
        obj.tonnage = catalog.tonnage
        if commit:
            obj.save()
            driver.vehicle = obj
            driver.save(update_fields=['vehicle'])
        return obj
