from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.ventes.models import Subscription, SubscriptionStatus, SubscriptionTerm
from apps.ventes.tests.factories import (
    make_opportunity,
    make_subscription,
    make_subscription_term,
)


# ── Subscription creation ────────────────────────────────────

@pytest.mark.django_db
def test_subscription_created_with_correct_fields(client_company, product_x):
    start = date.today()
    end = start + timedelta(days=365)
    sub = make_subscription(
        client=client_company,
        product=product_x,
        number='SUB-100',
        quantity=3,
        billing_cycle='ANNUAL',
        start=start,
        end=end,
    )

    assert sub.pk is not None
    assert sub.subscription_number == 'SUB-100'
    assert sub.client == client_company
    assert sub.product == product_x
    assert sub.quantity == 3
    assert sub.billing_cycle == 'ANNUAL'
    assert sub.current_term_start == start
    assert sub.current_term_end == end
    assert sub.status == SubscriptionStatus.ACTIVE
    assert sub.auto_renew is True


# ── Term / vérification des échéances ───────────────────────

@pytest.mark.django_db
def test_subscription_term_created_with_correct_pricing(client_company, product_x, commercial_user):
    opp = make_opportunity(client=client_company, user=commercial_user)
    sub = make_subscription(client=client_company, product=product_x)

    term = make_subscription_term(
        subscription=sub,
        opportunity=opp,
        term_number=1,
        unit_price_purchase=Decimal('100.00'),
        unit_price_sale=Decimal('120.00'),
    )

    assert term.term_number == 1
    assert term.unit_price_purchase == Decimal('100.00')
    assert term.unit_price_sale == Decimal('120.00')
    assert term.subscription == sub
    assert term.opportunity == opp
    assert term.start_date == sub.current_term_start
    assert term.end_date == sub.current_term_end


@pytest.mark.django_db
def test_subscription_expiring_soon_detected(client_company, product_x):
    start = date.today() - timedelta(days=335)
    end = date.today() + timedelta(days=20)   # 20 days left → below 30-day threshold
    sub = make_subscription(client=client_company, product=product_x, start=start, end=end)

    assert sub.is_expiring_soon(days=30) is True
    assert sub.days_until_expiration() == 20


@pytest.mark.django_db
def test_subscription_not_expiring_soon(client_company, product_x):
    start = date.today()
    end = date.today() + timedelta(days=300)
    sub = make_subscription(client=client_company, product=product_x, start=start, end=end)

    assert sub.is_expiring_soon(days=30) is False
    assert sub.days_until_expiration() > 30


@pytest.mark.django_db
def test_subscription_days_until_expiration_expired_returns_zero(client_company, product_x):
    start = date.today() - timedelta(days=400)
    end = date.today() - timedelta(days=10)   # already expired
    sub = make_subscription(
        client=client_company,
        product=product_x,
        start=start,
        end=end,
        status=SubscriptionStatus.EXPIRED,
    )

    assert sub.days_until_expiration() == 0


# ── FSM status transitions ───────────────────────────────────

@pytest.mark.django_db
def test_active_subscription_transitions_to_pending_renewal(client_company, product_x):
    sub = make_subscription(
        client=client_company,
        product=product_x,
        status=SubscriptionStatus.ACTIVE,
    )
    sub.mark_pending_renewal()
    sub.save()
    sub.refresh_from_db()

    assert sub.status == SubscriptionStatus.PENDING_RENEWAL


# ── Multiple terms ordered by term_number ───────────────────

@pytest.mark.django_db
def test_multiple_terms_ordered_correctly(client_company, product_x, commercial_user):
    opp = make_opportunity(client=client_company, user=commercial_user)
    sub = make_subscription(client=client_company, product=product_x)

    term1 = make_subscription_term(subscription=sub, opportunity=opp, term_number=1)
    term2 = make_subscription_term(
        subscription=sub,
        opportunity=opp,
        term_number=2,
        start=sub.current_term_end,
        end=sub.current_term_end + timedelta(days=365),
    )

    terms = list(sub.get_all_terms())
    assert len(terms) == 2
    assert terms[0].term_number == 1
    assert terms[1].term_number == 2
    assert terms[1].start_date == terms[0].end_date
