
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf.urls import handler404

urlpatterns = [
    path("admin/", admin.site.urls),
    # Landing page
    path("", TemplateView.as_view(template_name="landing.html"), name="landing"),
    path("", include("core.urls")),
    path("", include("access.urls")),
    path("", include("access.urls_checkout")),
]

# Use the default Django 404 view, which will render templates/404.html
handler404 = "django.views.defaults.page_not_found"
