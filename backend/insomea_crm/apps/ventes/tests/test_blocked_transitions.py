from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.ventes.models import OpportunityStatus, ProvisionStatus, SubscriptionStatus
from apps.ventes.services import (
    add_line_to_opportunity,
    complete_provisioning,
    create_insomea_quote,
    create_opportunity,
    create_renewal_opportunity,
    create_supplier_quote,
    request_all_supplier_quotes,
    upload_client_po,
)
from apps.ventes.tests.factories import make_pdf_file, make_provision


@pytest.mark.django_db
def test_cannot_create_insomea_quote_without_supplier_quote_line(commercial_user, client_company, product_x):
    opportunity = create_opportunity(data={'name': 'Blocked Quote', 'client': client_company}, user=commercial_user)
    line = add_line_to_opportunity(opportunity_id=opportunity.id, data={'product': product_x, 'quantity': 1, 'billing_cycle': 'ANNUAL'}, user=commercial_user)
    request_all_supplier_quotes(opportunity_id=opportunity.id, user=commercial_user)

    with pytest.raises(ValidationError):
        create_insomea_quote(
            opportunity_id=opportunity.id,
            lines_pricing=[{'line_id': line.id, 'unit_price_sale': Decimal('120.00')}],
            user=commercial_user,
        )


@pytest.mark.django_db
def test_cannot_create_insomea_quote_with_sale_price_below_purchase(commercial_user, client_company, product_x):
    opportunity = create_opportunity(data={'name': 'Bad Margin', 'client': client_company}, user=commercial_user)
    line = add_line_to_opportunity(opportunity_id=opportunity.id, data={'product': product_x, 'quantity': 1, 'billing_cycle': 'ANNUAL'}, user=commercial_user)
    request_all_supplier_quotes(opportunity_id=opportunity.id, user=commercial_user)
    create_supplier_quote(
        supplier_id=product_x.supplier_id,
        document=make_pdf_file(),
        lines_data=[{'line_id': line.id, 'unit_price_purchase': Decimal('100.00')}],
        reference='SQ-BAD',
        user=commercial_user,
    )

    with pytest.raises(ValidationError):
        create_insomea_quote(
            opportunity_id=opportunity.id,
            lines_pricing=[{'line_id': line.id, 'unit_price_sale': Decimal('90.00')}],
            user=commercial_user,
        )


@pytest.mark.django_db
def test_cannot_upload_client_po_before_request_stage(commercial_user, client_company, product_x):
    opportunity = create_opportunity(data={'name': 'No PO Yet', 'client': client_company}, user=commercial_user)
    add_line_to_opportunity(opportunity_id=opportunity.id, data={'product': product_x, 'quantity': 1, 'billing_cycle': 'ANNUAL'}, user=commercial_user)

    with pytest.raises(ValidationError):
        upload_client_po(
            opportunity_id=opportunity.id,
            document=make_pdf_file('po.pdf'),
            po_number='PO-X',
            user=commercial_user,
        )


@pytest.mark.django_db
def test_cannot_complete_initial_provisioning_without_subscription_number(opportunity_initial, technicien_user, product_x):
    line = opportunity_initial.lines.create(product=product_x, quantity=1, billing_cycle='ANNUAL')
    provision = make_provision(opportunity_line=line, status=ProvisionStatus.PROVISIONING)

    with pytest.raises(ValidationError):
        complete_provisioning(
            provision_id=provision.id,
            subscription_data={'start_date': date.today(), 'end_date': date.today().replace(year=date.today().year + 1)},
            user=technicien_user,
        )


@pytest.mark.django_db
def test_cannot_create_renewal_if_subscription_not_pending(active_subscription, commercial_user):
    assert active_subscription.status == SubscriptionStatus.ACTIVE

    with pytest.raises(ValidationError):
        create_renewal_opportunity(subscription=active_subscription, user=commercial_user)
