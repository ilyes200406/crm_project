import os
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from apps.ventes.tests.factories import (
    make_client,
    make_opportunity,
    make_pdf_file,
    make_product,
    make_subscription,
    make_subscription_term,
    make_supplier,
    make_user,
)


def pytest_configure(config):
    if not os.environ.get('DB_HOST'):
        os.environ['DB_HOST'] = 'localhost'


pytest_plugins = []


@pytest.fixture(scope='session', autouse=True)
def load_ventes_signals(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        import apps.ventes.signals.fsm_status_history  # noqa: F401


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return make_user(email='admin@example.com', role='ADMIN', is_staff=True, is_superuser=True)


@pytest.fixture
def commercial_user():
    return make_user(email='commercial@example.com', role='COMMERCIAL')


@pytest.fixture
def finance_user():
    return make_user(email='finance@example.com', role='FINANCE')


@pytest.fixture
def technicien_user():
    return make_user(email='tech@example.com', role='TECHNICIEN')


@pytest.fixture
def client_company(commercial_user):
    return make_client(created_by=commercial_user, assigned_to=commercial_user)


@pytest.fixture
def supplier_1():
    return make_supplier(name='Supplier One')


@pytest.fixture
def supplier_2():
    return make_supplier(name='Supplier Two')


@pytest.fixture
def product_x(supplier_1):
    return make_product(supplier=supplier_1, sku='SKU-X', title='Product X')


@pytest.fixture
def product_y(supplier_1):
    return make_product(supplier=supplier_1, sku='SKU-Y', title='Product Y')


@pytest.fixture
def product_z(supplier_2):
    return make_product(supplier=supplier_2, sku='SKU-Z', title='Product Z')


@pytest.fixture
def opportunity_initial(client_company, commercial_user):
    return make_opportunity(client=client_company, user=commercial_user, name='Initial Opportunity')


@pytest.fixture
def active_subscription(client_company, product_x, commercial_user):
    opportunity = make_opportunity(client=client_company, user=commercial_user, name='Original Opportunity')
    subscription = make_subscription(
        client=client_company,
        product=product_x,
        number='SUB-TEST-001',
        start=date.today() - timedelta(days=335),
        end=date.today() + timedelta(days=30),
    )
    make_subscription_term(subscription=subscription, opportunity=opportunity, term_number=1)
    return subscription


@pytest.fixture
def pdf_file():
    return make_pdf_file()


@pytest.fixture(autouse=True)
def patch_side_effects(monkeypatch):
    from django.core.files.base import ContentFile

    monkeypatch.setattr(
        'apps.ventes.services.quote_service.generate_quote_pdf',
        lambda insomea_quote: ContentFile(b'%PDF-1.4\n%quote\n', name=f'quote-{insomea_quote.id}.pdf'),
    )
    monkeypatch.setattr('apps.ventes.tasks.send_supplier_quote_request_email.delay', lambda *args, **kwargs: None)
    monkeypatch.setattr('apps.ventes.tasks.send_client_quote_pdf_email.delay', lambda *args, **kwargs: None)
    monkeypatch.setattr('apps.ventes.tasks.send_insomea_po_email.delay', lambda *args, **kwargs: None)
    monkeypatch.setattr('apps.ventes.notifications.services.notify_finance_to_approve', lambda *args, **kwargs: None)
    monkeypatch.setattr('apps.ventes.notifications.services.notify_techniciens_provision_waiting', lambda *args, **kwargs: None)
    monkeypatch.setattr('apps.ventes.notifications.services.notify_all_provisioned', lambda *args, **kwargs: None)
