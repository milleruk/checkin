from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib import messages

from .forms import SiteCreateForm, OnboardingManagerForm
from .models import Site, SiteManager


def onboarding_site(request):
    """Step 1: collect basic Site information."""
    if request.method == "POST":
        form = SiteCreateForm(request.POST)
        if form.is_valid():
            # Save site form data in session for later commit
            request.session['onboard_site_data'] = form.cleaned_data
            return redirect('onboarding_manager')
    else:
        form = SiteCreateForm()
    return render(request, 'onboarding/site.html', {'form': form})


def onboarding_manager(request):
    """Step 2: collect initial manager account info."""
    if 'onboard_site_data' not in request.session:
        return redirect('onboarding_site')
    if request.method == "POST":
        form = OnboardingManagerForm(request.POST)
        if form.is_valid():
            # store manager data and move to billing/summary
            request.session['onboard_manager_data'] = {
                'email': form.cleaned_data['email'],
                'first_name': form.cleaned_data.get('first_name', ''),
                'last_name': form.cleaned_data.get('last_name', ''),
                'password': form.cleaned_data['password'],
            }
            return redirect('onboarding_billing')
    else:
        form = OnboardingManagerForm()
    return render(request, 'onboarding/manager.html', {'form': form})


def onboarding_billing(request):
    """Step 3: optional billing/plan selection (placeholder)."""
    if 'onboard_site_data' not in request.session or 'onboard_manager_data' not in request.session:
        return redirect('onboarding_site')
    if request.method == "POST":
        # For now we don't implement billing; proceed to finalization
        return redirect('onboarding_complete')
    return render(request, 'onboarding/billing.html', {})


def onboarding_complete(request):
    """Finalize creation of Site, User and SiteManager in an atomic transaction."""
    site_data = request.session.get('onboard_site_data')
    manager_data = request.session.get('onboard_manager_data')
    if not site_data or not manager_data:
        messages.error(request, "Incomplete onboarding data; please start again.")
        return redirect('onboarding_site')

    # Re-validate and create objects atomically
    site_form = SiteCreateForm(site_data)
    user_form = UserCreateForm({
        'email': manager_data['email'],
        'first_name': manager_data.get('first_name', ''),
        'last_name': manager_data.get('last_name', ''),
        'password': manager_data['password'],
        'is_active': True,
    })
    if not site_form.is_valid():
        messages.error(request, "Site data invalid; please correct and retry.")
        return redirect('onboarding_site')
    if not user_form.is_valid():
        messages.error(request, "Manager account data invalid; please correct and retry.")
        return redirect('onboarding_manager')

    with transaction.atomic():
        site = site_form.save()
        # Create user
        user = user_form.save(commit=False)
        user.username = user.email
        user.is_staff = True
        user.save()
        # Link manager
        SiteManager.objects.get_or_create(site=site, user=user)

    # Set session to the new site so manager lands in correct context
    request.session['site_id'] = site.id

    # Clear onboarding session keys
    for key in ('onboard_site_data', 'onboard_manager_data'):
        if key in request.session:
            del request.session[key]

    return render(request, 'onboarding/complete.html', {'site': site, 'user': user})
