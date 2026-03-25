from datetime import date, timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.clients.models import Client, ClientStatus, Industry
from apps.products.models import Product, ProductCategory
from apps.suppliers.models import Supplier, SupplierType
from apps.users.models.users import User
from apps.ventes.models import (
    BillingCycle,
    Opportunity,
    OpportunityLine,
    OpportunityStatus,
    OpportunityType,
    Provision,
    ProvisionStatus,
    Subscription,
    SubscriptionStatus,
    SubscriptionTerm,
)


def make_user(*, email, role, password='password123', is_staff=False, is_superuser=False):
    return User.objects.create_user(
        email=email,
        password=password,
        role=role,
        is_active=True,
        is_staff=is_staff,
        is_superuser=is_superuser,
        first_name=role.title(),
        last_name='User',
    )


def make_client(*, created_by=None, assigned_to=None, email='client@example.com', company_name='Client Co'):
    return Client.objects.create(
        company_name=company_name,
        email=email,
        status=ClientStatus.CUSTOMER,
        industry=Industry.IT,
        assigned_to=assigned_to,
        created_by=created_by,
        is_active=True,
    )


def make_supplier(*, name):
    return Supplier.objects.create(
        name=name,
        type=SupplierType.DISTRIBUTOR,
        support_email=f'{name.lower().replace(" ", "")}@example.com',
        is_active=True,
    )


def make_product(*, supplier, sku, title):
    return Product.objects.create(
        sku=sku,
        title=title,
        category=ProductCategory.OTHER,
        publisher='Microsoft',
        supplier=supplier,
        is_active=True,
        is_deprecated=False,
    )


def make_opportunity(*, client, user, assigned_to=None, type=OpportunityType.INITIAL, related_opportunity=None, name='Opportunity'):
    return Opportunity.objects.create(
        client=client,
        created_by=user,
        assigned_to=assigned_to or user,
        type=type,
        related_opportunity=related_opportunity,
        name=name,
        status=OpportunityStatus.DRAFT,
    )


def make_opportunity_line(*, opportunity, product, quantity=1, billing_cycle=BillingCycle.ANNUAL, renewal_of_subscription=None):
    return OpportunityLine.objects.create(
        opportunity=opportunity,
        product=product,
        quantity=quantity,
        billing_cycle=billing_cycle,
        renewal_of_subscription=renewal_of_subscription,
    )


def make_subscription(*, client, product, number='SUB-001', quantity=1, billing_cycle=BillingCycle.ANNUAL, start=None, end=None, status=SubscriptionStatus.ACTIVE):
    start = start or date.today() - timedelta(days=30)
    end = end or date.today() + timedelta(days=30)
    return Subscription.objects.create(
        client=client,
        product=product,
        subscription_number=number,
        current_term_start=start,
        current_term_end=end,
        quantity=quantity,
        billing_cycle=billing_cycle,
        auto_renew=True,
        status=status,
    )


def make_subscription_term(*, subscription, opportunity, term_number=1, start=None, end=None, provision=None, unit_price_purchase=Decimal('100.00'), unit_price_sale=Decimal('120.00')):
    start = start or subscription.current_term_start
    end = end or subscription.current_term_end
    return SubscriptionTerm.objects.create(
        subscription=subscription,
        opportunity=opportunity,
        term_number=term_number,
        start_date=start,
        end_date=end,
        unit_price_purchase=unit_price_purchase,
        unit_price_sale=unit_price_sale,
        auto_renew_enabled=subscription.auto_renew,
    )


def make_provision(*, opportunity_line, subscription=None, status=ProvisionStatus.WAITING_PROVISION):
    return Provision.objects.create(
        opportunity_line=opportunity_line,
        subscription=subscription,
        status=status,
    )


def make_pdf_file(name='document.pdf', content=b'%PDF-1.4\n%pytest\n'):
    return SimpleUploadedFile(name, content, content_type='application/pdf')
