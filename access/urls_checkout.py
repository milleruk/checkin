from django.urls import path
from . import views_checkout, views
from . import views_checkout_associated

urlpatterns = [
    path('visitor_checkout/<str:token>/<str:checkout_token>/', views_checkout.visitor_self_checkout, name='visitor_self_checkout'),
    path('visitor_checkin_complete/<str:token>/<str:checkout_token>/', views.visitor_checkin_complete, name='visitor_checkin_complete'),
    path('contractor_checkout/<str:token>/<str:checkout_token>/', views_checkout.contractor_self_checkout, name='contractor_self_checkout'),
    path('contractor_checkin_complete/<str:token>/<str:checkout_token>/', views.contractor_checkin_complete, name='contractor_checkin_complete'),
    path('associated_staff_checkout/<str:token>/<str:checkout_token>/', views_checkout_associated.associated_staff_self_checkout, name='associated_staff_self_checkout'),
]
