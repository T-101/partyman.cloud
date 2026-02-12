from datetime import date, timedelta

from django.test import RequestFactory, TestCase
from django.utils import timezone
from django.db.models.signals import pre_save

from request.models import CloudflareZone, Request, Email
from request.views import ActivationListView
from request.signals import prepare_request_received_emails, send_email


class ActivationListViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        pre_save.disconnect(prepare_request_received_emails, sender=Request)
        pre_save.disconnect(send_email, sender=Email)

    @classmethod
    def tearDownClass(cls):
        pre_save.connect(prepare_request_received_emails, sender=Request)
        pre_save.connect(send_email, sender=Email)
        super().tearDownClass()

    def setUp(self):
        self.factory = RequestFactory()
        self.cloudflare_zone = CloudflareZone.objects.create(
            name="example.com",
            cloudflare_id="zone-1",
            public=True,
            visible=True
        )

    def create_request(self, domain, party_start, activated=None, deactivated=None):
        return Request.objects.create(
            party_name=f"Party {domain}",
            contact_email=f"{domain}@example.com",
            party_start=party_start,
            party_end=party_start + timedelta(days=2),
            inception_date=party_start - timedelta(days=14),
            domain=domain,
            cloudflare_zone=self.cloudflare_zone,
            activated=activated,
            deactivated=deactivated
        )

    def _get_queryset_ids(self):
        request = self.factory.get("/activation/")
        view = ActivationListView()
        view.request = request
        return list(view.get_queryset().values_list("id", flat=True))

    def test_get_queryset_orders_active_requests_first_then_party_start_desc(self):
        now = timezone.now()
        active_newer = self.create_request(
            domain="active-newer",
            party_start=date(2025, 6, 1),
            activated=now - timedelta(days=2),
            deactivated=None,
        )
        active_older = self.create_request(
            domain="active-older",
            party_start=date(2024, 6, 1),
            activated=now - timedelta(days=3),
            deactivated=None,
        )
        deactivated_newest = self.create_request(
            domain="deactivated-newest",
            party_start=date(2026, 1, 1),
            activated=now - timedelta(days=10),
            deactivated=now - timedelta(days=1),
        )
        never_activated = self.create_request(
            domain="never-activated",
            party_start=date(2023, 1, 1),
        )

        ordered_ids = self._get_queryset_ids()

        self.assertEqual(
            ordered_ids,
            [
                active_newer.id,
                active_older.id,
                deactivated_newest.id,
                never_activated.id,
            ],
        )

    def test_activation_list_view_returns_http_200(self):
        self.create_request(
            domain="smoke",
            party_start=date(2025, 1, 1),
        )

        request = self.factory.get("/activation/")
        response = ActivationListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
