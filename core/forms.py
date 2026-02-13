
from django import forms
from tinymce.widgets import TinyMCE

from .models import Site
from django.contrib.auth import get_user_model

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ["confidentiality_terms", "health_safety_procedures"]
        widgets = {
            "confidentiality_terms": TinyMCE(attrs={"cols": 80, "rows": 10}),
            "health_safety_procedures": TinyMCE(attrs={"cols": 80, "rows": 10}),
        }

User = get_user_model()

class SiteCreateForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ["name", "address", "is_active"]


class UserCreateForm(forms.ModelForm):

    first_name = forms.CharField(max_length=150, required=False, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "is_superuser", "is_staff", "is_active"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class SiteManagerAssignForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True))
    site = forms.ModelChoiceField(queryset=Site.objects.filter(is_active=True))
