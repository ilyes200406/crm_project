"""
import pytest

from apps.ventes.models import StatusHistory
from apps.ventes.services import create_opportunity, request_all_supplier_quotes
from apps.ventes.tests.factories import make_opportunity_line, make_subscription


@pytest.mark.django_db
def test_opportunity_and_line_transitions_create_status_history(commercial_user, client_company, product_x):
    opportunity = create_opportunity(data={'name': 'History Flow', 'client': client_company}, user=commercial_user)
    make_opportunity_line(opportunity=opportunity, product=product_x, quantity=1)

    request_all_supplier_quotes(opportunity_id=opportunity.id, user=commercial_user)

    assert StatusHistory.objects.filter(opportunity=opportunity).exists()
    assert StatusHistory.objects.filter(opportunity_line__opportunity=opportunity).exists()


@pytest.mark.django_db
def test_subscription_transition_creates_status_history(client_company, product_x):
    subscription = make_subscription(client=client_company, product=product_x, number='SUB-HIST-1')
    subscription.mark_pending_renewal()
    subscription.save()

    assert StatusHistory.objects.filter(subscription=subscription).exists()
"""