from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.ventes.models import OpportunityType, ProvisionStatus, SubscriptionStatus, Subscription
from apps.ventes.services import (
    approve_opportunity,
    complete_provisioning,
    create_insomea_quote,
    create_renewal_opportunity,
    create_supplier_quote,
    request_all_supplier_quotes,
    request_client_po,
    start_provisioning,
    upload_client_po,
)
from apps.ventes.tests.factories import make_pdf_file


@pytest.mark.django_db
def test_renewal_happy_path_end_to_end(active_subscription, commercial_user, finance_user, technicien_user):
    active_subscription.mark_pending_renewal()
    active_subscription.save()
    assert active_subscription.status == SubscriptionStatus.PENDING_RENEWAL

    result = create_renewal_opportunity(
        subscription=active_subscription,
        user=commercial_user,
        quantity=7,
        notes='renewal via pytest',
    )
    renewal_opportunity = result['opportunity']
    renewal_line = result['line']

    assert renewal_opportunity.type == OpportunityType.RENEWAL
    assert renewal_line.renewal_of_subscription == active_subscription
    assert renewal_line.quantity == 7

    request_all_supplier_quotes(opportunity_id=renewal_opportunity.id, user=commercial_user)
    create_supplier_quote(
        supplier_id=renewal_line.product.supplier_id,
        document=make_pdf_file('renewal-supplier.pdf'),
        lines_data=[{'line_id': renewal_line.id, 'unit_price_purchase': Decimal('110.00')}],
        reference='SQ-REN',
        user=commercial_user,
    )
    create_insomea_quote(
        opportunity_id=renewal_opportunity.id,
        lines_pricing=[{'line_id': renewal_line.id, 'unit_price_sale': Decimal('132.00')}],
        user=commercial_user,
    )
    request_client_po(opportunity_id=renewal_opportunity.id, user=commercial_user)
    upload_client_po(
        opportunity_id=renewal_opportunity.id,
        document=make_pdf_file('renewal-po.pdf'),
        po_number='PO-REN-001',
        user=commercial_user,
    )
    approval_result = approve_opportunity(opportunity_id=renewal_opportunity.id, user=finance_user)
    provision = approval_result['provisions'][0]
    assert provision.subscription == active_subscription

    started = start_provisioning(provision_id=provision.id, user=technicien_user)
    assert started.status == ProvisionStatus.PROVISIONING

    completed = complete_provisioning(
        provision_id=provision.id,
        subscription_data={
            'start_date': date.today() + timedelta(days=31),
            'end_date': date.today() + timedelta(days=396),
        },
        user=technicien_user,
    )

    fresh_subscription = Subscription.objects.get(id=active_subscription.id)
    assert completed['provision'].status == ProvisionStatus.PROVISIONED
    assert fresh_subscription.status == SubscriptionStatus.ACTIVE
    assert fresh_subscription.terms.count() == 2
#    assert StatusHistory.objects.filter(subscription=active_subscription).exists()


@pytest.mark.django_db
def test_create_renewal_opportunity_uses_optional_quantity_and_notes(active_subscription, commercial_user):
    active_subscription.mark_pending_renewal()
    active_subscription.save()

    result = create_renewal_opportunity(
        subscription=active_subscription,
        user=commercial_user,
        quantity=12,
        notes='custom renewal notes',
    )

    assert result['line'].quantity == 12
    assert result['opportunity'].notes == 'custom renewal notes'
