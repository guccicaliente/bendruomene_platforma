from django import forms
from django.contrib.auth.models import User
from .models import (
    Resident, Notification, Document, Maintenance,
    MaintenanceImage, VotingTopic, Complaint, Apartment,
    UserProfile
)

class ResidentRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(label='Vardas')
    last_name = forms.CharField(label='Pavardė')
    email = forms.EmailField(label='El. paštas')
    username = forms.CharField(label='Vartotojo vardas')
    password = forms.CharField(widget=forms.PasswordInput(), label='Slaptažodis')
    apartment_number = forms.CharField(label='Buto numeris')
    is_owner = forms.BooleanField(label='Savininkas', required=False)
    phone = forms.CharField(label='Telefono numeris')
    birth_date = forms.DateField(
        label='Gimimo data',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Resident
        fields = ['first_name', 'last_name', 'email', 'username', 'password', 'apartment_number', 'is_owner', 'phone', 'birth_date']
        labels = {
            'first_name': 'Vardas',
            'last_name': 'Pavardė',
            'email': 'El. paštas',
            'username': 'Vartotojo vardas',
            'password': 'Slaptažodis',
            'apartment_number': 'Buto numeris',
            'is_owner': 'Savininkas',
            'phone': 'Telefono numeris',
            'birth_date': 'Gimimo data',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        username = cleaned_data.get("username")

        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("Toks vartotojo vardas jau egzistuoja")

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'document_type', 'file', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'form-control'})
        }

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'title': 'Pavadinimas',
            'content': 'Turinys'
        }

class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = Maintenance
        fields = ['title', 'description', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'title': 'Pavadinimas',
            'description': 'Aprašymas',
            'start_date': 'Pradžios data',
            'end_date': 'Pabaigos data',
        }

class VotingTopicForm(forms.ModelForm):
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'YYYY-MM-DD'
            }
        ),
        input_formats=['%Y-%m-%d'],
        label='Pabaigos data'
    )

    class Meta:
        model = VotingTopic
        fields = ['title', 'description', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'title': 'Pavadinimas',
            'description': 'Aprašymas'
        }

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.apartment = kwargs.pop('apartment', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.apartment and not Complaint.can_create_complaint(self.apartment):
            raise forms.ValidationError(
                "Jūsų butas jau pateikė maksimalų leistiną skundų skaičių šį mėnesį (2)."
            )
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(label='Vardas')
    last_name = forms.CharField(label='Pavardė')
    email = forms.EmailField(label='El. paštas')
    phone = forms.CharField(label='Telefono numeris')
    birth_date = forms.DateField(
        label='Gimimo data',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = UserProfile
        fields = ['birth_date', 'phone']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()

            try:
                resident = user.resident
                resident.phone = self.cleaned_data['phone']
                resident.birth_date = self.cleaned_data['birth_date']
                resident.save()
            except Resident.DoesNotExist:
                pass
        return profile 