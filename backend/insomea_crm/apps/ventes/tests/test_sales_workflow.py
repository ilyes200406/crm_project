from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.ventes.models import OpportunityStatus, ProvisionStatus, Subscription
from apps.ventes.services import (
    add_line_to_opportunity,
    approve_opportunity,
    complete_provisioning,
    create_insomea_quote,
    create_opportunity,
    create_supplier_quote,
    request_all_supplier_quotes,
    request_client_po,
    start_provisioning,
    upload_client_po,
)
from apps.ventes.tests.factories import make_pdf_file


@pytest.mark.django_db
def test_sales_happy_path_end_to_end(commercial_user, finance_user, technicien_user, client_company, product_x, product_y, product_z):
    opportunity = create_opportunity(
        data={'name': 'Full Sales Flow', 'client': client_company},
        user=commercial_user,
    )

    line_x = add_line_to_opportunity(opportunity_id=opportunity.id, data={'product': product_x, 'quantity': 5, 'billing_cycle': 'ANNUAL'}, user=commercial_user)
    line_y = add_line_to_opportunity(opportunity_id=opportunity.id, data={'product': product_y, 'quantity': 3, 'billing_cycle': 'ANNUAL'}, user=commercial_user)
    line_z = add_line_to_opportunity(opportunity_id=opportunity.id, data={'product': product_z, 'quantity': 2, 'billing_cycle': 'ANNUAL'}, user=commercial_user)

    opportunity = request_all_supplier_quotes(opportunity_id=opportunity.id, user=commercial_user)
    assert opportunity.status == OpportunityStatus.SUPPLIER_QUOTE_REQUEST

    create_supplier_quote(
        supplier_id=product_x.supplier_id,
        document=make_pdf_file('supplier-1.pdf'),
        lines_data=[
            {'line_id': line_x.id, 'unit_price_purchase': Decimal('100.00')},
            {'line_id': line_y.id, 'unit_price_purchase': Decimal('80.00')},
        ],
        reference='SQ-1',
        discount_percent=Decimal('0.00'),
        user=commercial_user,
    )
    create_supplier_quote(
        supplier_id=product_z.supplier_id,
        document=make_pdf_file('supplier-2.pdf'),
        lines_data=[
            {'line_id': line_z.id, 'unit_price_purchase': Decimal('50.00')},
        ],
        reference='SQ-2',
        discount_percent=Decimal('0.00'),
        user=commercial_user,
    )

    opportunity.refresh_from_db()
    assert opportunity.status == OpportunityStatus.SUPPLIER_QUOTE_RECIEVED

    quote = create_insomea_quote(
        opportunity_id=opportunity.id,
        lines_pricing=[
            {'line_id': line_x.id, 'unit_price_sale': Decimal('120.00')},
            {'line_id': line_y.id, 'unit_price_sale': Decimal('96.00')},
            {'line_id': line_z.id, 'unit_price_sale': Decimal('60.00')},
        ],
        discount_percent=Decimal('0.00'),
        notes='pytest quote',
        user=commercial_user,
    )
    opportunity.refresh_from_db()
    assert opportunity.status == OpportunityStatus.INSOMEA_QUOTE_CREATED
    assert quote.lines.count() == 3

    opportunity = request_client_po(opportunity_id=opportunity.id, user=commercial_user)
    assert opportunity.status == OpportunityStatus.CLIENT_PO_REQUEST

    upload_client_po(
        opportunity_id=opportunity.id,
        document=make_pdf_file('client-po.pdf'),
        po_number='PO-CLIENT-001',
        user=commercial_user,
    )
    opportunity.refresh_from_db()
    assert opportunity.status == OpportunityStatus.CLIENT_PO_RECIEVED

    approval_result = approve_opportunity(opportunity_id=opportunity.id, user=finance_user)
    opportunity.refresh_from_db()
    assert opportunity.status == OpportunityStatus.APPROUVED
    assert len(approval_result['provisions']) == 3
    assert len(approval_result['insomea_pos']) == 2

    for index, provision in enumerate(approval_result['provisions'], start=1):
        started = start_provisioning(provision_id=provision.id, user=technicien_user)
        assert started.status == ProvisionStatus.PROVISIONING

        completed = complete_provisioning(
            provision_id=provision.id,
            subscription_data={
                'subscription_number': f'MS-{index:03d}',
                'start_date': date.today(),
                'end_date': date.today() + timedelta(days=365),
            },
            user=technicien_user,
        )
        assert completed['provision'].status == ProvisionStatus.PROVISIONED

    assert Subscription.objects.count() == 3
    #assert StatusHistory.objects.filter(opportunity=opportunity).exists()


@pytest.mark.django_db
def test_sales_happy_path_calculates_expected_related_objects(commercial_user, finance_user, technicien_user, client_company, product_x, product_z):
    opportunity = create_opportunity(data={'name': 'Counts Flow', 'client': client_company}, user=commercial_user)
    line_x = add_line_to_opportunity(opportunity_id=opportunity.id, data={'product': product_x, 'quantity': 2, 'billing_cycle': 'ANNUAL'}, user=commercial_user)
    line_z = add_line_to_opportunity(opportunity_id=opportunity.id, data={'product': product_z, 'quantity': 1, 'billing_cycle': 'ANNUAL'}, user=commercial_user)

    request_all_supplier_quotes(opportunity_id=opportunity.id, user=commercial_user)
    create_supplier_quote(
        supplier_id=product_x.supplier_id,
        document=make_pdf_file('supplier-1.pdf'),
        lines_data=[{'line_id': line_x.id, 'unit_price_purchase': Decimal('100.00')}],
        reference='SQ-A',
        user=commercial_user,
    )
    create_supplier_quote(
        supplier_id=product_z.supplier_id,
        document=make_pdf_file('supplier-2.pdf'),
        lines_data=[{'line_id': line_z.id, 'unit_price_purchase': Decimal('50.00')}],
        reference='SQ-B',
        user=commercial_user,
    )
    quote = create_insomea_quote(
        opportunity_id=opportunity.id,
        lines_pricing=[
            {'line_id': line_x.id, 'unit_price_sale': Decimal('120.00')},
            {'line_id': line_z.id, 'unit_price_sale': Decimal('60.00')},
        ],
        user=commercial_user,
    )
    request_client_po(opportunity_id=opportunity.id, user=commercial_user)
    upload_client_po(opportunity_id=opportunity.id, document=make_pdf_file('po.pdf'), po_number='PO-002', user=commercial_user)
    result = approve_opportunity(opportunity_id=opportunity.id, user=finance_user)

    assert quote.total_purchase == Decimal('250.00')
    assert quote.total_sale == Decimal('300.00')
    assert len(result['provisions']) == 2
    assert len(result['insomea_pos']) == 2
