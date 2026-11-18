"""冻结的公共数据结构。成员一至三只导入，不各自创建同名模型。"""
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q


class Listing(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "可预订"
        RESERVED = "RESERVED", "已预订"
        COMPLETED = "COMPLETED", "已完成"
        OFF_SHELF = "OFF_SHELF", "已下架"
        HIDDEN = "HIDDEN", "已隐藏"

    class Category(models.TextChoices):
        BOOKS = "BOOKS", "书籍资料"
        DIGITAL = "DIGITAL", "数码用品"
        DAILY = "DAILY", "生活用品"
        OTHER = "OTHER", "其他"

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="listings")
    title = models.CharField(max_length=60)
    description = models.TextField(max_length=1000)
    price = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("99999.99"))])
    category = models.CharField(max_length=16, choices=Category.choices, default=Category.OTHER)
    campus = models.CharField(max_length=40, default="旗山校区")
    meeting_place = models.CharField(max_length=100)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["status", "created_at"]), models.Index(fields=["seller", "created_at"])]
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0) & Q(price__lte=Decimal("99999.99")), name="listing_price_range"),
            models.CheckConstraint(condition=Q(status__in=["AVAILABLE", "RESERVED", "COMPLETED", "OFF_SHELF", "HIDDEN"]), name="listing_valid_status"),
            models.CheckConstraint(condition=Q(category__in=["BOOKS", "DIGITAL", "DAILY", "OTHER"]), name="listing_valid_category"),
        ]

    def __str__(self):
        return self.title


class Reservation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "进行中"
        CANCELLED = "CANCELLED", "已取消"
        EXPIRED = "EXPIRED", "已过期"
        COMPLETED = "COMPLETED", "已完成"
        VOID = "VOID", "已终止"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name="reservations")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservations")
    request_key = models.UUIDField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    expires_at = models.DateTimeField()
    buyer_confirmed_at = models.DateTimeField(null=True, blank=True)
    seller_confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "expires_at"])]
        constraints = [
            models.UniqueConstraint(fields=["listing"], condition=Q(status="ACTIVE"), name="one_active_reservation_per_listing"),
            models.UniqueConstraint(fields=["buyer", "request_key"], name="unique_buyer_request_key"),
            models.CheckConstraint(condition=Q(status__in=["ACTIVE", "CANCELLED", "EXPIRED", "COMPLETED", "VOID"]), name="reservation_valid_status"),
            models.CheckConstraint(condition=~Q(status="COMPLETED") | (Q(buyer_confirmed_at__isnull=False) & Q(seller_confirmed_at__isnull=False)), name="completed_has_both_confirmations"),
            models.CheckConstraint(condition=Q(expires_at__gt=F("created_at")), name="reservation_expiry_after_creation"),
        ]


class ModerationLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT)
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
