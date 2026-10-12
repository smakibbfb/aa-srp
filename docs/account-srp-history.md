# Account SRP history

SRP staff can use **Account SRP history** in the navigation to search by main,
any currently linked alt, or Auth username. Select a result to see the account's
currently linked characters, corporation names, lifetime approved SRP total,
and all submitted requests with dates, ships, fleets, statuses and amounts.
Search results show 25 accounts per page; history shows 50 requests per page.

An account means one Alliance Auth user and all their linked characters.
Totals combine requests across every fleet, including closed and completed
fleets. Only approved requests contribute to the total; pending and rejected
requests remain visible in the history. AA-SRP has no payment confirmation
status, so approved ISK must not be interpreted as confirmed paid ISK.

Access requires `aasrp.basic_access` and either `aasrp.manage_srp` or
`aasrp.manage_srp_requests`, including when visiting an account URL directly.
No new permissions, database fields, migrations or ESI scopes are required.

Historical requests belong to their recorded creator, not a character's current
owner. Transferring an alt does not transfer its old claims. Search and the
linked character list reflect current Auth ownership. Requests attributed to
the existing deleted-user sentinel cannot be separated back into the original
deleted accounts. This page reports SRP and linked character identities; it
does not expose unrelated account data or authentication tokens.

## Validation

Regression tests are in `aasrp/tests/test_views_accounts.py`, covering access,
main/alt/username search, approved totals, ownership transfer, empty results
and missing accounts. Run in the usual Alliance Auth test environment:

```sh
DJANGO_SETTINGS_MODULE=testauth.settings.local python runtests.py aasrp.tests.test_views_accounts -v 2
```

Before production installation, run these tests and the repository's usual
CI checks, then check the page on a staging Auth installation with real data.
