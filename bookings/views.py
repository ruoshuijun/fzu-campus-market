import uuid
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_POST
from core.models import Reservation
from core.results import Result
from . import services


@login_required
def mine(request):
    return render(request, "bookings/mine.html", {"reservations": Reservation.objects.filter(buyer=request.user).select_related("listing")})


@require_POST
def reserve(request, listing_id):
    if not request.user.is_authenticated:
        return Result(status=401, code="AUTH_REQUIRED", message="请先登录").response()
    try:
        key = uuid.UUID(request.POST.get("request_key", ""))
    except (ValueError, TypeError, AttributeError):
        return Result(status=422, code="VALIDATION_ERROR", message="request_key 必须为 UUID").response()
    return services.reserve(buyer=request.user, listing_id=listing_id, request_key=key).response()


@require_POST
def cancel(request, reservation_id):
    if not request.user.is_authenticated:
        return Result(status=401, code="AUTH_REQUIRED", message="请先登录").response()
    return services.cancel(actor=request.user, reservation_id=reservation_id).response()


@require_POST
def confirm(request, reservation_id):
    if not request.user.is_authenticated:
        return Result(status=401, code="AUTH_REQUIRED", message="请先登录").response()
    return services.confirm(actor=request.user, reservation_id=reservation_id).response()
