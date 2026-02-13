from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from access.models import AssociatedStaff
from core.models import SiteToken

def associated_staff_self_checkout(request, token: str, checkout_token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="public", is_active=True, site__is_active=True)
    try:
        staff = AssociatedStaff.objects.get(checkout_token=checkout_token, site=token_obj.site)
    except AssociatedStaff.DoesNotExist:
        return render(request, "access/associated_staff_checkout.html", {"invalid_token": True, "site": token_obj.site, "token": token})
    if not staff.is_active:
        return render(request, "access/associated_staff_checkout.html", {"already_signed_out": True, "staff": staff, "site": token_obj.site, "token": token})
    if request.method == "POST":
        staff.is_active = False
        staff.signed_out_at = timezone.now()
        staff.save()
        return render(request, "access/generic_checkout_complete.html", {"site": token_obj.site, "token": token})
    return render(request, "access/associated_staff_checkout.html", {"staff": staff, "site": token_obj.site, "token": token})
