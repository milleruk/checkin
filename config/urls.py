
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf.urls import handler404

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="manager_dashboard", permanent=False)),
    path("", include("core.urls")),
    path("", include("access.urls")),
    path("", include("access.urls_checkout")),
]

# Use the default Django 404 view, which will render templates/404.html
handler404 = "django.views.defaults.page_not_found"
