from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Site, SiteToken, SITE_TOKEN_TYPE_CHOICES, new_token

@receiver(post_save, sender=Site)
def create_site_tokens(sender, instance, created, **kwargs):
    if created:
        for type_key, _ in SITE_TOKEN_TYPE_CHOICES:
            if not SiteToken.objects.filter(site=instance, type=type_key).exists():
                SiteToken.objects.create(site=instance, token=new_token(), type=type_key)
