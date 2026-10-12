"""Account reporting must preserve attribution and enforce staff access."""

# Django
from django.urls import reverse
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership

# AA SRP
from aasrp.models import SrpLink, SrpRequest
from aasrp.tests import BaseTestCase
from aasrp.tests.utils import create_fake_user


class TestAccountHistory(BaseTestCase):
    def setUp(self):
        self.staff = create_fake_user(
            910001,
            "Report Staff",
            permissions=["aasrp.basic_access", "aasrp.manage_srp_requests"],
        )
        self.member = create_fake_user(
            910002, "Report Main", permissions=["aasrp.basic_access"]
        )
        self.other = create_fake_user(910003, "Report Alt")
        self.alt = self.other.profile.main_character
        self.other.profile.main_character = None
        self.other.profile.save()
        CharacterOwnership.objects.filter(character=self.alt).update(user=self.member)
        self.link = SrpLink.objects.create(
            srp_name="Report fleet", fleet_time=timezone.now()
        )
        for character, status, amount in [
            (self.member.profile.main_character, SrpRequest.Status.APPROVED, 100),
            (self.alt, SrpRequest.Status.APPROVED, 200),
            (self.alt, SrpRequest.Status.PENDING, 400),
            (self.alt, SrpRequest.Status.REJECTED, 800),
        ]:
            SrpRequest.objects.create(
                creator=self.member,
                character=character,
                srp_link=self.link,
                request_status=status,
                payout_amount=amount,
            )
        SrpRequest.objects.create(
            creator=self.other,
            character=self.alt,
            srp_link=self.link,
            request_status=SrpRequest.Status.APPROVED,
            payout_amount=1600,
        )

    def test_member_and_anonymous_cannot_access_search_or_detail(self):
        for user in [None, self.member]:
            if user:
                self.client.force_login(user)
            for url in [
                reverse("aasrp:account_search"),
                reverse("aasrp:account_history", args=[self.member.pk]),
            ]:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_search_by_main_alt_and_username(self):
        self.client.force_login(self.staff)
        for query in ["Report Main", "Report Alt", self.member.username]:
            response = self.client.get(reverse("aasrp:account_search"), {"q": query})
            rows = [
                row
                for row in response.context["accounts"]
                if row["user"].pk == self.member.pk
            ]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["total"], 300)

    def test_history_uses_creator_and_counts_only_approved(self):
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse("aasrp:account_history", args=[self.member.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["approved_total"], 300)
        self.assertEqual(response.context["history"].paginator.count, 4)
        self.assertEqual(response.context["characters"].count(), 2)

    def test_unknown_account_is_404(self):
        self.client.force_login(self.staff)
        self.assertEqual(
            self.client.get(
                reverse("aasrp:account_history", args=[999999])
            ).status_code,
            404,
        )

    def test_empty_search_and_unmatched_search(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("aasrp:account_search"))
        self.assertNotIn("accounts", response.context)
        response = self.client.get(
            reverse("aasrp:account_search"), {"q": "missing-account"}
        )
        self.assertEqual(response.context["accounts"], [])
