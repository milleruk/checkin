from django.db import models
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string


from django.contrib.auth.models import AbstractUser

class User(AbstractUser):


    email = models.EmailField(unique=True)
    must_change_password = models.BooleanField(default=False, help_text="Require password change on next login")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    # Removed custom app_label to restore compatibility with AUTH_USER_MODEL

def new_token() -> str:
    return get_random_string(48)


class Site(models.Model):

    name = models.CharField(max_length=120, unique=True)
    address = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    confidentiality_terms = models.TextField(blank=True, default="", help_text="Custom confidentiality terms for this site. Shown on sign-in forms.")
    health_safety_procedures = models.TextField(blank=True, default="", help_text="Health and safety procedures for this site. Shown on sign-in forms.")

    def __str__(self) -> str:
        return self.name


# Token types for different portal/QR views
SITE_TOKEN_TYPE_CHOICES = [
    ("public", "Public Portal"),
    ("staff", "Staff Management"),
    ("keypad", "Staff Keypad Sign-In"),
    ("fire", "Fire Roll Call"),
]

class SiteToken(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="tokens")
    token = models.CharField(max_length=80, unique=True)
    type = models.CharField(max_length=16, choices=SITE_TOKEN_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("site", "type")

    def __str__(self):
        return f"{self.site.name} - {self.get_type_display()}"

class SiteManager(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="manager_links")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="site_links")
    pin = models.CharField(max_length=12, blank=True, null=True, help_text="Optional PIN for site manager actions")

    class Meta:
        unique_together = ("site", "user")

    def __str__(self) -> str:
        return f"{self.user} -> {self.site}"

