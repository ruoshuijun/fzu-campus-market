import os
import uuid
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from core.models import Listing, Reservation


class Command(BaseCommand):
    help = "导入本地演示账号和物品，可重复运行；不会重置已有账号密码或已有物品状态。"

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo 仅允许 DEBUG=1 的本地演示环境")
        User = get_user_model()
        users = {}
        password = os.getenv("DEMO_PASSWORD", "DemoPass123!")
        for username, nickname in [("student1", "卖家同学"), ("student2", "买家同学"), ("student3", "另一位买家"), ("admin", "演示管理员")]:
            user, created = User.objects.get_or_create(username=username, defaults={"first_name": nickname, "is_staff": username == "admin", "is_superuser": username == "admin"})
            if created:
                user.set_password(password)
                user.save()
            users[username] = user
        products = [
            ("高等数学复习资料", "整理好的复习笔记，适合期末查漏补缺。", "12.00", "BOOKS"),
            ("便携无线鼠标", "日常学习使用，功能正常，附收纳袋。", "25.00", "DIGITAL"),
            ("简约桌面台灯", "亮度可调，适合宿舍桌面。", "30.00", "DAILY"),
            ("软件工程教材", "有少量划线，内容完整。", "18.50", "BOOKS"),
            ("羽毛球拍", "入门练习使用，附拍套。", "40.00", "OTHER"),
            ("桌面收纳盒", "毕业整理闲置，干净完整。", "8.00", "DAILY"),
        ]
        for title, description, price, category in products:
            Listing.objects.get_or_create(seller=users["student1"], title=title, defaults={"description": description, "price": Decimal(price), "category": category, "campus": "旗山校区", "meeting_place": "校园公共区域，见面时约定"})
        held, created = Listing.objects.get_or_create(seller=users["student1"], title="演示：已被预订的计算器", defaults={"description": "供成员三开发取消、确认、超时，以及成员四验证隐藏联动。", "price": Decimal("20.00"), "category": "DIGITAL", "meeting_place": "校园公共区域", "status": Listing.Status.RESERVED})
        if created:
            Reservation.objects.create(listing=held, buyer=users["student2"], request_key=uuid.UUID("11111111-1111-4111-8111-111111111111"), expires_at=timezone.now() + timedelta(days=1))
        self.stdout.write(self.style.SUCCESS("演示数据就绪。账号：admin / student1 / student2 / student3；新建账号的默认密码见 README（或 DEMO_PASSWORD）。已有账号和物品保持原样。"))
