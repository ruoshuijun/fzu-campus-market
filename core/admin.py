from django.contrib import admin
from .models import Listing, ModerationLog, Reservation


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Listing)
class ListingAdmin(ReadOnlyAdmin):
    list_display = ("id", "title", "seller", "status", "price")
    list_filter = ("status",)


@admin.register(Reservation)
class ReservationAdmin(ReadOnlyAdmin):
    list_display = ("id", "listing", "buyer", "status", "expires_at")


@admin.register(ModerationLog)
class LogAdmin(ReadOnlyAdmin):
    list_display = ("actor", "listing", "reason", "created_at")
