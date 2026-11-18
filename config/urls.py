from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="items:list", permanent=False)),
    path("accounts/", include("accounts.urls")),
    path("items/", include("items.urls")),
    path("bookings/", include("bookings.urls")),
    path("moderation/", include("moderation.urls")),
    path("django-admin/", admin.site.urls),
]
