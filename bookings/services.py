"""成员三替换函数体，保留签名与 Result 返回契约。当前不会创建虚假交易。"""
from core.results import not_ready


def reserve(*, buyer, listing_id, request_key):
    return not_ready()


def cancel(*, actor, reservation_id):
    return not_ready()


def confirm(*, actor, reservation_id):
    return not_ready()


def expire_due(*, now=None):
    """实现后返回实际释放数量；当前显式提示未实现，禁止假报零条。"""
    raise NotImplementedError("成员三尚未实现到期回收")
