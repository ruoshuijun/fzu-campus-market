"""共同锁协议。调用方必须先做身份检查，再在 atomic 内调用。"""
from dataclasses import dataclass
from django.db import connection
from django.utils import timezone
from .models import Listing, Reservation


@dataclass
class LockedListing:
    listing: Listing
    active: Reservation | None


def lock_listing(listing_id):
    if not connection.in_atomic_block:
        raise RuntimeError("lock_listing 必须在 transaction.atomic 内调用")
    listing = Listing.objects.select_for_update().get(pk=listing_id)
    active = Reservation.objects.select_for_update().filter(listing=listing, status=Reservation.Status.ACTIVE).first()
    return LockedListing(listing=listing, active=active)


def release_if_expired(state, *, now=None):
    """调用方在锁内复核权限后调用；返回是否释放，不自行开事务。"""
    if not connection.in_atomic_block:
        raise RuntimeError("release_if_expired 必须在 transaction.atomic 内调用")
    now = now or timezone.now()
    if state.active and state.active.expires_at <= now:
        state.active.status = Reservation.Status.EXPIRED
        state.active.save(update_fields=["status", "updated_at"])
        if state.listing.status == Listing.Status.RESERVED:
            state.listing.status = Listing.Status.AVAILABLE
            state.listing.save(update_fields=["status", "updated_at"])
        state.active = None
        return True
    return False
