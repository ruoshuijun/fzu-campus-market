from django.db import transaction
from core.locking import lock_listing, release_if_expired
from core.models import Listing, ModerationLog, Reservation
from core.results import Result


def hide_listing(*, actor, listing_id, reason):
    if not actor.is_authenticated or not actor.is_active or not actor.is_staff:
        return Result(status=403, code="FORBIDDEN", message="仅管理员可隐藏物品")
    reason = reason.strip()
    if not reason or len(reason) > 200:
        return Result(status=422, code="VALIDATION_ERROR", message="请填写 1—200 字隐藏原因")
    with transaction.atomic():
        try:
            state = lock_listing(listing_id)
        except Listing.DoesNotExist:
            return Result(status=404, code="NOT_FOUND", message="物品不存在")
        item = state.listing
        if item.status == Listing.Status.HIDDEN:
            return Result(data={"listing_id": item.pk, "status": item.status})
        if item.status == Listing.Status.COMPLETED:
            return Result(status=409, code="STATE_CONFLICT", message="已完成的交易不能隐藏")
        release_if_expired(state)
        if state.active:
            state.active.status = Reservation.Status.VOID
            state.active.save(update_fields=["status", "updated_at"])
        item.status = Listing.Status.HIDDEN
        item.save(update_fields=["status", "updated_at"])
        ModerationLog.objects.create(actor=actor, listing=item, reason=reason)
        return Result(data={"listing_id": item.pk, "status": item.status})
