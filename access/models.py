from core.models import Site
from django.db import models
class AssociatedStaff(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="associated_staff")
    name = models.CharField(max_length=160)
    ASSOCIATION_TYPE_CHOICES = [
        ("locum", "Locum"),
        ("trainee", "Trainee"),
        ("pcn", "PCN"),
    ]
    association_type = models.CharField(max_length=32, choices=ASSOCIATION_TYPE_CHOICES, blank=True, default="pcn")
    work_description = models.CharField(max_length=255, blank=True, default="")
    confidentiality_signed = models.BooleanField(default=False)
    signed_in_at = models.DateTimeField(null=True, blank=True)
    signed_out_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    checkout_token = models.CharField(max_length=64, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.name} (Associate at {self.site})"
from core.models import Site
from django.db import models
class Visitor(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="visitors")
    name = models.CharField(max_length=160)
    company = models.CharField(max_length=160, blank=True, default="")
    reason = models.CharField(max_length=255, blank=True, default="")
    confidentiality_signed = models.BooleanField(default=False)
    signed_in_at = models.DateTimeField(null=True, blank=True)
    signed_out_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


    checkout_token = models.CharField(max_length=64, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.name} (Visitor at {self.site})"

class Contractor(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="contractors")
    name = models.CharField(max_length=160)
    company = models.CharField(max_length=160, blank=True, default="")
    work_description = models.CharField(max_length=255, blank=True, default="")
    confidentiality_signed = models.BooleanField(default=False)
    signed_in_at = models.DateTimeField(null=True, blank=True)
    signed_out_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    checkout_token = models.CharField(max_length=64, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.name} (Contractor at {self.site})"
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from core.models import Site

class StaffMember(models.Model):
    checkout_token = models.CharField(max_length=64, blank=True, null=True, unique=True)
    ASSOCIATION_TYPE_CHOICES = [
        ("locum", "Locum"),
        ("trainee", "Trainee"),
        ("other", "Other"),
    ]
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="staff")
    name = models.CharField(max_length=160)

    # used for authentication
    pin_hash = models.CharField(max_length=256)

    # shown to site admins/managers in UI
    pin_value = models.CharField(max_length=6)

    is_active = models.BooleanField(default=True)
    is_associated = models.BooleanField(default=False, help_text="Flag for associated staff (no PIN required)")
    association_type = models.CharField(max_length=32, choices=ASSOCIATION_TYPE_CHOICES, blank=True, default="other")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["site", "name"], name="uniq_staff_name_per_site"),
            models.UniqueConstraint(fields=["site", "pin_value"], name="uniq_pin_per_site"),
        ]
        indexes = [
            models.Index(fields=["site", "name"]),
            models.Index(fields=["site", "pin_value"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.site})"

    def set_pin(self, pin: str):
        self.pin_value = pin
        self.pin_hash = make_password(pin)

    def check_pin(self, pin: str) -> bool:
        return check_password(pin, self.pin_hash)

class AccessEvent(models.Model):
    IN = "IN"
    OUT = "OUT"
    DIRECTION_CHOICES = [(IN, "In"), (OUT, "Out")]

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="events")
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name="events", null=True, blank=True)
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    occurred_at = models.DateTimeField(auto_now_add=True)
    auto_clockout = models.BooleanField(default=False, help_text="True if this event was an automatic clock-out at 23:00 GMT.")

    class Meta:
        indexes = [
            models.Index(fields=["site", "-occurred_at"]),
            models.Index(fields=["staff", "-occurred_at"]),
        ]
        ordering = ["-occurred_at"]
