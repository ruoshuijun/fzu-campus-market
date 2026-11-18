from django.core.management.base import BaseCommand, CommandError
from bookings.services import expire_due


class Command(BaseCommand):
    help = "回收超时预订（服务待成员三实现）"

    def handle(self, *args, **options):
        try:
            count = expire_due()
        except NotImplementedError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"已释放 {count} 条到期预订"))
