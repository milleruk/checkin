from typing import Iterable
from .models import Site, SiteManager

def site_ids_for_user(user) -> Iterable[int]:
    if user.is_superuser:
        return Site.objects.filter(is_active=True).values_list("id", flat=True)
    return SiteManager.objects.filter(user=user, site__is_active=True).values_list("site_id", flat=True)

def user_can_manage_site(user, site_id: int) -> bool:
    if user.is_superuser:
        return True
    return SiteManager.objects.filter(user=user, site_id=site_id).exists()
