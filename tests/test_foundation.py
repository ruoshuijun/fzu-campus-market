"""成员四维护的公共基线回归。业务扩展测试由各成员放自己模块。"""
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO
from threading import Barrier
from unittest import skipUnless
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from core.locking import lock_listing, release_if_expired
from core.models import Listing, ModerationLog, Reservation
from moderation.services import hide_listing


class FixtureMixin:
    def setUp(self):
        User = get_user_model()
        self.seller = User.objects.create_user(username="seller", password="ExamplePass123!")
        self.buyer = User.objects.create_user(username="buyer", password="ExamplePass123!")
        self.admin = User.objects.create_user(username="reviewer", password="ExamplePass123!", is_staff=True)
        self.item = Listing.objects.create(seller=self.seller, title="测试物品", description="说明", price="12.50", meeting_place="公共区域")

    def reserve_fixture(self, **overrides):
        self.item.status = Listing.Status.RESERVED
        self.item.save()
        fields = {"listing": self.item, "buyer": self.buyer, "request_key": uuid.uuid4(), "expires_at": timezone.now() + timedelta(hours=2)}
        fields.update(overrides)
        return Reservation.objects.create(**fields)


class ModelContractTests(FixtureMixin, TestCase):
    def test_single_active_reservation_is_database_constraint(self):
        self.reserve_fixture()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.reserve_fixture()

    def test_terminal_history_does_not_block_new_active(self):
        self.reserve_fixture(status=Reservation.Status.CANCELLED)
        self.reserve_fixture()
        self.assertEqual(Reservation.objects.filter(status="ACTIVE").count(), 1)

    def test_request_key_unique_per_buyer(self):
        original = self.reserve_fixture(status=Reservation.Status.CANCELLED)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.reserve_fixture(request_key=original.request_key)

    def test_price_cannot_be_negative(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Listing.objects.filter(pk=self.item.pk).update(price="-1.00")

    def test_invalid_listing_status_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Listing.objects.filter(pk=self.item.pk).update(status="FAKE")

    def test_completed_requires_both_confirmation_times(self):
        reservation = self.reserve_fixture()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reservation.objects.filter(pk=reservation.pk).update(status="COMPLETED")

    def test_expiry_cannot_precede_creation(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.reserve_fixture(expires_at=timezone.now() - timedelta(days=1))


class LockingTests(FixtureMixin, TestCase):
    def test_expiry_boundary_and_release_are_idempotent(self):
        reservation = self.reserve_fixture()
        with transaction.atomic():
            state = lock_listing(self.item.pk)
            self.assertTrue(release_if_expired(state, now=reservation.expires_at))
            self.assertFalse(release_if_expired(state, now=reservation.expires_at))
        reservation.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(reservation.status, "EXPIRED")
        self.assertEqual(self.item.status, "AVAILABLE")

    def test_before_expiry_does_not_release(self):
        reservation = self.reserve_fixture()
        with transaction.atomic():
            self.assertFalse(release_if_expired(lock_listing(self.item.pk), now=reservation.expires_at - timedelta(microseconds=1)))


class ModerationTests(FixtureMixin, TestCase):
    def test_hide_available_records_reason(self):
        result = hide_listing(actor=self.admin, listing_id=self.item.pk, reason=" 不适宜发布 ")
        self.assertEqual(result.status, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "HIDDEN")
        self.assertEqual(ModerationLog.objects.get().reason, "不适宜发布")

    def test_hide_active_reservation_voids_it(self):
        reservation = self.reserve_fixture()
        hide_listing(actor=self.admin, listing_id=self.item.pk, reason="违规")
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, "VOID")
        self.assertFalse(Reservation.objects.filter(status="ACTIVE").exists())

    def test_hide_expired_reservation_preserves_expired_reason(self):
        reservation = self.reserve_fixture()
        Reservation.objects.filter(pk=reservation.pk).update(expires_at=timezone.now() - timedelta(seconds=1), created_at=timezone.now() - timedelta(hours=1))
        hide_listing(actor=self.admin, listing_id=self.item.pk, reason="违规")
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, "EXPIRED")
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "HIDDEN")

    def test_student_cannot_hide_or_release_expired_data(self):
        reservation = self.reserve_fixture()
        Reservation.objects.filter(pk=reservation.pk).update(expires_at=timezone.now() - timedelta(seconds=1), created_at=timezone.now() - timedelta(hours=1))
        self.assertEqual(hide_listing(actor=self.buyer, listing_id=self.item.pk, reason="违规").status, 403)
        reservation.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(reservation.status, "ACTIVE")
        self.assertEqual(self.item.status, "RESERVED")
        self.assertFalse(ModerationLog.objects.exists())

    def test_hide_is_idempotent(self):
        for _ in range(2):
            hide_listing(actor=self.admin, listing_id=self.item.pk, reason="违规")
        self.assertEqual(ModerationLog.objects.count(), 1)

    def test_completed_trade_is_immutable(self):
        self.item.status = "COMPLETED"
        self.item.save()
        self.assertEqual(hide_listing(actor=self.admin, listing_id=self.item.pk, reason="违规").status, 409)
        self.assertFalse(ModerationLog.objects.exists())

    def test_empty_or_long_reason_has_no_side_effect(self):
        for reason in [" ", "字" * 201]:
            self.assertEqual(hide_listing(actor=self.admin, listing_id=self.item.pk, reason=reason).status, 422)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "AVAILABLE")

    def test_missing_item_returns_404(self):
        self.assertEqual(hide_listing(actor=self.admin, listing_id=99999, reason="违规").status, 404)

    def test_inactive_staff_is_denied(self):
        self.admin.is_active = False
        self.assertEqual(hide_listing(actor=self.admin, listing_id=self.item.pk, reason="违规").status, 403)


class PageAndAuthTests(FixtureMixin, TestCase):
    def test_public_pages_and_static_template(self):
        response = self.client.get(reverse("items:list"))
        self.assertContains(response, "测试物品")
        self.assertContains(response, "/static/css/site.css")
        self.assertEqual(self.client.get(reverse("items:detail", args=[self.item.pk])).status_code, 200)

    def test_hidden_not_public(self):
        self.item.status = "HIDDEN"
        self.item.save()
        self.assertNotContains(self.client.get(reverse("items:list")), "测试物品")
        self.assertEqual(self.client.get(reverse("items:detail", args=[self.item.pk])).status_code, 404)

    def test_description_is_html_escaped(self):
        self.item.description = "<script>alert('x')</script>"
        self.item.save()
        response = self.client.get(reverse("items:detail", args=[self.item.pk]))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert")

    def test_login_and_logout(self):
        self.assertTrue(self.client.login(username="seller", password="ExamplePass123!"))
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 200)
        self.client.post(reverse("accounts:logout"))
        self.assertEqual(self.client.get(reverse("accounts:profile")).status_code, 302)

    def test_bad_password_does_not_login(self):
        self.assertFalse(self.client.login(username="seller", password="wrong"))

    def test_student_cannot_view_dashboard(self):
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse("moderation:dashboard")).status_code, 403)

    def test_staff_dashboard_and_hide_form(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("moderation:dashboard")).status_code, 200)
        self.assertEqual(self.client.post(reverse("moderation:hide", args=[self.item.pk]), {"reason": "违规"}).status_code, 302)

    def test_moderation_requires_post_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        url = reverse("moderation:hide", args=[self.item.pk])
        self.assertEqual(client.get(url).status_code, 405)
        self.assertEqual(client.post(url, {"reason": "违规"}).status_code, 403)

    def test_booking_write_requires_auth(self):
        response = self.client.post(reverse("bookings:reserve", args=[self.item.pk]), {"request_key": str(uuid.uuid4())})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "AUTH_REQUIRED")

    def test_booking_requires_post(self):
        self.assertEqual(self.client.get(reverse("bookings:reserve", args=[self.item.pk])).status_code, 405)


@override_settings(DEBUG=True)
class SeedTests(TestCase):
    @override_settings(DEBUG=False)
    def test_demo_seed_refuses_non_debug_environment(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo", stdout=StringIO())

    def test_seed_repeat_preserves_password_and_moderated_state(self):
        output = StringIO()
        call_command("seed_demo", stdout=output)
        user = get_user_model().objects.get(username="student1")
        password_hash = user.password
        item = Listing.objects.first()
        item.status = "HIDDEN"
        item.save()
        count = Listing.objects.count()
        call_command("seed_demo", stdout=output)
        user.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(user.password, password_hash)
        self.assertEqual(item.status, "HIDDEN")
        self.assertEqual(Listing.objects.count(), count)
        self.assertEqual(Reservation.objects.count(), 1)


class TransactionBoundaryTests(TransactionTestCase):
    def test_lock_requires_explicit_transaction(self):
        with self.assertRaises(RuntimeError):
            lock_listing(1)


@skipUnless(connection.vendor == "postgresql", "真实并发需 PostgreSQL；SQLite 不代表行锁验证")
class PostgresModerationRaceTests(FixtureMixin, TransactionTestCase):
    def test_parallel_hide_creates_one_log_and_no_active(self):
        self.reserve_fixture()
        barrier = Barrier(4)
        actor_id, item_id = self.admin.pk, self.item.pk

        def work():
            close_old_connections()
            try:
                actor = get_user_model().objects.get(pk=actor_id)
                barrier.wait(timeout=10)
                return hide_listing(actor=actor, listing_id=item_id, reason="并发审核").status
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: work(), range(4)))
        self.assertEqual(results, [200] * 4)
        self.assertEqual(ModerationLog.objects.count(), 1)
        self.assertFalse(Reservation.objects.filter(status="ACTIVE").exists())
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "HIDDEN")
