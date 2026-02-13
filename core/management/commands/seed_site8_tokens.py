from django.core.management.base import BaseCommand
from core.models import Site, SiteToken, SITE_TOKEN_TYPE_CHOICES, new_token

class Command(BaseCommand):
    help = 'Seed tokens for site 8.'

    def handle(self, *args, **options):
        try:
            site = Site.objects.get(id=8)
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR('Site with id=8 does not exist.'))
            return
        created = 0
        for type_key, _ in SITE_TOKEN_TYPE_CHOICES:
            if not SiteToken.objects.filter(site=site, type=type_key).exists():
                token = new_token()
                SiteToken.objects.create(site=site, token=token, type=type_key)
                self.stdout.write(self.style.SUCCESS(f"Created {type_key} token for {site.name}"))
                created += 1
        if created == 0:
            self.stdout.write(self.style.WARNING('All tokens already exist for site 8.'))
        else:
            self.stdout.write(self.style.SUCCESS(f"Created {created} tokens for site 8."))
