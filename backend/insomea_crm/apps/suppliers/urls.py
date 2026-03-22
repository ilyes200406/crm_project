"""
URLS - APP SUPPLIERS

Routes pour API REST suppliers
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SupplierViewSet


# ═══════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════

router = DefaultRouter()
router.register(r'', SupplierViewSet, basename='supplier')

# Routes générées automatiquement :
# GET    /suppliers/              → list
# POST   /suppliers/              → create
# GET    /suppliers/{id}/         → retrieve
# PUT    /suppliers/{id}/         → update
# PATCH  /suppliers/{id}/         → partial_update
# DELETE /suppliers/{id}/         → destroy (désactivation)
# POST   /suppliers/{id}/activate/    → activate
# POST   /suppliers/{id}/deactivate/  → deactivate
# GET    /suppliers/stats/        → stats


# ═══════════════════════════════════════════════════════════
# URL PATTERNS
# ═══════════════════════════════════════════════════════════

app_name = 'apps.suppliers'

urlpatterns = [
    path('', include(router.urls)),
]