from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from access.models import Visitor, Contractor
from core.models import SiteToken

def visitor_self_checkout(request, token: str, checkout_token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="public", is_active=True, site__is_active=True)
    try:
        visitor = Visitor.objects.get(checkout_token=checkout_token, site=token_obj.site)
    except Visitor.DoesNotExist:
        return render(request, "access/visitor_checkout.html", {"invalid_token": True, "site": token_obj.site, "token": token})
    if not visitor.is_active or visitor.signed_out_at:
        return render(request, "access/visitor_checkout.html", {"already_signed_out": True, "visitor": visitor, "site": token_obj.site, "token": token})
    if request.method == "POST":
        visitor.signed_out_at = timezone.now()
        visitor.is_active = False
        visitor.save()
        return render(request, "access/generic_checkout_complete.html", {"site": token_obj.site, "token": token})
    return render(request, "access/visitor_checkout.html", {"visitor": visitor, "site": token_obj.site, "token": token})

def contractor_self_checkout(request, token: str, checkout_token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="public", is_active=True, site__is_active=True)
    try:
        contractor = Contractor.objects.get(checkout_token=checkout_token, site=token_obj.site)
    except Contractor.DoesNotExist:
        return render(request, "access/contractor_checkout.html", {"invalid_token": True, "site": token_obj.site, "token": token})
    if not contractor.is_active or contractor.signed_out_at:
        return render(request, "access/contractor_checkout.html", {"already_signed_out": True, "contractor": contractor, "site": token_obj.site, "token": token})
    if request.method == "POST":
        contractor.signed_out_at = timezone.now()
        contractor.is_active = False
        contractor.save()
        return render(request, "access/generic_checkout_complete.html", {"site": token_obj.site, "token": token})
    return render(request, "access/contractor_checkout.html", {"contractor": contractor, "site": token_obj.site, "token": token})
