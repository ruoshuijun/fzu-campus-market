from dataclasses import dataclass, field
from django.http import JsonResponse


@dataclass(frozen=True)
class Result:
    """服务正常返回错误结果，避免业务冲突抛异常把到期释放也回滚。"""
    status: int = 200
    data: dict = field(default_factory=dict)
    code: str = ""
    message: str = ""

    def response(self):
        if self.code:
            return JsonResponse({"error": {"code": self.code, "message": self.message}}, status=self.status)
        return JsonResponse({"data": self.data}, status=self.status)


def not_ready():
    return Result(status=501, code="NOT_IMPLEMENTED", message="此模块的业务功能尚待对应成员开发")
