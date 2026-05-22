from django.urls import path

from .views import PublicDemandeCreateView

urlpatterns = [
    path('demandes/', PublicDemandeCreateView.as_view(), name='public-demande-create'),
]
