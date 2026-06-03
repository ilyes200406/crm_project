from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from apps.ventes.models import (
    OpportunityStatus,
    Provision,
    ProvisionStatus,
    Subscription,
    SubscriptionTerm,
)
from apps.ventes.services import (
    add_line_to_opportunity,
    approve_opportunity,
    complete_provisioning,
    confirm_all_insomea_pos,
    create_insomea_quote,
    create_opportunity,
    create_supplier_quote,
    request_all_supplier_quotes,
    request_client_po,
    send_insomea_pos,
    start_provisioning,
    upload_client_po,
)
from apps.ventes.tests.factories import make_pdf_file


@pytest.mark.django_db
def test_complete_sales_workflow_end_to_end(
    monkeypatch,
    commercial_user,
    finance_user,
    technicien_user,
    client_company,
    product_x,
    product_y,
):
    monkeypatch.setattr('apps.ventes.tasks.send_insomea_po_email', MagicMock())

    # ── 1. Create opportunity and add lines ──────────────────
    opp = create_opportunity(
        data={'name': 'Full Workflow', 'client': client_company},
        user=commercial_user,
    )
    assert opp.status == OpportunityStatus.DRAFT

    line_x = add_line_to_opportunity(
        opportunity_id=opp.id,
        data={'product': product_x, 'quantity': 5, 'billing_cycle': 'ANNUAL'},
        user=commercial_user,
    )
    line_y = add_line_to_opportunity(
        opportunity_id=opp.id,
        data={'product': product_y, 'quantity': 2, 'billing_cycle': 'ANNUAL'},
        user=commercial_user,
    )

    # ── 2. Request supplier quotes ───────────────────────────
    opp = request_all_supplier_quotes(opportunity_id=opp.id, user=commercial_user)
    assert opp.status == OpportunityStatus.SUPPLIER_QUOTE_REQUEST

    # ── 3. Receive supplier quotes ───────────────────────────
    # product_x and product_y share the same supplier (supplier_1)
    create_supplier_quote(
        supplier_id=product_x.supplier_id,
        document=make_pdf_file('sq.pdf'),
        lines_data=[
            {'line_id': line_x.id, 'unit_price_purchase': Decimal('100.00')},
            {'line_id': line_y.id, 'unit_price_purchase': Decimal('80.00')},
        ],
        reference='SQ-1',
        user=commercial_user,
    )
    opp.refresh_from_db()
    assert opp.status == OpportunityStatus.SUPPLIER_QUOTE_RECIEVED

    # ── 4. Create Insomea quote ──────────────────────────────
    quote = create_insomea_quote(
        opportunity_id=opp.id,
        lines_pricing=[
            {'line_id': line_x.id, 'unit_price_sale': Decimal('120.00')},
            {'line_id': line_y.id, 'unit_price_sale': Decimal('96.00')},
        ],
        discount_percent=Decimal('0.00'),
        user=commercial_user,
    )
    opp.refresh_from_db()
    assert opp.status == OpportunityStatus.INSOMEA_QUOTE_CREATED
    assert quote.total_purchase == Decimal('660.00')   # 5×100 + 2×80
    assert quote.total_sale == Decimal('792.00')        # 5×120 + 2×96
    assert quote.lines.count() == 2

    # ── 5. Send quote to client, receive signed PO ───────────
    opp = request_client_po(opportunity_id=opp.id, user=commercial_user)
    assert opp.status == OpportunityStatus.CLIENT_PO_REQUEST

    upload_client_po(
        opportunity_id=opp.id,
        document=make_pdf_file('client-po.pdf'),
        po_number='PO-CLIENT-001',
        user=commercial_user,
    )
    opp.refresh_from_db()
    assert opp.status == OpportunityStatus.CLIENT_PO_RECIEVED

    # ── 6. Finance approves — Insomea POs created ───────────
    result = approve_opportunity(opportunity_id=opp.id, user=finance_user)
    opp.refresh_from_db()
    assert opp.status == OpportunityStatus.APPROUVED
    assert len(result['pos_created']) == 1  # single supplier → single PO

    # ── 7. Send POs to suppliers ─────────────────────────────
    send_insomea_pos(opportunity_id=opp.id, user=finance_user)
    opp.refresh_from_db()
    assert opp.status == OpportunityStatus.INSOMEA_POS_SENT

    # ── 8. Confirm POs received → provisions created ─────────
    confirm_result = confirm_all_insomea_pos(opportunity_id=opp.id, user=finance_user)
    opp.refresh_from_db()
    assert opp.status == OpportunityStatus.INSOMEA_POS_CONFIRMED
    assert confirm_result['provisions_created'] is True

    provisions = list(Provision.objects.filter(opportunity_line__opportunity=opp))
    assert len(provisions) == 2  # one per line

    # ── 9. Technicien provisions each line ───────────────────
    today = date.today()
    for i, provision in enumerate(provisions, start=1):
        start_provisioning(provision_id=provision.id, user=technicien_user)
        completed = complete_provisioning(
            provision_id=provision.id,
            subscription_data={
                'subscription_number': f'MS-{i:03d}',
                'start_date': today,
                'end_date': today + timedelta(days=365),
            },
            user=technicien_user,
        )
        assert completed['provision'].status == ProvisionStatus.PROVISIONED

    # ── 10. Verify subscriptions created correctly ───────────
    assert Subscription.objects.filter(client=client_company).count() == 2

    sub_x = Subscription.objects.get(client=client_company, product=product_x)
    assert sub_x.quantity == 5
    assert sub_x.billing_cycle == 'ANNUAL'
    assert sub_x.current_term_start == today
    assert sub_x.current_term_end == today + timedelta(days=365)

    # ── 11. Verify subscription terms ────────────────────────
    term_x = SubscriptionTerm.objects.filter(subscription=sub_x).first()
    assert term_x is not None
    assert term_x.unit_price_purchase == Decimal('100.00')
    assert term_x.unit_price_sale == Decimal('120.00')
