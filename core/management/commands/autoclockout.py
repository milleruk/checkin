from django.core.management.base import BaseCommand
from django.utils import timezone
from access.models import StaffMember, AccessEvent
from core.models import Site

class Command(BaseCommand):
    help = "Auto clock-out staff still clocked in when this command runs."

    def handle(self, *args, **options):
        cutoff = timezone.now()
        total = 0

        for site in Site.objects.filter(is_active=True):
            for staff in StaffMember.objects.filter(site=site, is_active=True):

                last_event = (
                    AccessEvent.objects
                    .filter(site=site, staff=staff, occurred_at__lte=cutoff)
                    .order_by("-occurred_at", "-id")
                    .first()
                )

                if not last_event or last_event.direction != AccessEvent.IN:
                    continue

                # idempotent: don't create another OUT if one already exists after their last IN
                already_out = AccessEvent.objects.filter(
                    site=site,
                    staff=staff,
                    direction=AccessEvent.OUT,
                    occurred_at__gt=last_event.occurred_at,
                ).exists()
                if already_out:
                    continue

                AccessEvent.objects.create(
                    site=site,
                    staff=staff,
                    direction=AccessEvent.OUT,
                    occurred_at=cutoff,
                    auto_clockout=True,
                )
                total += 1
                self.stdout.write(f"Auto clocked out {staff.name} at {site.name}")

        self.stdout.write(self.style.SUCCESS(f"Auto clock-out complete. ({total} staff)"))

