
from django.core.management.base import BaseCommand
from django.utils import timezone
from access.models import AccessEvent, StaffMember
from core.models import Site
from datetime import datetime, time, timedelta
import random

class Command(BaseCommand):
    help = 'Seed 3 months of check-in/out and auto clock-out data for all staff at a given site.'

    def add_arguments(self, parser):
        parser.add_argument('site_id', type=int, help='ID of the site to seed')
        parser.add_argument('--days', type=int, default=90, help='Number of days to seed (default: 90)')

    def handle(self, *args, **options):
        site_id = options['site_id']
        days = options['days']
        try:
            site = Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Site id {site_id} does not exist.'))
            return
        staff_qs = StaffMember.objects.filter(site=site, is_active=True)
        if not staff_qs.exists():
            self.stdout.write(self.style.WARNING(f'No staff found for site {site_id}'))
            return
        tz = timezone.get_current_timezone()
        today = timezone.localdate()
        for staff in staff_qs:
            for day_offset in range(days, 0, -1):
                day = today - timedelta(days=day_offset)
                # Make sure day is a date, and datetimes are timezone-aware
                checkin_hour = random.randint(7, 9)
                checkin_minute = random.randint(0, 59)
                checkin_dt = timezone.make_aware(datetime.combine(day, time(checkin_hour, checkin_minute)), timezone=tz)
                AccessEvent.objects.create(
                    site=site,
                    staff=staff,
                    direction=AccessEvent.IN,
                    occurred_at=checkin_dt,
                    auto_clockout=False
                )
                # 80% chance of manual clock-out, else auto clock-out
                if random.random() < 0.8:
                    checkout_hour = random.randint(16, 18)
                    checkout_minute = random.randint(0, 59)
                    checkout_dt = timezone.make_aware(datetime.combine(day, time(checkout_hour, checkout_minute)), timezone=tz)
                    AccessEvent.objects.create(
                        site=site,
                        staff=staff,
                        direction=AccessEvent.OUT,
                        occurred_at=checkout_dt,
                        auto_clockout=False
                    )
                else:
                    auto_dt = timezone.make_aware(datetime.combine(day, time(23, 0)), timezone=tz)
                    AccessEvent.objects.create(
                        site=site,
                        staff=staff,
                        direction=AccessEvent.OUT,
                        occurred_at=auto_dt,
                        auto_clockout=True
                    )
            self.stdout.write(self.style.SUCCESS(f'Seeded {days} days for staff {staff.name} (id {staff.id}) at site {site.name}'))
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {days} days of data for all staff at site {site.name}'))
