"""
URLS - APP OPPORTUNITIES

Lines are nested under /opportunities/{opportunity_pk}/lines/
via drf-nested-routers.
"""

from django.urls import path, include
from rest_framework_nested import routers

from .views import (
    OpportunityViewSet,
    OpportunityLineViewSet,
    SupplierQuoteViewSet,
    InsomeaQuoteViewSet,
    ProvisionViewSet,
    SubscriptionViewSet,
)

# Top-level router
router = routers.DefaultRouter()
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'supplier-quotes', SupplierQuoteViewSet, basename='supplierquote')
router.register(r'insomea-quotes', InsomeaQuoteViewSet, basename='insomeaquote')
router.register(r'provisions', ProvisionViewSet, basename='provision')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

# Nested router: /opportunities/{opportunity_pk}/lines/
opportunities_router = routers.NestedDefaultRouter(
    router, r'opportunities', lookup='opportunity'
)
opportunities_router.register(r'lines', OpportunityLineViewSet, basename='opportunity-lines')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(opportunities_router.urls)),
]
