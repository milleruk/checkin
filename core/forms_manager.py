from django import forms
from django.contrib.auth import get_user_model
from core.models import Site, SiteManager, SiteToken, SITE_TOKEN_TYPE_CHOICES, new_token

User = get_user_model()

class ManagerInviteForm(forms.Form):
    email = forms.EmailField(label="Manager Email", max_length=255)
    site = forms.ModelChoiceField(queryset=Site.objects.filter(is_active=True))
    password = forms.CharField(label="Password", max_length=128, required=False, widget=forms.TextInput(attrs={"autocomplete": "new-password"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        return email

    def save(self):
        import secrets
        email = self.cleaned_data["email"].strip().lower()
        site = self.cleaned_data["site"]
        password = self.cleaned_data.get("password")
        if not password:
            # Generate a random password if not provided
            password = secrets.token_urlsafe(12)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "is_active": True,
                "is_staff": True,
            }
        )
        if created or not user.has_usable_password():
            user.set_password(password)
            user.save(update_fields=["password"])
        SiteManager.objects.get_or_create(site=site, user=user)
        return user, created

class TokenRotateForm(forms.Form):
    token_type = forms.ChoiceField(choices=SITE_TOKEN_TYPE_CHOICES, label="Token Type")
    confirm = forms.CharField(label="Confirm rotation", max_length=10, required=True)

    def clean_confirm(self):
        value = self.cleaned_data.get('confirm')
        # Accept 'on', True, or 'true' as valid confirmations
        if value in [True, 'on', 'true', 'True', 1, '1']:
            return True
        raise forms.ValidationError('You must confirm rotation.')

    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('site', None)
        super().__init__(*args, **kwargs)

    def save(self):
        token_type = self.cleaned_data['token_type']
        site = self.site
        token_obj = SiteToken.objects.get(site=site, type=token_type)
        token_obj.token = new_token()
        token_obj.save()
        return token_obj

class MultiTokenRotateForm(forms.Form):
    token_types = forms.MultipleChoiceField(choices=SITE_TOKEN_TYPE_CHOICES, label="Tokens to rotate", required=True, widget=forms.CheckboxSelectMultiple)
    confirm = forms.BooleanField(label="Confirm rotation", required=True)

    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('site', None)
        super().__init__(*args, **kwargs)

    def clean_confirm(self):
        value = self.cleaned_data.get('confirm')
        if value in [True, 'on', 'true', 'True', 1, '1']:
            return True
        raise forms.ValidationError('You must confirm rotation.')

    def save(self):
        site = self.site
        rotated = []
        for token_type in self.cleaned_data['token_types']:
            token_obj = SiteToken.objects.get(site=site, type=token_type)
            token_obj.token = new_token()
            token_obj.save()
            rotated.append(token_obj)
        return rotated
