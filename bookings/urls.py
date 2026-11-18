from django.urls import path
from . import views

app_name = "bookings"
urlpatterns = [
    path("mine/", views.mine, name="mine"),
    path("reserve/<int:listing_id>/", views.reserve, name="reserve"),
    path("<uuid:reservation_id>/cancel/", views.cancel, name="cancel"),
    path("<uuid:reservation_id>/confirm/", views.confirm, name="confirm"),
]
