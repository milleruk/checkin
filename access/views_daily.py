from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, time
from .models import StaffMember, AccessEvent
from core.models import Site

@login_required
def manager_daily_events(request, site_id):
    site = Site.objects.get(id=site_id)
    # Only allow site managers or superusers
    if not (request.user.is_superuser or site.manager_links.filter(user=request.user).exists()):
        return render(request, "sbadmin/no_sites.html")

    # Get date from GET param, default today
    date_str = request.GET.get("date")
    today = timezone.localdate()
    if date_str:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            day = today
    else:
        day = today
    start = datetime.combine(day, time.min, tzinfo=timezone.get_current_timezone())
    end = datetime.combine(day, time.max, tzinfo=timezone.get_current_timezone())

    # Calculate prev/next dates
    from datetime import timedelta
    prev_date = day - timedelta(days=1)
    next_date = day + timedelta(days=1)
    is_today = (day == today)

    # Staff who checked in that day
    staff_in_ids = AccessEvent.objects.filter(site=site, direction=AccessEvent.IN, occurred_at__range=(start, end)).values_list('staff_id', flat=True).distinct()
    staff_in = StaffMember.objects.filter(id__in=staff_in_ids, site=site)
    # All events for that day
    events = AccessEvent.objects.filter(site=site, occurred_at__range=(start, end)).select_related('staff').order_by('occurred_at')

    from core.perms import site_ids_for_user
    # from core.models import Site  # Remove duplicate import
    site_ids = list(site_ids_for_user(request.user))
    sites = Site.objects.filter(id__in=site_ids).order_by("name")
    return render(request, "manager/daily_events.html", {
        "site": site,
        "sites": sites,
        "date": day,
        "today": today,
        "prev_date": prev_date,
        "next_date": next_date,
        "is_today": is_today,
        "staff_in": staff_in,
        "events": events,
    })
