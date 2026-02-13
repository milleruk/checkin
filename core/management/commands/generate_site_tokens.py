from django.core.management.base import BaseCommand
from core.models import Site, SiteToken, SITE_TOKEN_TYPE_CHOICES, new_token

class Command(BaseCommand):
    help = 'Generate missing tokens for each portal view per site.'

    def handle(self, *args, **options):
        created = 0
        for site in Site.objects.all():
            for type_key, _ in SITE_TOKEN_TYPE_CHOICES:
                if not SiteToken.objects.filter(site=site, type=type_key).exists():
                    token = new_token()
                    SiteToken.objects.create(site=site, token=token, type=type_key)
                    self.stdout.write(self.style.SUCCESS(f"Created {type_key} token for {site.name}"))
                    created += 1
        if created == 0:
            self.stdout.write(self.style.WARNING('All tokens already exist.'))
        else:
            self.stdout.write(self.style.SUCCESS(f"Created {created} tokens."))
