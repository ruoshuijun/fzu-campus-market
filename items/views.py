"""成员二扩展。已有可运行的只读页面；发布等写操作尚未实现。"""
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from core.models import Listing
from core.results import not_ready


def listings(request):
    queryset = Listing.objects.filter(status__in=[Listing.Status.AVAILABLE, Listing.Status.RESERVED])
    return render(request, "items/list.html", {"page_obj": Paginator(queryset.select_related("seller"), 20).get_page(request.GET.get("page"))})


def detail(request, pk):
    listing = get_object_or_404(Listing.objects.select_related("seller").filter(status__in=[Listing.Status.AVAILABLE, Listing.Status.RESERVED, Listing.Status.COMPLETED]), pk=pk)
    return render(request, "items/detail.html", {"listing": listing})


@login_required
def create(request):
    return render(request, "items/pending.html", {"heading": "发布闲置"})


@login_required
def mine(request):
    return render(request, "items/mine.html", {"listings": Listing.objects.filter(seller=request.user)})


@login_required
def edit(request, pk):
    return render(request, "items/pending.html", {"heading": "编辑闲置"})


@require_POST
@login_required
def take_off(request, pk):
    return not_ready().response()


@require_POST
@login_required
def relist(request, pk):
    return not_ready().response()
