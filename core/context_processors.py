from core.models import Site

def site_context(request):
    user = request.user
    sites = []
    current_site = None
    if user.is_authenticated:
        # Example: get all sites user can access (customize as needed)
        if hasattr(user, 'site_managers'):
            sites = [link.site for link in user.site_managers.select_related('site').all()]
        else:
            sites = list(Site.objects.all())
        # Try to get current site from session
        site_id = request.session.get('site_id')
        if site_id:
            try:
                current_site = Site.objects.get(id=site_id)
            except Site.DoesNotExist:
                current_site = sites[0] if sites else None
        elif sites:
            current_site = sites[0]
            request.session['site_id'] = current_site.id
    return {
        'sites': sites,
        'site': current_site,
    }
