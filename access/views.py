from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .forms import SiteManagerProfileForm
from core.models import SiteManager
# ...existing code...

@login_required
def manager_profile(request):
    user = request.user
    # Check if user is a site manager
    if not SiteManager.objects.filter(user=user).exists() and not user.is_superuser:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = SiteManagerProfileForm(user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, user)  # Keep user logged in after password change
            messages.success(request, "Profile updated successfully.")
            return redirect('manager_profile')
    else:
        form = SiteManagerProfileForm(user)

    from core.perms import site_ids_for_user
    from core.models import Site
    site_ids = list(site_ids_for_user(request.user))
    sites = Site.objects.filter(id__in=site_ids).order_by("name")
    return render(request, 'access/manager_profile.html', {'form': form, 'sites': sites})
from .forms import AssociatedStaffSignInForm
# Associated staff self sign-in view
def associated_staff_signin(request, token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="public", is_active=True, site__is_active=True)
    site = token_obj.site
    error = None
    from .models import AssociatedStaff
    if request.method == "POST":
        form = AssociatedStaffSignInForm(request.POST)
        if form.is_valid():
            # Check for duplicate name at this site before saving
            name = form.cleaned_data["name"].strip()
            if AssociatedStaff.objects.filter(site=site, name=name).exists():
                error = f"The name '{name}' is already in use for this site. Please use a different name or ask staff for assistance."
            else:
                import secrets
                staff = form.save(commit=False)
                staff.site = site
                staff.signed_in_at = timezone.now()
                staff.is_active = True
                if not staff.checkout_token:
                    staff.checkout_token = secrets.token_urlsafe(16)
                staff.save()
                request.session["associated_staff_id"] = staff.id
                return redirect("associated_staff_checkin_complete", token=token, checkout_token=staff.checkout_token)
    else:
        form = AssociatedStaffSignInForm()
    return render(request, "access/associated_staff_signin.html", {"form": form, "site": site, "token": token, "error": error})

# Add a new check-in complete view for associated staff
def associated_staff_checkin_complete(request, token: str, checkout_token: str):
    from .models import AssociatedStaff
    token_obj = get_object_or_404(SiteToken, token=token, type="public", is_active=True, site__is_active=True)
    staff = get_object_or_404(AssociatedStaff, checkout_token=checkout_token, site=token_obj.site)
    return render(request, "access/associated_staff_checkin_complete.html", {"staff": staff, "token": token, "checkout_token": checkout_token})
def visitor_checkin_complete(request, token: str, checkout_token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="public", is_active=True, site__is_active=True)
    visitor = get_object_or_404(Visitor, checkout_token=checkout_token, site=token_obj.site)
    return render(request, "access/visitor_checkin_complete.html", {"visitor": visitor, "token": token, "checkout_token": checkout_token})
# --- Portal Views by SiteToken ---
from core.models import Site, SiteToken, SITE_TOKEN_TYPE_CHOICES
# --- Portal Views by SiteToken ---

from .forms import VisitorSignInForm, ContractorSignInForm
from .models import Visitor, Contractor, StaffMember
from django.views.decorators.csrf import csrf_exempt
def visitor_signin(request, token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="public", is_active=True, site__is_active=True)
    site = token_obj.site
    # No session logic; always show the form
    if request.method == "POST":
        form = VisitorSignInForm(request.POST)
        if form.is_valid():
            import secrets
            visitor = form.save(commit=False)
            visitor.site = site
            visitor.signed_in_at = timezone.now()
            visitor.is_active = True
            # Generate a unique checkout token
            visitor.checkout_token = secrets.token_urlsafe(16)
            visitor.save()
            request.session["visitor_id"] = visitor.id
            # Redirect to a dedicated check-in complete page
            return redirect("visitor_checkin_complete", token=token, checkout_token=visitor.checkout_token)
    else:
        form = VisitorSignInForm()
    return render(request, "access/visitor_signin.html", {"form": form, "site": site, "token": token})

def contractor_signin(request, token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="public", is_active=True, site__is_active=True)
    site = token_obj.site
    if request.method == "POST":
        form = ContractorSignInForm(request.POST)
        if form.is_valid():
            import secrets
            contractor = form.save(commit=False)
            contractor.site = site
            contractor.signed_in_at = timezone.now()
            contractor.is_active = True
            contractor.checkout_token = secrets.token_urlsafe(16)
            contractor.save()
            return redirect("contractor_checkin_complete", token=token, checkout_token=contractor.checkout_token)
    else:
        form = ContractorSignInForm()
    return render(request, "access/contractor_signin.html", {"form": form, "site": site, "token": token})
def contractor_checkin_complete(request, token: str, checkout_token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="public", is_active=True, site__is_active=True)
    contractor = get_object_or_404(Contractor, checkout_token=checkout_token, site=token_obj.site)
    return render(request, "access/contractor_checkin_complete.html", {"contractor": contractor, "token": token, "checkout_token": checkout_token})

def portal_public(request, token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="public", is_active=True, site__is_active=True)
    site = token_obj.site
    # Render a page with options: Visitors, Staff, Contractors
    return render(request, "access/portal_public.html", {"site": site, "token": token})

def portal_staff(request, token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="staff", is_active=True, site__is_active=True)
    site = token_obj.site
    # Handle sign-in/out actions
    msg = None
    if request.method == "POST":
        action = request.POST.get("action")
        entity_type = request.POST.get("entity_type")
        entity_id = request.POST.get("entity_id")
        if action in ("sign_in", "sign_out") and entity_type in ("visitor", "contractor", "associate") and entity_id:
            from .models import AccessEvent, AssociatedStaff
            direction = AccessEvent.IN if action == "sign_in" else AccessEvent.OUT
            if entity_type == "visitor":
                obj = get_object_or_404(Visitor, id=entity_id, site=site)
                if action == "sign_in":
                    obj.signed_in_at = timezone.now()
                    obj.signed_out_at = None
                    obj.is_active = True
                    msg = f"Visitor {obj.name} signed in."
                else:
                    obj.signed_out_at = timezone.now()
                    obj.is_active = False
                    msg = f"Visitor {obj.name} signed out."
                obj.save()
                # Log AccessEvent for visitor (as staff=None)
                AccessEvent.objects.create(site=site, staff=None, direction=direction, occurred_at=timezone.now())
            elif entity_type == "contractor":
                obj = get_object_or_404(Contractor, id=entity_id, site=site)
                if action == "sign_in":
                    obj.signed_in_at = timezone.now()
                    obj.signed_out_at = None
                    obj.is_active = True
                    msg = f"Contractor {obj.name} signed in."
                else:
                    obj.signed_out_at = timezone.now()
                    obj.is_active = False
                    msg = f"Contractor {obj.name} signed out."
                obj.save()
                # Log AccessEvent for contractor (as staff=None)
                AccessEvent.objects.create(site=site, staff=None, direction=direction, occurred_at=timezone.now())
            elif entity_type == "associate":
                obj = get_object_or_404(AssociatedStaff, id=entity_id, site=site)
                if action == "sign_in":
                    obj.signed_in_at = timezone.now()
                    obj.signed_out_at = None
                    obj.is_active = True
                    msg = f"Associate {obj.name} signed in."
                else:
                    obj.signed_out_at = timezone.now()
                    obj.is_active = False
                    msg = f"Associate {obj.name} signed out."
                obj.save()
                # Log AccessEvent for associate (as staff=None)
                AccessEvent.objects.create(site=site, staff=None, direction=direction, occurred_at=timezone.now())
        # Add new visitor/contractor
        elif action == "add_visitor":
            form = VisitorSignInForm(request.POST)
            if form.is_valid():
                visitor = form.save(commit=False)
                visitor.site = site
                visitor.signed_in_at = timezone.now()
                visitor.is_active = True
                visitor.save()
                msg = f"Visitor {visitor.name} added and signed in."
        elif action == "add_contractor":
            form = ContractorSignInForm(request.POST)
            if form.is_valid():
                contractor = form.save(commit=False)
                contractor.site = site
                contractor.signed_in_at = timezone.now()
                contractor.is_active = True
                contractor.save()
                msg = f"Contractor {contractor.name} added and signed in."

    # List all visitors/contractors/associated staff for this site
    visitors = Visitor.objects.filter(site=site).order_by('-signed_in_at', 'name')
    visitors_in = visitors.filter(signed_in_at__isnull=False, signed_out_at__isnull=True)
    contractors = Contractor.objects.filter(site=site).order_by('-signed_in_at', 'name')
    contractors_in = contractors.filter(signed_in_at__isnull=False, signed_out_at__isnull=True)
    from .models import AssociatedStaff
    associates = AssociatedStaff.objects.filter(site=site, is_active=True, signed_out_at__isnull=True).order_by('name')
    visitor_form = VisitorSignInForm()
    contractor_form = ContractorSignInForm()
    # Staff currently in the building (latest AccessEvent direction == IN)
    from .models import StaffMember, AccessEvent
    from django.db.models import OuterRef, Subquery
    latest_dir = AccessEvent.objects.filter(site=site, staff_id=OuterRef("pk"), on_site=True).order_by("-occurred_at").values("direction")[:1]
    latest_at = AccessEvent.objects.filter(site=site, staff_id=OuterRef("pk"), on_site=True).order_by("-occurred_at").values("occurred_at")[:1]
    staff_in = StaffMember.objects.filter(site=site, is_active=True).annotate(
        last_direction=Subquery(latest_dir),
        last_at=Subquery(latest_at),
    ).filter(last_direction=AccessEvent.IN).order_by("name")

    # Staff currently WFH (latest remote event is IN)
    latest_wfh_dir = AccessEvent.objects.filter(site=site, staff_id=OuterRef("pk"), on_site=False).order_by("-occurred_at").values("direction")[:1]
    latest_wfh_at = AccessEvent.objects.filter(site=site, staff_id=OuterRef("pk"), on_site=False).order_by("-occurred_at").values("occurred_at")[:1]
    staff_wfh = StaffMember.objects.filter(site=site, is_active=True).annotate(
        last_wfh_direction=Subquery(latest_wfh_dir),
        last_wfh_at=Subquery(latest_wfh_at),
    ).filter(last_wfh_direction=AccessEvent.IN).order_by("name")

    from core.perms import site_ids_for_user
    from core.models import Site
    site_ids = list(site_ids_for_user(request.user)) if hasattr(request, 'user') and request.user.is_authenticated else []
    sites = Site.objects.filter(id__in=site_ids).order_by("name") if site_ids else Site.objects.none()
    return render(request, "access/portal_staff.html", {
        "site": site,
        "sites": sites,
        "token": token,
        "visitors": visitors,
        "visitors_in": visitors_in,
        "contractors": contractors,
        "contractors_in": contractors_in,
        "associates": associates,
        "visitor_form": visitor_form,
        "contractor_form": contractor_form,
        "msg": msg,
        "staff_in": staff_in,
        "staff_wfh": staff_wfh,
    })

def portal_keypad(request, token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="keypad", is_active=True, site__is_active=True)
    site = token_obj.site
    # Use the existing scan.html template for keypad sign-in
    resolve_url = reverse('scan_resolve_pin', kwargs={'token': token})
    confirm_url = reverse('scan_confirm', kwargs={'token': token})
    normal_scan = reverse('scan_page', kwargs={'token': token})
    wfh_url = reverse('wfh_signin', kwargs={'token': token})
    return render(request, "access/scan.html", {"site": site, "token": token, "resolve_url": resolve_url, "confirm_url": confirm_url, "is_wfh": False, "normal_scan_url": normal_scan, "wfh_url": wfh_url})

def portal_fire(request, token: str):
    token_obj = get_object_or_404(SiteToken, token=token, type="fire", is_active=True, site__is_active=True)
    site = token_obj.site
    # Use the existing public_staff_list.html template for fire roll call
    latest_dir = AccessEvent.objects.filter(site=site, staff_id=OuterRef("pk"), on_site=True).order_by("-occurred_at").values("direction")[:1]
    latest_at = AccessEvent.objects.filter(site=site, staff_id=OuterRef("pk"), on_site=True).order_by("-occurred_at").values("occurred_at")[:1]
    who_is_in = StaffMember.objects.filter(site=site, is_active=True).annotate(
        last_direction=Subquery(latest_dir),
        last_at=Subquery(latest_at),
    ).filter(last_direction=AccessEvent.IN).order_by("name")
    normal_scan = reverse('scan_page', kwargs={'token': token})
    return render(request, "access/public_staff_list.html", {"site": site, "who_is_in": who_is_in, "now": now(), "token": token, "normal_scan_url": normal_scan})
from django.utils.timezone import now

# Public view for on-site staff (fire evacuation)
def public_staff_list(request, fire_token: str):
    from core.models import SiteToken
    token_obj = get_object_or_404(SiteToken, token=fire_token, type="fire", is_active=True, site__is_active=True)
    site = token_obj.site
    latest_dir = AccessEvent.objects.filter(site=site, staff_id=OuterRef("pk"), on_site=True).order_by("-occurred_at").values("direction")[:1]
    latest_at = AccessEvent.objects.filter(site=site, staff_id=OuterRef("pk"), on_site=True).order_by("-occurred_at").values("occurred_at")[:1]
    who_is_in = StaffMember.objects.filter(site=site, is_active=True).annotate(
        last_direction=Subquery(latest_dir),
        last_at=Subquery(latest_at),
    ).filter(last_direction=AccessEvent.IN).order_by("name")
    from .models import Visitor, Contractor, AssociatedStaff
    visitors_in = Visitor.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True).order_by('-signed_in_at', 'name')
    contractors_in = Contractor.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True).order_by('-signed_in_at', 'name')
    associates_in = AssociatedStaff.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True).order_by('name')
    print('DEBUG who_is_in:', list(who_is_in.values('id', 'name', 'last_at')) if hasattr(who_is_in, 'values') else who_is_in)
    print('DEBUG associates_in:', list(associates_in.values('id', 'name', 'signed_in_at')) if hasattr(associates_in, 'values') else associates_in)
    print('DEBUG visitors_in:', list(visitors_in.values('id', 'name', 'signed_in_at', 'is_active')) if hasattr(visitors_in, 'values') else visitors_in)
    print('DEBUG contractors_in:', list(contractors_in.values('id', 'name', 'signed_in_at', 'is_active')) if hasattr(contractors_in, 'values') else contractors_in)
    # Add visitors, contractors, associates currently in
    from .models import Visitor, Contractor, AssociatedStaff
    visitors_in = Visitor.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True).order_by('-signed_in_at', 'name')
    contractors_in = Contractor.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True).order_by('-signed_in_at', 'name')
    associates_in = AssociatedStaff.objects.filter(site=site, is_active=True, signed_out_at__isnull=True).order_by('name')
    print('DEBUG visitors_in:', list(visitors_in.values('id', 'name', 'site_id', 'is_active', 'signed_in_at', 'signed_out_at')))
    print('DEBUG contractors_in:', list(contractors_in.values('id', 'name', 'site_id', 'is_active', 'signed_in_at', 'signed_out_at')))

    # Add visitors, contractors, associates currently in
    from .models import Visitor, Contractor, AssociatedStaff
    visitors_in = Visitor.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True).order_by('name')
    contractors_in = Contractor.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True).order_by('name')
    associates_in = AssociatedStaff.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True).order_by('name')

    fire_url = request.build_absolute_uri(reverse("public_staff_list", kwargs={"fire_token": fire_token}))
    return render(request, "access/public_staff_list.html", {
        "site": site,
        "who_is_in": who_is_in,
        "visitors_in": visitors_in,
        "contractors_in": contractors_in,
        "associates_in": associates_in,
        "now": now(),
        "fire_url": fire_url,
    })
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from core.models import Site
from core.perms import user_can_manage_site, site_ids_for_user
from .models import StaffMember, AccessEvent
from .forms import StaffCreateForm, StaffPinResetForm

DOUBLE_SCAN_SECONDS = 30

# ---------- Public scan (staff) ----------
def scan_page(request, token: str):
    # Use SiteToken for check-in QR (type 'public' or 'checkin')
    token_obj = get_object_or_404(SiteToken, token=token, is_active=True, site__is_active=True)
    resolve_url = reverse('scan_resolve_pin', kwargs={'token': token})
    confirm_url = reverse('scan_confirm', kwargs={'token': token})
    normal_scan = reverse('scan_page', kwargs={'token': token})
    wfh_url = reverse('wfh_signin', kwargs={'token': token})
    return render(request, "access/scan.html", {"site": token_obj.site, "token": token, "resolve_url": resolve_url, "confirm_url": confirm_url, "is_wfh": False, "normal_scan_url": normal_scan, "wfh_url": wfh_url})

@transaction.atomic
def scan_resolve_pin(request, token: str):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    token_obj = get_object_or_404(SiteToken, token=token, is_active=True, site__is_active=True)
    pin = (request.POST.get("pin") or "").strip()

    if not (pin.isdigit() and len(pin) == 6):
        return JsonResponse({"error": "PIN must be exactly 6 digits."}, status=400)

    # POC-sized: iterate staff for site and verify hash
    staff_qs = StaffMember.objects.select_for_update().filter(site=token_obj.site, is_active=True)
    matched = None
    for s in staff_qs:
        if s.check_pin(pin):
            matched = s
            break
    if not matched:
        return JsonResponse({"error": "PIN not recognised."}, status=401)

    last = AccessEvent.objects.filter(site=token_obj.site, staff=matched).order_by("-occurred_at").first()
    if last and (timezone.now() - last.occurred_at).total_seconds() < DOUBLE_SCAN_SECONDS:
        return JsonResponse({
            "error": "Flood/spam protection: You are acting too soon. Please wait a moment before trying again.",
            "last_direction": last.direction,
            "last_at": last.occurred_at.isoformat(),
        }, status=429)

    suggested = AccessEvent.OUT if (last and last.direction == AccessEvent.IN) else AccessEvent.IN

    return JsonResponse({
        "staff_id": matched.id,
        "staff_name": matched.name,
        "suggested": suggested,
        "last_direction": last.direction if last else None,
        "last_at": last.occurred_at.isoformat() if last else None,
    })

@transaction.atomic
def scan_confirm(request, token: str):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    token_obj = get_object_or_404(SiteToken, token=token, is_active=True, site__is_active=True)
    staff_id = request.POST.get("staff_id")
    direction = request.POST.get("direction")

    if direction not in (AccessEvent.IN, AccessEvent.OUT):
        return JsonResponse({"error": "Invalid direction."}, status=400)

    staff = get_object_or_404(StaffMember, id=staff_id, site=token_obj.site, is_active=True)

    last = AccessEvent.objects.filter(site=token_obj.site, staff=staff).order_by("-occurred_at").first()
    if last and last.direction == direction:
        return JsonResponse({"error": "No change needed (already that status)."}, status=409)

    if last and (timezone.now() - last.occurred_at).total_seconds() < DOUBLE_SCAN_SECONDS:
        return JsonResponse({"error": "Flood/spam protection: You are acting too soon. Please wait a moment before trying again."}, status=429)

    ev = AccessEvent.objects.create(site=token_obj.site, staff=staff, direction=direction)
    return JsonResponse({"ok": True, "direction": ev.direction, "at": ev.occurred_at.isoformat()})


@transaction.atomic
def scan_resolve_pin_wfh(request, token: str):
    # same as scan_resolve_pin but used by WFH keypad flow
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    token_obj = get_object_or_404(SiteToken, token=token, is_active=True, site__is_active=True)
    pin = (request.POST.get("pin") or "").strip()

    if not (pin.isdigit() and len(pin) == 6):
        return JsonResponse({"error": "PIN must be exactly 6 digits."}, status=400)

    staff_qs = StaffMember.objects.select_for_update().filter(site=token_obj.site, is_active=True)
    matched = None
    for s in staff_qs:
        if s.check_pin(pin):
            matched = s
            break
    if not matched:
        return JsonResponse({"error": "PIN not recognised."}, status=401)

    last = AccessEvent.objects.filter(site=token_obj.site, staff=matched).order_by("-occurred_at").first()
    if last and (timezone.now() - last.occurred_at).total_seconds() < DOUBLE_SCAN_SECONDS:
        return JsonResponse({
            "error": "Flood/spam protection: You are acting too soon. Please wait a moment before trying again.",
            "last_direction": last.direction,
            "last_at": last.occurred_at.isoformat(),
        }, status=429)

    suggested = AccessEvent.OUT if (last and last.direction == AccessEvent.IN) else AccessEvent.IN

    return JsonResponse({
        "staff_id": matched.id,
        "staff_name": matched.name,
        "suggested": suggested,
        "last_direction": last.direction if last else None,
        "last_at": last.occurred_at.isoformat() if last else None,
    })


@transaction.atomic
def scan_confirm_wfh(request, token: str):
    # similar to scan_confirm but records on_site=False
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    token_obj = get_object_or_404(SiteToken, token=token, is_active=True, site__is_active=True)
    staff_id = request.POST.get("staff_id")
    direction = request.POST.get("direction")

    if direction not in (AccessEvent.IN, AccessEvent.OUT):
        return JsonResponse({"error": "Invalid direction."}, status=400)

    staff = get_object_or_404(StaffMember, id=staff_id, site=token_obj.site, is_active=True)

    last = AccessEvent.objects.filter(site=token_obj.site, staff=staff).order_by("-occurred_at").first()
    if last and last.direction == direction:
        return JsonResponse({"error": "No change needed (already that status)."}, status=409)

    if last and (timezone.now() - last.occurred_at).total_seconds() < DOUBLE_SCAN_SECONDS:
        return JsonResponse({"error": "Flood/spam protection: You are acting too soon. Please wait a moment before trying again."}, status=429)

    ev = AccessEvent.objects.create(site=token_obj.site, staff=staff, direction=direction, on_site=False)
    return JsonResponse({"ok": True, "direction": ev.direction, "at": ev.occurred_at.isoformat()})


# ---------- Work From Home sign-in (simple PIN + confirmations) ----------
@transaction.atomic
def wfh_signin(request, token: str):
    # Render the same keypad scan UI but wired to WFH resolve/confirm endpoints
    token_obj = get_object_or_404(SiteToken, token=token, is_active=True, site__is_active=True)
    site = token_obj.site
    resolve_url = reverse('scan_resolve_pin_wfh', kwargs={'token': token})
    confirm_url = reverse('scan_confirm_wfh', kwargs={'token': token})
    normal_scan = reverse('scan_page', kwargs={'token': token})
    wfh_url = reverse('wfh_signin', kwargs={'token': token})
    return render(request, "access/scan.html", {"site": site, "token": token, "resolve_url": resolve_url, "confirm_url": confirm_url, "is_wfh": True, "normal_scan_url": normal_scan, "wfh_url": wfh_url})

# ---------- Manager views ----------
def _get_site_or_404_for_user(user, site_id: int) -> Site:
    if not user_can_manage_site(user, site_id):
        raise Http404()
    return get_object_or_404(Site, id=site_id, is_active=True)

@login_required
def manager_dashboard(request):

    # Get all site ids user can access
    site_ids = list(site_ids_for_user(request.user))
    if not site_ids:
        return render(request, "sbadmin/no_sites.html")

    # Priority: GET param > session > first available
    site_id = request.GET.get("site")
    if site_id:
        site_id = int(site_id)
        if site_id not in site_ids and not request.user.is_superuser:
            raise Http404()
        request.session['site_id'] = site_id
    else:
        site_id = request.session.get('site_id')
        if site_id and int(site_id) in site_ids:
            site_id = int(site_id)
        else:
            site_id = int(site_ids[0])
            request.session['site_id'] = site_id

    site = _get_site_or_404_for_user(request.user, site_id)

    from .models import AssociatedStaff
    associates_in = AssociatedStaff.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True).order_by('name')
    from django.utils import timezone
    from datetime import datetime, time
    today = timezone.localdate()
    associates_today = AssociatedStaff.objects.filter(site=site, signed_in_at__date=today).order_by('name')
    # Handle sign-out POST for visitor/contractor
    if request.method == "POST":
        action = request.POST.get("action")
        entity_type = request.POST.get("entity_type")
        entity_id = request.POST.get("entity_id")
        if action == "sign_out" and entity_type in ("visitor", "contractor", "associate") and entity_id:
            if entity_type == "visitor":
                obj = Visitor.objects.filter(id=entity_id, site=site, is_active=True, signed_out_at__isnull=True).first()
            elif entity_type == "contractor":
                obj = Contractor.objects.filter(id=entity_id, site=site, is_active=True, signed_out_at__isnull=True).first()
            elif entity_type == "associate":
                obj = AssociatedStaff.objects.filter(id=entity_id, site=site, is_active=True, signed_out_at__isnull=True).first()
            else:
                obj = None
            if obj:
                from django.utils import timezone
                obj.signed_out_at = timezone.now()
                obj.is_active = False
                obj.save()
        # Always redirect to avoid resubmission
        return redirect(request.path + f'?site={site_id}')

    # KPIs
    # Define start and end for today
    start = datetime.combine(today, time.min, tzinfo=timezone.get_current_timezone())
    end = datetime.combine(today, time.max, tzinfo=timezone.get_current_timezone())
    total_staff = StaffMember.objects.filter(site=site).count()
    total_events_today = AccessEvent.objects.filter(site=site, occurred_at__range=(start, end)).count()
    # Auto clock-out KPIs
    from datetime import timedelta
    yesterday = today - timedelta(days=1)
    y_start = datetime.combine(yesterday, time.min, tzinfo=timezone.get_current_timezone())
    y_end = datetime.combine(yesterday, time.max, tzinfo=timezone.get_current_timezone())
    auto_yesterday = AccessEvent.objects.filter(site=site, auto_clockout=True, occurred_at__range=(y_start, y_end)).count()
    week_start = today - timedelta(days=today.weekday())
    w_start = datetime.combine(week_start, time.min, tzinfo=timezone.get_current_timezone())
    auto_week = AccessEvent.objects.filter(site=site, auto_clockout=True, occurred_at__gte=w_start).count()
    # Visitors and contractors currently on site (signed in, not signed out, active)
    visitors_in = Visitor.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True)
    contractors_in = Contractor.objects.filter(site=site, is_active=True, signed_in_at__isnull=False, signed_out_at__isnull=True)

    # Staff seen today: any IN event today (daily attendance logic)
    start = datetime.combine(today, time.min, tzinfo=timezone.get_current_timezone())
    end = datetime.combine(today, time.max, tzinfo=timezone.get_current_timezone())
    staff_in_today_ids = AccessEvent.objects.filter(site=site, direction=AccessEvent.IN, occurred_at__range=(start, end)).values_list('staff_id', flat=True).distinct()
    staff_in_today = StaffMember.objects.filter(id__in=staff_in_today_ids, site=site)

    # Who's In: staff whose latest event today is IN (not OUT), only one row per staff
    from django.db.models import OuterRef, Subquery
    latest_event_today = AccessEvent.objects.filter(
        site=site,
        staff_id=OuterRef('pk'),
        occurred_at__range=(start, end)
    ).order_by('-occurred_at')
    staff_with_latest = StaffMember.objects.filter(site=site).annotate(
        last_event_direction=Subquery(latest_event_today.values('direction')[:1]),
        last_at=Subquery(latest_event_today.values('occurred_at')[:1])
    ).filter(last_event_direction=AccessEvent.IN)
    who_is_in = staff_with_latest

    # Staff currently WFH (latest remote event is IN)
    latest_wfh_dir = AccessEvent.objects.filter(site=site, staff_id=OuterRef('pk'), on_site=False).order_by('-occurred_at').values('direction')[:1]
    latest_wfh_at = AccessEvent.objects.filter(site=site, staff_id=OuterRef('pk'), on_site=False).order_by('-occurred_at').values('occurred_at')[:1]
    staff_wfh = StaffMember.objects.filter(site=site, is_active=True).annotate(
        last_wfh_direction=Subquery(latest_wfh_dir),
        last_wfh_at=Subquery(latest_wfh_at),
    ).filter(last_wfh_direction=AccessEvent.IN).order_by('name')

    context = {
        "site": site,
        "sites": Site.objects.filter(id__in=site_ids_for_user(request.user)).order_by("name"),
        "associates_in": associates_in,
        "associates_today": associates_today,
        "total_staff": total_staff,
        "total_events_today": total_events_today,
        "auto_clockout_yesterday": auto_yesterday,
        "auto_clockout_week": auto_week,
        "visitors_in": visitors_in,
        "contractors_in": contractors_in,
        "staff_in_today": staff_in_today,
        "who_is_in": who_is_in,
        "staff_wfh": staff_wfh,
    }
    return render(request, "manager/dashboard.html", context)

@login_required
def manager_audit(request, site_id: int):
    site = _get_site_or_404_for_user(request.user, site_id)
    qs = AccessEvent.objects.select_related("staff").filter(site=site)

    staff_id = request.GET.get("staff")
    if staff_id:
        qs = qs.filter(staff_id=int(staff_id))

    from core.perms import site_ids_for_user
    site_ids = list(site_ids_for_user(request.user))
    from core.models import Site
    sites = Site.objects.filter(id__in=site_ids).order_by("name")
    context = {
        "site": site,
        "sites": sites,
        "events": qs[:500],
        "staff_list": StaffMember.objects.filter(site=site).order_by("name"),
        "selected_staff": int(staff_id) if staff_id else None,
    }
    return render(request, "manager/audit.html", context)

@login_required
def manager_staff(request, site_id: int):
    site = _get_site_or_404_for_user(request.user, site_id)

    from core.forms_manager import ManagerInviteForm
    invite_success = None
    invite_error = None

    if request.method == "POST":
        if "invite_manager" in request.POST:
            invite_form = ManagerInviteForm(request.POST)
            if invite_form.is_valid():
                try:
                    user, created = invite_form.save()
                    invite_success = f"{'Invited' if created else 'Added'} manager: {user.email}"
                except Exception as e:
                    invite_error = str(e)
            else:
                invite_error = invite_form.errors.as_text()
            form = StaffCreateForm(site=site)
        else:
            form = StaffCreateForm(request.POST, site=site)
            invite_form = ManagerInviteForm(initial={"site": site})
            if form.is_valid():
                obj = form.save(commit=False)
                obj.site = site
                obj.save()
                return redirect("manager_staff", site_id=site.id)
    else:
        form = StaffCreateForm(site=site)
        invite_form = ManagerInviteForm(initial={"site": site})

    from core.perms import site_ids_for_user
    site_ids = list(site_ids_for_user(request.user))
    from core.models import Site, SiteManager
    sites = Site.objects.filter(id__in=site_ids).order_by("name")
    site_managers = SiteManager.objects.filter(site=site).select_related("user").order_by("user__email")
    context = {
        "site": site,
        "sites": sites,
        "form": form,
        "invite_form": invite_form,
        "invite_success": invite_success,
        "invite_error": invite_error,
        "staff": StaffMember.objects.filter(site=site).order_by("name"),
        "site_managers": site_managers,
    }
    return render(request, "manager/staff.html", context)

@login_required
def manager_staff_detail(request, site_id: int, staff_id: int):
    site = _get_site_or_404_for_user(request.user, site_id)
    staff = get_object_or_404(StaffMember, id=staff_id, site=site)

    from .forms import StaffRenameForm
    rename_form = StaffRenameForm(site=site, staff=staff)
    form = StaffPinResetForm(site=site, staff=staff)
    if request.method == "POST":
        if "toggle_active" in request.POST:
            staff.is_active = not staff.is_active
            staff.save(update_fields=["is_active"])
            return redirect("manager_staff", site_id=site.id)

        if "reset_pin" in request.POST:
            form = StaffPinResetForm(request.POST, site=site, staff=staff)
            if form.is_valid():
                staff.set_pin(form.cleaned_data["pin"])
                staff.save(update_fields=["pin_hash", "pin_value"])
                return redirect("manager_staff_detail", site_id=site.id, staff_id=staff.id)

        if "rename" in request.POST:
            rename_form = StaffRenameForm(request.POST, site=site, staff=staff)
            if rename_form.is_valid():
                staff.name = rename_form.cleaned_data["name"]
                staff.save(update_fields=["name"])
                return redirect("manager_staff_detail", site_id=site.id, staff_id=staff.id)

    from django.core.paginator import Paginator
    from datetime import timedelta
    all_events = AccessEvent.objects.filter(site=site, staff=staff).order_by("-occurred_at")
    recent_events = all_events[:10]
    page_number = request.GET.get("page", 1)
    paginator = Paginator(all_events, 25)
    page_obj = paginator.get_page(page_number)
    today = timezone.localdate()
    week_ago = today - timedelta(days=7)
    three_months_ago = today - timedelta(days=90)
    # Check-ins (IN)
    checkins_today = all_events.filter(direction=AccessEvent.IN, occurred_at__date=today).count()
    checkins_week = all_events.filter(direction=AccessEvent.IN, occurred_at__date__gte=week_ago).count()
    checkins_3months = all_events.filter(direction=AccessEvent.IN, occurred_at__date__gte=three_months_ago).count()
    # Auto clock-outs
    auto_week = all_events.filter(auto_clockout=True, occurred_at__date__gte=week_ago).count()
    auto_3months = all_events.filter(auto_clockout=True, occurred_at__date__gte=three_months_ago).count()

    # Total hours on site (last 7 days)
    from datetime import timedelta
    events_7d = all_events.filter(occurred_at__date__gte=week_ago).order_by('occurred_at')
    total_seconds = 0
    in_time = None
    for ev in events_7d:
        if ev.direction == AccessEvent.IN:
            in_time = ev.occurred_at
        elif ev.direction == AccessEvent.OUT and in_time:
            total_seconds += (ev.occurred_at - in_time).total_seconds()
            in_time = None
    total_hours_7d = round(total_seconds / 3600, 2)

    # Last check-out time (last 7 days)
    last_checkout_7d = all_events.filter(direction=AccessEvent.OUT, occurred_at__date__gte=week_ago).order_by('-occurred_at').first()
    last_checkout_7d_time = last_checkout_7d.occurred_at if last_checkout_7d else None

    # First check-in time (last 7 days)
    first_checkin_7d = all_events.filter(direction=AccessEvent.IN, occurred_at__date__gte=week_ago).order_by('occurred_at').first()
    first_checkin_7d_time = first_checkin_7d.occurred_at if first_checkin_7d else None

    from core.perms import site_ids_for_user
    from core.models import Site
    site_ids = list(site_ids_for_user(request.user))
    sites = Site.objects.filter(id__in=site_ids).order_by("name")
    context = {
        "site": site,
        "sites": sites,
        "staff_obj": staff,
        "pin_form": form,
        "recent_events": recent_events,
        "page_obj": page_obj,
        "checkins_today": checkins_today,
        "checkins_week": checkins_week,
        "checkins_3months": checkins_3months,
        "auto_week": auto_week,
        "auto_3months": auto_3months,
        "total_hours_7d": total_hours_7d,
        "last_checkout_7d_time": last_checkout_7d_time,
        "first_checkin_7d_time": first_checkin_7d_time,
    }
    return render(request, "manager/staff_detail.html", context)

@login_required
def manager_qr(request, site_id: int):
    site = _get_site_or_404_for_user(request.user, site_id)

    # Generate missing tokens
    if request.method == "POST":
        # Only handle fire token rotation here now
        if "generate_fire_token" in request.POST or "rotate_fire_token" in request.POST:
            from core.models import new_token, SiteToken
            fire_token_obj, created = SiteToken.objects.get_or_create(site=site, type="fire", defaults={"token": new_token()})
            if not created:
                fire_token_obj.token = new_token()
                fire_token_obj.is_active = True
                fire_token_obj.save(update_fields=["token", "is_active"])
            return redirect("manager_qr", site_id=site.id)

    from core.models import SiteToken, SITE_TOKEN_TYPE_CHOICES
    # Gather all portal tokens for this site
    portal_tokens = SiteToken.objects.filter(site=site, is_active=True)
    portal_links = []
    for t in portal_tokens:
        if t.type == "public":
            url = request.build_absolute_uri(reverse("portal_public", kwargs={"token": t.token}))
        elif t.type == "staff":
            url = request.build_absolute_uri(reverse("portal_staff", kwargs={"token": t.token}))
        elif t.type == "keypad":
            url = request.build_absolute_uri(reverse("portal_keypad", kwargs={"token": t.token}))
        elif t.type == "fire":
            url = request.build_absolute_uri(reverse("portal_fire", kwargs={"token": t.token}))
        else:
            url = None
        # Provide an optional WFH URL for tokens that support staff-style sign-in
        wfh_url = None
        if t.type in ("staff", "keypad"):
            wfh_url = request.build_absolute_uri(reverse("wfh_signin", kwargs={"token": t.token}))

        portal_links.append({
            "type": t.get_type_display(),
            "token": t.token,
            "url": url,
            "wfh_url": wfh_url,
            "raw_type": t.type,
        })
    from core.perms import site_ids_for_user
    from core.models import Site
    site_ids = list(site_ids_for_user(request.user))
    sites = Site.objects.filter(id__in=site_ids).order_by("name")
    context = {"site": site, "sites": sites, "portal_links": portal_links}
    return render(request, "manager/qr.html", context)
