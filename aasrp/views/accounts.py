"""Staff reporting across a main and all alts on an Auth account."""

# Django
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, render

# Alliance Auth
from allianceauth.authentication.decorators import permissions_required

# AA SRP
from aasrp.models import SrpRequest


@permission_required("aasrp.basic_access")
@permissions_required(("aasrp.manage_srp", "aasrp.manage_srp_requests"))
def account_history(request, user_id=None):
    """Search account identities and report requests by their original creator.

    Current ownership is used for searching and displaying linked characters,
    never to reassign historical requests when a character changes owners.
    """
    query = request.GET.get("q", "").strip()[:254]
    context = {"query": query}
    users = get_user_model().objects.select_related("profile__main_character")
    if user_id is None:
        if query:
            users = (
                users.filter(
                    Q(profile__main_character__character_name__icontains=query)
                    | Q(
                        character_ownerships__character__character_name__icontains=query
                    )
                    | Q(username__icontains=query)
                )
                .distinct()
                .order_by("profile__main_character__character_name", "pk")
            )
            page = Paginator(users, 25).get_page(request.GET.get("page"))
            totals = dict(
                SrpRequest.objects.filter(
                    creator_id__in=[user.pk for user in page],
                    request_status=SrpRequest.Status.APPROVED,
                )
                .values("creator_id")
                .annotate(total=Sum("payout_amount"))
                .values_list("creator_id", "total")
            )
            context.update(
                page=page,
                accounts=[
                    {"user": user, "total": totals.get(user.pk, 0)} for user in page
                ],
            )
    else:
        account = get_object_or_404(users, pk=user_id)
        requests = (
            SrpRequest.objects.filter(creator=account)
            .select_related("character", "ship", "srp_link")
            .order_by("-post_time", "-pk")
        )
        totals = requests.values("request_status").annotate(total=Sum("payout_amount"))
        context.update(
            account=account,
            characters=account.character_ownerships.select_related(
                "character"
            ).order_by("character__character_name"),
            approved_total=next(
                (
                    row["total"]
                    for row in totals
                    if row["request_status"] == SrpRequest.Status.APPROVED
                ),
                0,
            ),
            history=Paginator(requests, 50).get_page(request.GET.get("page")),
        )
    return render(request, "aasrp/account-history.html", context)
