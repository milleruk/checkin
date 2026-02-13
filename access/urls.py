
from django.urls import path, include
from . import views
from . import views_daily

urlpatterns = [
    # staff scan
    path("s/<str:token>/", views.scan_page, name="scan_page"),
    path("s/<str:token>/resolve/", views.scan_resolve_pin, name="scan_resolve_pin"),
    path("s/<str:token>/confirm/", views.scan_confirm, name="scan_confirm"),

    # manager
    path("manager/", views.manager_dashboard, name="manager_dashboard"),
    path("manager/<int:site_id>/audit/", views.manager_audit, name="manager_audit"),
    path("manager/<int:site_id>/staff/", views.manager_staff, name="manager_staff"),
    path("manager/<int:site_id>/staff/<int:staff_id>/", views.manager_staff_detail, name="manager_staff_detail"),

    path("manager/<int:site_id>/qr/", views.manager_qr, name="manager_qr"),
    path("manager/<int:site_id>/daily/", views_daily.manager_daily_events, name="manager_daily_events"),

    # public fire evacuation staff list
    path("fire/<str:fire_token>/", views.public_staff_list, name="public_staff_list"),

    # Portal views by SiteToken
        path("manager/profile/", views.manager_profile, name="manager_profile"),
    path("portal/public/<str:token>/", views.portal_public, name="portal_public"),
    path("portal/staff/<str:token>/", views.portal_staff, name="portal_staff"),
    path("portal/keypad/<str:token>/", views.portal_keypad, name="portal_keypad"),
    path("portal/fire/<str:token>/", views.portal_fire, name="portal_fire"),

    # Visitor/Contractor/Associated Staff sign-in
    path("portal/visitor_signin/<str:token>/", views.visitor_signin, name="visitor_signin"),
    path("portal/contractor_signin/<str:token>/", views.contractor_signin, name="contractor_signin"),
    path("portal/associated_staff_signin/<str:token>/", views.associated_staff_signin, name="associated_staff_signin"),
    path("portal/associated_staff_checkin_complete/<str:token>/<str:checkout_token>/", views.associated_staff_checkin_complete, name="associated_staff_checkin_complete"),
    # Self-checkout URLs
    path("", include("access.urls_checkout")),
]
