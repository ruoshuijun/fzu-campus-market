"""Common functional review for both experiment variants; run outside the coding sessions."""
import io
import json
import os
import sys
import uuid
from datetime import timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

group = sys.argv[1]
snapshot = Path(sys.argv[2]).resolve()
os.chdir(snapshot)
sys.path.insert(0, str(snapshot))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DB_ENGINE"] = "sqlite"
import django
from django.conf import settings
settings.DATABASES["default"]["NAME"] = ":memory:"
django.setup()
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.utils import timezone
from core.models import Listing, Reservation


class Controls(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.has_selected = False
        self.has_status_control = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "a" and "href" in attrs:
            self.links.append(parse_qs(urlsplit(attrs["href"]).query))
        if attrs.get("name") == "status" or "status" in parse_qs(urlsplit(attrs.get("href", "")).query):
            self.has_status_control = True
        selected_value = attrs.get("value") == desired and ("selected" in attrs or "checked" in attrs)
        selected_link = (
            parse_qs(urlsplit(attrs.get("href", "")).query).get("status") == [desired]
            and attrs.get("aria-current") in ("true", "page")
        )
        if selected_value or selected_link:
            self.has_selected = True


def make_record(title, owner, filtered):
    seller = owner if group == "X-bmad" else other
    target = Listing.objects.create(
        seller=seller, title=title, description="experiment fixture",
        price="10.00", meeting_place="校园公共区域",
        status=("AVAILABLE" if filtered else "OFF_SHELF") if group == "X-bmad" else "AVAILABLE",
    )
    if group == "Y-direct":
        Reservation.objects.create(
            listing=target, buyer=owner, request_key=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(hours=1),
            status="ACTIVE" if filtered else "CANCELLED",
        )


call_command("migrate", verbosity=0, interactive=False)
User = get_user_model()
mine = User.objects.create_user(username="experiment_mine")
other = User.objects.create_user(username="experiment_other")
my_titles = [f"Experiment row {i:03d}" for i in range(43)]
other_title = "EXPERIMENT OUTSIDE ACCOUNT"
for i, title in enumerate(my_titles):
    make_record(title, mine, i < 23)
make_record(other_title, other, True)
row_counts = (Listing.objects.count(), Reservation.objects.count())
route, desired = ("/items/mine/", "AVAILABLE") if group == "X-bmad" else ("/bookings/mine/", "ACTIVE")
empty_status = "HIDDEN" if group == "X-bmad" else "VOID"
c = Client()


def page(**params):
    response = c.get(route, params)
    assert response.status_code == 200, f"HTTP {response.status_code}"
    return response.content.decode("utf-8")


def asserting_rows(body, expected):
    row_index = {title: body.find(title) for title in my_titles}
    visible = sorted((title for title in my_titles if row_index[title] >= 0), key=row_index.get)
    assert visible == expected, f"expected {len(expected)} rows in order, found {len(visible)}"
    assert other_title not in body, "another user's row was shown"


def check_redirect():
    response = Client().get(route)
    assert response.status_code == 302 and "/accounts/login/" in response.get("Location", "")


c.force_login(mine)


def check_default():
    asserting_rows(page(), my_titles[::-1][:20])


def check_filter():
    body = page(status=desired)
    asserting_rows(body, my_titles[:23][::-1][:20])
    controls = Controls()
    controls.feed(body)
    assert controls.has_status_control, "no filter control with name=status"
    assert controls.has_selected, "chosen status is not selected in the filter control"


def check_next_link():
    controls = Controls()
    controls.feed(page(status=desired))
    assert any(link.get("page") == ["2"] and link.get("status") == [desired] for link in controls.links), "next link does not keep status"
    asserting_rows(page(status=desired, page=2), my_titles[:23][::-1][20:])


def check_invalid():
    asserting_rows(page(status="NOT_A_STATUS", page="junk"), my_titles[::-1][:20])
    asserting_rows(page(status=desired, page="9999"), my_titles[:23][::-1][20:])


def check_empty():
    body = page(status=empty_status)
    asserting_rows(body, [])
    assert any(label in body for label in ("暂无", "没有", "无记录", "未找到", "无符合"))


def check_read_only():
    assert row_counts == (Listing.objects.count(), Reservation.objects.count())


def check_settings():
    call_command("check", verbosity=0, stdout=io.StringIO())
    call_command("makemigrations", check=True, dry_run=True, verbosity=0, stdout=io.StringIO())


checks = [
    ("anonymous_login_redirect", check_redirect),
    ("owner_filter_and_default_page", check_default),
    ("status_filter_and_selected_value", check_filter),
    ("second_page_and_filter_retention", check_next_link),
    ("safe_invalid_parameters", check_invalid),
    ("empty_result_hint", check_empty),
    ("read_does_not_create_records", check_read_only),
    ("django_and_migration_check", check_settings),
]
results = []
for name, check in checks:
    try:
        check()
        results.append({"check": name, "passed": True})
    except (Exception, SystemExit) as exc:
        results.append({"check": name, "passed": False, "detail": str(exc) or type(exc).__name__})
print(json.dumps({"group": group, "checks": results}, indent=2, ensure_ascii=True))
sys.exit(0 if all(result["passed"] for result in results) else 1)
