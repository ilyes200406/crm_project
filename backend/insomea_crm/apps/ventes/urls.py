"""
URLS - APP OPPORTUNITIES

Router REST Framework
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    OpportunityViewSet,
    OpportunityLineViewSet,
    SupplierQuoteViewSet,
    InsomeaQuoteViewSet,
    ProvisionViewSet,
    SubscriptionViewSet,
    StatusHistoryViewSet,
)

# Router principal
router = DefaultRouter()

# Register ViewSets
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'opportunity-lines', OpportunityLineViewSet, basename='opportunityline')
router.register(r'supplier-quotes', SupplierQuoteViewSet, basename='supplierquote')
router.register(r'insomea-quotes', InsomeaQuoteViewSet, basename='insomeaquote')
router.register(r'provisions', ProvisionViewSet, basename='provision')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'status-history', StatusHistoryViewSet, basename='statushistory')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]