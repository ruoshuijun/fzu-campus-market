"""成员一扩展：注册和个人资料；基础登录/退出已由 Django 提供。"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def register(request):
    return render(request, "accounts/register.html")


@login_required
def profile(request):
    return render(request, "accounts/profile.html")
