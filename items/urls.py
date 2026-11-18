from django.urls import path
from . import views

app_name = "items"
urlpatterns = [
    path("", views.listings, name="list"),
    path("new/", views.create, name="create"),
    path("mine/", views.mine, name="mine"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/edit/", views.edit, name="edit"),
    path("<int:pk>/take-off/", views.take_off, name="take_off"),
    path("<int:pk>/relist/", views.relist, name="relist"),
]
