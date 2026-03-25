import pytest

from apps.ventes.tests.factories import make_opportunity, make_provision


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('fixture_name', 'expected_status'),
    [
        ('commercial_user', 200),
        ('admin_user', 200),
        ('finance_user', 403),
        ('technicien_user', 403),
    ],
)
def test_request_supplier_quotes_permissions(request, api_client, fixture_name, expected_status, client_company):
    user = request.getfixturevalue(fixture_name)
    opportunity = make_opportunity(client=client_company, user=request.getfixturevalue('commercial_user'))
    api_client.force_authenticate(user=user)

    response = api_client.post(f'/api/ventes/opportunities/{opportunity.id}/request-supplier-quotes/')
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('fixture_name', 'expected_status'),
    [
        ('finance_user', 200),
        ('admin_user', 200),
        ('commercial_user', 403),
        ('technicien_user', 403),
    ],
)
def test_approve_permissions(request, api_client, fixture_name, expected_status, client_company, product_x):
    finance_owner = request.getfixturevalue('finance_user')
    user = request.getfixturevalue(fixture_name)
    opportunity = make_opportunity(client=client_company, user=request.getfixturevalue('commercial_user'))
        # Add a line to the opportunity
    from apps.ventes.services import add_line_to_opportunity
    add_line_to_opportunity(
        opportunity_id=opportunity.id,
        data={'product': product_x, 'quantity': 1, 'billing_cycle': 'ANNUAL'},
        user=request.getfixturevalue('commercial_user')
    )
    opportunity.status = 'CLIENT_PO_RECIEVED'
    opportunity.assigned_to = finance_owner
    opportunity.save()

    api_client.force_authenticate(user=user)
    response = api_client.post(f'/api/ventes/opportunities/{opportunity.id}/approve/')
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('fixture_name', 'expected_status'),
    [
        ('technicien_user', 200),
        ('admin_user', 200),
        ('commercial_user', 403),
        ('finance_user', 403),
    ],
)
def test_start_provisioning_permissions(request, api_client, fixture_name, expected_status, opportunity_initial, product_x):
    owner = request.getfixturevalue('commercial_user')
    tech = request.getfixturevalue('technicien_user')
    line = opportunity_initial.lines.create(product=product_x, quantity=1, billing_cycle='ANNUAL')
    opportunity_initial.status = 'APPROUVED'
    opportunity_initial.assigned_to = tech
    opportunity_initial.save()
    provision = make_provision(opportunity_line=line)

    api_client.force_authenticate(user=request.getfixturevalue(fixture_name))
    response = api_client.post(f'/api/ventes/provisions/{provision.id}/start/')
    assert response.status_code == expected_status
