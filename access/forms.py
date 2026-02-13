
from django import forms
from django.contrib.auth import password_validation

# ...existing code...

class SiteManagerProfileForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True, label="First name")
    last_name = forms.CharField(max_length=30, required=True, label="Last name")
    email = forms.EmailField(required=True, label="Email")
    password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput,
        required=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput,
        required=False,
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email

    def clean_email(self):
        email = self.cleaned_data['email']
        if email != self.user.email and type(self.user)._default_manager.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 or password2:
            if password1 != password2:
                self.add_error('password2', "Passwords do not match.")
            else:
                password_validation.validate_password(password1, self.user)
        return cleaned_data

    def save(self):
        user = self.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if self.cleaned_data['password1']:
            user.set_password(self.cleaned_data['password1'])
        user.save()
        return user
from django import forms
from .models import AssociatedStaff


class AssociatedStaffSignInForm(forms.ModelForm):
    confidentiality_signed = forms.BooleanField(required=True, label="I agree to the confidentiality terms.")

    class Meta:
        model = AssociatedStaff
        fields = ["name", "association_type", "work_description", "confidentiality_signed"]

    def __init__(self, *args, **kwargs):
        self._site = kwargs.pop("site", None)
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"placeholder": "Full name", "class": "form-control"})
        self.fields["association_type"].widget.attrs.update({"class": "form-control"})
        self.fields["work_description"].widget.attrs.update({"placeholder": "Work description (optional)", "class": "form-control"})
        self.fields["confidentiality_signed"].widget.attrs.update({"class": "form-check-input"})

        from crispy_forms.helper import FormHelper
        from crispy_forms.layout import Layout, Row, Column
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('association_type', css_class='form-group col-md-6 mb-0'),
            ),
            'work_description',
            'confidentiality_signed',
        )

    def save(self, commit=True, site=None):
        instance = super().save(commit=False)
        if site is not None:
            instance.site = site
        instance.is_active = True
        if commit:
            instance.save()
        return instance


from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import Visitor, Contractor


class VisitorSignInForm(forms.ModelForm):
    confidentiality_signed = forms.BooleanField(required=True, label="I agree to the confidentiality terms.")

    class Meta:
        model = Visitor
        fields = ["name", "company", "reason", "confidentiality_signed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('company', css_class='form-group col-md-6 mb-0'),
            ),
            'reason',
            'confidentiality_signed',
        )


class ContractorSignInForm(forms.ModelForm):
    confidentiality_signed = forms.BooleanField(required=True, label="I agree to the confidentiality terms.")

    class Meta:
        model = Contractor
        fields = ["name", "company", "work_description", "confidentiality_signed"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('company', css_class='form-group col-md-6 mb-0'),
            ),
            'work_description',
            'confidentiality_signed',
        )
from django import forms
class StaffRenameForm(forms.Form):
    name = forms.CharField(max_length=160, required=True)


    def __init__(self, *args, site=None, staff=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._site = site
        self._staff = staff
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout('name')

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        qs = StaffMember.objects.filter(site=self._site, name=name)
        if self._staff:
            qs = qs.exclude(id=self._staff.id)
        if self._site and qs.exists():
            raise forms.ValidationError("That name is already in use for this site.")
        return name
from django import forms
from .models import StaffMember


import random

class StaffCreateForm(forms.ModelForm):
    pin = forms.CharField(max_length=6, min_length=6, required=True)

    class Meta:
        model = StaffMember
        fields = ["name", "is_active", "pin"]

    def __init__(self, *args, site=None, **kwargs):
        # If not POST, prefill pin with a unique random 6-digit PIN for this site
        if not kwargs.get('data') and site:
            pin = self._generate_unique_pin(site)
            initial = kwargs.get('initial', {})
            initial['pin'] = pin
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        self._site = site
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('pin', css_class='form-group col-md-6 mb-0'),
            ),
            'is_active',
        )

    def _generate_unique_pin(self, site):
        from .models import StaffMember
        tries = 0
        while tries < 1000:
            pin = f"{random.randint(0, 999999):06d}"
            if not StaffMember.objects.filter(site=site, pin_value=pin).exists():
                return pin
            tries += 1
        raise Exception("Could not generate unique PIN after 1000 tries")


    def clean_pin(self):
        pin = self.cleaned_data["pin"]
        if not pin.isdigit() or len(pin) != 6:
            raise forms.ValidationError("PIN must be exactly 6 digits.")
        if self._site and StaffMember.objects.filter(site=self._site, pin_value=pin).exists():
            raise forms.ValidationError("That PIN is already in use for this site.")
        return pin

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        if self._site and name:
            qs = StaffMember.objects.filter(site=self._site, name=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("name", "A staff member with this name already exists for this site.")
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.set_pin(self.cleaned_data["pin"])
        if commit:
            obj.save()
        return obj



class StaffPinResetForm(forms.Form):
    pin = forms.CharField(max_length=6, min_length=6, required=True)
    random_pin = forms.BooleanField(required=False, label="Generate random PIN")

    def __init__(self, *args, site=None, staff=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._site = site
        self._staff = staff
        # If not POST, prefill pin with a unique random 6-digit PIN for this site
        if not kwargs.get('data') and site:
            self.fields['pin'].initial = self._generate_unique_pin(site, staff)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('pin', css_class='form-group col-md-6 mb-0'),
                Column('random_pin', css_class='form-group col-md-6 mb-0'),
            ),
        )

    def _generate_unique_pin(self, site, staff=None):
        from .models import StaffMember
        tries = 0
        while tries < 1000:
            pin = f"{random.randint(0, 999999):06d}"
            qs = StaffMember.objects.filter(site=site, pin_value=pin)
            if staff:
                qs = qs.exclude(id=staff.id)
            if not qs.exists():
                return pin
            tries += 1
        raise Exception("Could not generate unique PIN after 1000 tries")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('random_pin') and self._site:
            cleaned['pin'] = self._generate_unique_pin(self._site, self._staff)
            self.cleaned_data['pin'] = cleaned['pin']
        return cleaned

    def clean_pin(self):
        pin = self.cleaned_data["pin"]
        if not pin.isdigit() or len(pin) != 6:
            raise forms.ValidationError("PIN must be exactly 6 digits.")
        qs = StaffMember.objects.filter(site=self._site, pin_value=pin)
        if self._staff:
            qs = qs.exclude(id=self._staff.id)
        if self._site and qs.exists():
            raise forms.ValidationError("That PIN is already in use for this site.")
        return pin

