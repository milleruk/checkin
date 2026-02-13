from .forms import SiteSettingsForm
from .perms import user_can_manage_site
from .models import Site
# Site manager: Edit site settings (confidentiality, health & safety)
from django.contrib.auth.decorators import login_required
@login_required
def site_settings(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not user_can_manage_site(request.user, site_id):
        return HttpResponse('Unauthorized', status=403)
    if request.method == "POST":
        form = SiteSettingsForm(request.POST, instance=site)
        if form.is_valid():
            form.save()
            return redirect(request.path)
    else:
        form = SiteSettingsForm(instance=site)
    from core.perms import site_ids_for_user
    site_ids = list(site_ids_for_user(request.user))
    sites = Site.objects.filter(id__in=site_ids).order_by("name")
    return render(request, "core/site_settings.html", {"site": site, "sites": sites, "form": form})
# All imports at the top
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .forms import SiteCreateForm, UserCreateForm, SiteManagerAssignForm
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json
import io
import qrcode
# Superuser: List all users with sites managed
@user_passes_test(lambda u: u.is_superuser)
def superuser_user_list(request):
    from .models import SiteManager, Site, User
    users = User.objects.all().order_by('username')
    user_data = []
    for user in users:
        sites = Site.objects.filter(manager_links__user=user)
        user_data.append({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_active': user.is_active,
            'is_superuser': user.is_superuser,
            'sites': [s.name for s in sites],
        })
    return render(request, "core/superuser/user_list.html", {"users": user_data})

# Superuser: User detail with assigned sites
@user_passes_test(lambda u: u.is_superuser)
def superuser_user_detail(request, user_id):
    from .models import Site, User, SiteManager
    user = get_object_or_404(User, id=user_id)
    from .forms import SiteManagerAssignForm
    from .models import SiteManager
    # Handle add site
    add_form = None
    remove_site_id = request.POST.get('remove_site_id')
    if request.method == "POST" and 'add_site' in request.POST:
        add_form = SiteManagerAssignForm(request.POST)
        add_form.fields["user"].queryset = User.objects.filter(id=user.id)
        if add_form.is_valid():
            site = add_form.cleaned_data["site"]
            SiteManager.objects.get_or_create(site=site, user=user)
    # Handle remove site
    if request.method == "POST" and remove_site_id:
        try:
            site = Site.objects.get(id=remove_site_id)
            SiteManager.objects.filter(site=site, user=user).delete()
        except Site.DoesNotExist:
            pass
    # Prepare forms and site lists
    if user.is_superuser:
        sites = Site.objects.all().order_by("name")
    else:
        sites = Site.objects.filter(manager_links__user=user)
    # Only show sites user is not already assigned to
    assigned_site_ids = sites.values_list('id', flat=True)
    add_form = add_form or SiteManagerAssignForm(initial={"user": user})
    add_form.fields["user"].queryset = User.objects.filter(id=user.id)
    add_form.fields["site"].queryset = Site.objects.exclude(id__in=assigned_site_ids)
    # No pin_forms logic, as SiteManagerPinForm does not exist
    return render(request, "core/superuser/user_detail.html", {"user": user, "sites": sites, "add_form": add_form})

# Superuser: Site detail with assigned managers
@user_passes_test(lambda u: u.is_superuser)
def superuser_site_detail(request, site_id):
    from .models import Site, User, SiteManager
    site = get_object_or_404(Site, id=site_id)
    managers = User.objects.filter(site_links__site=site)
    # Manager assignment form
    from .forms import SiteManagerAssignForm
    assign_form = SiteManagerAssignForm(initial={"site": site})
    assign_form.fields["site"].queryset = Site.objects.filter(id=site.id)
    assign_form.fields["user"].queryset = User.objects.filter(is_active=True, is_superuser=False).exclude(site_links__site=site)
    assigned = None
    if request.method == "POST" and "assign_manager" in request.POST:
        assign_form = SiteManagerAssignForm(request.POST)
        assign_form.fields["site"].queryset = Site.objects.filter(id=site.id)
        assign_form.fields["user"].queryset = User.objects.filter(is_active=True, is_superuser=False).exclude(site_links__site=site)
        if assign_form.is_valid():
            user = assign_form.cleaned_data["user"]
            SiteManager.objects.get_or_create(site=site, user=user)
            assigned = user
            # Refresh managers and form
            managers = User.objects.filter(site_links__site=site)
            assign_form = SiteManagerAssignForm(initial={"site": site})
            assign_form.fields["site"].queryset = Site.objects.filter(id=site.id)
            assign_form.fields["user"].queryset = User.objects.filter(is_active=True, is_superuser=False).exclude(site_links__site=site)
    return render(request, "core/superuser/site_detail.html", {"site": site, "managers": managers, "assign_form": assign_form, "assigned": assigned})

@user_passes_test(lambda u: u.is_superuser)
def superuser_users(request):
    user_form = UserCreateForm(request.POST or None)
    created_user = None
    if request.method == "POST" and "create_user" in request.POST and user_form.is_valid():
        user = user_form.save(commit=False)
        user.set_password(user_form.cleaned_data["password"])
        user.save()
        created_user = user
    return render(request, "core/superuser/users.html", {"user_form": user_form, "created_user": created_user})

@user_passes_test(lambda u: u.is_superuser)
def superuser_sites(request):
    from .models import Site
    site_form = SiteCreateForm(request.POST or None)
    created_site = None
    if request.method == "POST" and "create_site" in request.POST and site_form.is_valid():
        created_site = site_form.save()
    # List all sites for the card listing
    sites = Site.objects.all().order_by("name")
    return render(request, "core/superuser/sites.html", {"site_form": site_form, "created_site": created_site, "sites": sites})

@user_passes_test(lambda u: u.is_superuser)
def superuser_assign(request):
    from .models import Site, User, SiteManager
    if request.method == "POST":
        # AJAX assign user to site
        data = json.loads(request.body)
        user_id = int(data["user_id"])
        site_id = int(data["site_id"])
        SiteManager.objects.get_or_create(site_id=site_id, user_id=user_id)
        return JsonResponse({"success": True})
    if request.method == "DELETE":
        # AJAX unassign user from site
        data = json.loads(request.body)
        user_id = int(data["user_id"])
        site_id = int(data["site_id"])
        SiteManager.objects.filter(site_id=site_id, user_id=user_id).delete()
        return JsonResponse({"success": True})
    users = list(User.objects.filter(is_active=True, is_superuser=False).values("id", "username"))
    sites = list(Site.objects.filter(is_active=True).values("id", "name"))
    assignments = list(SiteManager.objects.values("site_id", "user_id"))
    assigned_user_ids = {a["user_id"] for a in assignments}
    unassigned_users = [u for u in users if u["id"] not in assigned_user_ids]
    return render(request, "core/superuser/assign.html", {
        "users": json.dumps(unassigned_users),
        "sites": json.dumps(sites),
        "assignments": json.dumps(assignments),
    })


# Superuser admin panel for user/site management
@user_passes_test(lambda u: u.is_superuser)
def superuser_admin(request):
    site_form = SiteCreateForm(request.POST or None)
    user_form = UserCreateForm(request.POST or None)
    assign_form = SiteManagerAssignForm(request.POST or None)
    created_site = created_user = assigned = None
    if request.method == "POST":
        if "create_site" in request.POST and site_form.is_valid():
            created_site = site_form.save()
        if "create_user" in request.POST and user_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data["password"])
            user.save()
            created_user = user
        if "assign_manager" in request.POST and assign_form.is_valid():
            site = assign_form.cleaned_data["site"]
            user = assign_form.cleaned_data["user"]
            from .models import SiteManager
            SiteManager.objects.get_or_create(site=site, user=user)
            assigned = (site, user)
    context = {
        "site_form": site_form,
        "user_form": user_form,
        "assign_form": assign_form,
        "created_site": created_site,
        "created_user": created_user,
        "assigned": assigned,
    }
    return render(request, "core/superuser_admin.html", context)
def fire_qr_png(request, site_id: int):
    # QR for fire evacuation staff list
    from core.models import Site
    site = Site.objects.get(id=site_id)
    target = request.build_absolute_uri(reverse("public_staff_list", kwargs={"fire_token": site.fire_token}))
    img = qrcode.make(target)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")
import io
import qrcode
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

class LoginView(auth_views.LoginView):
    template_name = "sbadmin/login.html"

class LogoutView(auth_views.LogoutView):
    pass

def qr_png(request, token: str):
    # Public QR image: just render the URL encoded in QR.
    # URL target is /s/<token>/
    target = request.build_absolute_uri(reverse("scan_page", kwargs={"token": token}))
    img = qrcode.make(target)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")

from .forms_manager import MultiTokenRotateForm
from core.models import SiteToken

def rotate_token(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if not user_can_manage_site(request.user, site_id):
        return HttpResponse('Unauthorized', status=403)
    if request.method == "POST":
        form = MultiTokenRotateForm(request.POST, site=site)
        if form.is_valid():
            rotated_tokens = form.save()
            return render(request, "core/token_rotated.html", {"site": site, "rotated_tokens": rotated_tokens})
    else:
        form = MultiTokenRotateForm(site=site)
    return render(request, "core/rotate_token.html", {"site": site, "form": form, "tokens": SiteToken.objects.filter(site=site)})
