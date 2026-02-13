from django.urls import path
from .views import LoginView, LogoutView, qr_png, fire_qr_png, superuser_admin, superuser_users, superuser_sites, superuser_assign, superuser_user_list, superuser_user_detail, superuser_site_detail, site_settings, rotate_token
from .views_onboarding import onboarding_site, onboarding_manager, onboarding_billing, onboarding_complete

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("qr/<str:token>.png", qr_png, name="qr_png"),
    path("fireqr/<int:site_id>.png", fire_qr_png, name="fire_qr_png"),
    path("superuser-admin/", superuser_admin, name="superuser_admin"),
    path("superuser-admin/users/", superuser_users, name="superuser_users"),
    path("superuser-admin/sites/", superuser_sites, name="superuser_sites"),
    path("superuser-admin/assign/", superuser_assign, name="superuser_assign"),
    path("superuser-admin/user-list/", superuser_user_list, name="superuser_user_list"),
    path("superuser-admin/user/<int:user_id>/", superuser_user_detail, name="superuser_user_detail"),
    path("superuser-admin/site/<int:site_id>/", superuser_site_detail, name="superuser_site_detail"),
    path("site/<int:site_id>/settings/", site_settings, name="site_settings"),
    path("site/<int:site_id>/rotate-token/", rotate_token, name="rotate_token"),
    # Onboarding / public wizard
    path("onboarding/site/", onboarding_site, name="onboarding_site"),
    path("onboarding/manager/", onboarding_manager, name="onboarding_manager"),
    path("onboarding/billing/", onboarding_billing, name="onboarding_billing"),
    path("onboarding/complete/", onboarding_complete, name="onboarding_complete"),
]
