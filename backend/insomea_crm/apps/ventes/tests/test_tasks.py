from datetime import date, timedelta

import pytest

from apps.ventes.models import OpportunityStatus, Subscription, SubscriptionStatus
from apps.ventes.tasks import check_expiring_subscriptions, expire_unrenewed_subscriptions
from apps.ventes.tests.factories import make_opportunity, make_subscription, make_subscription_term


@pytest.mark.django_db
def test_check_expiring_subscriptions_marks_pending_renewal_at_30_days(client_company, product_x, commercial_user, monkeypatch):
    subscription = make_subscription(
        client=client_company,
        product=product_x,
        number='SUB-EXP-30',
        start=date.today() - timedelta(days=335),
        end=date.today() + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
    )
    opportunity = make_opportunity(client=client_company, user=commercial_user, name='Task Opportunity')
    make_subscription_term(subscription=subscription, opportunity=opportunity, term_number=1)

    monkeypatch.setattr('apps.ventes.tasks.send_renewal_reminder_email_client', lambda *args, **kwargs: None)
    monkeypatch.setattr('apps.ventes.tasks.notify_commercial_subscription_expiring', lambda *args, **kwargs: None)

    stats = check_expiring_subscriptions()

    subscription = Subscription.objects.get(pk=subscription.pk)
    assert subscription.status == SubscriptionStatus.PENDING_RENEWAL
    assert stats['marked_pending_renewal'] == 1


@pytest.mark.django_db
def test_expire_unrenewed_subscriptions_skips_when_renewal_in_progress(client_company, product_x, commercial_user, monkeypatch):
    subscription = make_subscription(
        client=client_company,
        product=product_x,
        number='SUB-EXP-SKIP',
        start=date.today() - timedelta(days=400),
        end=date.today() - timedelta(days=1),
        status=SubscriptionStatus.PENDING_RENEWAL,
    )
    original = make_opportunity(client=client_company, user=commercial_user, name='Original')
    make_subscription_term(subscription=subscription, opportunity=original, term_number=1)
    renewal = make_opportunity(
        client=client_company,
        user=commercial_user,
        type='RENEWAL',
        related_opportunity=original,
        name='Renewal In Progress',
    )
    renewal.status = OpportunityStatus.CLIENT_PO_REQUEST
    renewal.save()
    renewal.lines.create(product=product_x, quantity=1, billing_cycle='ANNUAL', renewal_of_subscription=subscription)

    monkeypatch.setattr('apps.ventes.tasks.send_subscription_expired_email_client', lambda *args, **kwargs: None)
    monkeypatch.setattr('apps.ventes.tasks.notify_teams_subscription_expired', lambda *args, **kwargs: None)

    stats = expire_unrenewed_subscriptions()

    subscription = Subscription.objects.get(pk=subscription.pk)
    assert subscription.status == SubscriptionStatus.PENDING_RENEWAL
    assert stats['renewal_in_progress'] == 1
