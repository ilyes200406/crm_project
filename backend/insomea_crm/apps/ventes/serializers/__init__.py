"""
SERIALIZERS - APP OPPORTUNITIES
"""

# ... (garder imports existants)

# 🆕 NOUVEAUX IMPORTS
from .subscription_serializers import (
    SubscriptionTermSerializer,
    SubscriptionListSerializer,
    SubscriptionDetailSerializer,
    SubscriptionCreateSerializer,
    SubscriptionUpdateSerializer,
    CreateRenewalSerializer,
    RenewalDataSerializer,
)

from .provision_serializers import (
    ProvisionListSerializer,
    ProvisionDetailSerializer,
    StartProvisioningSerializer,
    CompleteProvisioningSerializer,  # 🆕 MODIFIÉ
    FailProvisioningSerializer,
)

__all__ = [
    # ... (garder existants)
    
    # 🆕 NOUVEAUX
    'SubscriptionTermSerializer',
    'SubscriptionListSerializer',
    'SubscriptionDetailSerializer',
    'SubscriptionCreateSerializer',
    'SubscriptionUpdateSerializer',
    'CreateRenewalSerializer',
    'RenewalDataSerializer',
    
    # 🆕 MODIFIÉS
    'ProvisionListSerializer',
    'ProvisionDetailSerializer',
    'CompleteProvisioningSerializer',
]