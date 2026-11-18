from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.decorators.http import require_POST
from core.models import Listing, ModerationLog
from core.results import Result
from .services import hide_listing


@login_required
def dashboard(request):
    if not request.user.is_staff:
        raise PermissionDenied
    queryset = Listing.objects.select_related("seller").all()
    return render(request, "moderation/dashboard.html", {
        "page_obj": Paginator(queryset, 20).get_page(request.GET.get("page")),
        "logs": ModerationLog.objects.select_related("actor", "listing")[:10],
    })


@require_POST
def hide(request, pk):
    if not request.user.is_authenticated:
        return Result(status=401, code="AUTH_REQUIRED", message="请先登录").response()
    result = hide_listing(actor=request.user, listing_id=pk, reason=request.POST.get("reason", ""))
    if result.code:
        return result.response()
    messages.success(request, "物品已隐藏，相关有效预订已结束。")
    return redirect("moderation:dashboard")
