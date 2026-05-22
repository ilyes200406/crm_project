from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DemandeClientViewSet

router = DefaultRouter()
router.register(r'', DemandeClientViewSet, basename='demande')

urlpatterns = [
    path('', include(router.urls)),
]
