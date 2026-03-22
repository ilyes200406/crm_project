"""
EXPLICATION :

URLs = Configuration des routes API

Architecture :
- DRF Router pour ViewSets (auto-génération)
- URLs REST standards
- Nested routes pour relations
- Custom actions incluses

Avantages :
- URLs auto-générées (DRY)
- Standards REST
- Documentation auto (Swagger)
- Versioning possible

Structure générée :
/api/clients/                     → ClientViewSet
/api/clients/contacts/            → ContactViewSet
/api/clients/activities/          → ActivityViewSet
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import ClientViewSet, ContactViewSet, ClientActivityViewSet


# ═══════════════════════════════════════════════════════════
# ROUTER PRINCIPAL
# ═══════════════════════════════════════════════════════════

router = DefaultRouter()
# Explication DefaultRouter :
# DRF built-in router
# Génère automatiquement URLs REST standards
# Ajoute API root view (/)

router.register(r'clients', ClientViewSet, basename='client')
# Explication :
# Génère automatiquement :
# - GET    /clients/                     → list()
# - POST   /clients/                     → create()
# - GET    /clients/{id}/                → retrieve()
# - PUT    /clients/{id}/                → update()
# - PATCH  /clients/{id}/                → partial_update()
# - DELETE /clients/{id}/                → destroy()
#
# Actions custom :
# - POST   /clients/{id}/assign/         → assign()
# - POST   /clients/{id}/restore/        → restore()
# - GET    /clients/stats/               → stats()
# - GET    /clients/export/              → export()
# - POST   /clients/bulk-update/         → bulk_update()
# - POST   /clients/bulk-delete/         → bulk_delete()
# - GET    /clients/{id}/activities/     → activities()
# - GET    /clients/{id}/contacts/       → contacts()

router.register(r'contacts', ContactViewSet, basename='contact')
# Explication :
# URLs contacts standalone
# GET /contacts/, POST /contacts/, etc.
#
# Alternative : nested sous clients (voir plus bas)

router.register(r'activities', ClientActivityViewSet, basename='activity')
# Explication :
# URLs activités standalone
# GET /activities/ (toutes activités filtrées par RBAC)
# GET /activities/{id}/


# ═══════════════════════════════════════════════════════════
# NESTED ROUTERS (Optionnel)
# ═══════════════════════════════════════════════════════════

"""
EXPLICATION NESTED ROUTING :

Pour relations parent-enfant, on peut utiliser nested routes :
/clients/{client_id}/contacts/
/clients/{client_id}/activities/

Avantages :
- URLs sémantiques
- Context automatique (client_id)
- RESTful

Installation :
pip install drf-nested-routers

Désavantages :
- Complexité additionnelle
- Redondance avec ViewSets standalone

Décision architecture :
Pour ce projet, on utilise :
1. ViewSets standalone pour flexibilité
2. Custom actions pour nested access
   Ex: GET /clients/{id}/contacts/ (action custom)

Mais voici l'implémentation nested si besoin :
"""

# # Nested router pour contacts sous clients
# clients_router = nested_routers.NestedDefaultRouter(
#     router, 
#     r'clients', 
#     lookup='client'
# )
# clients_router.register(
#     r'contacts', 
#     ContactViewSet, 
#     basename='client-contacts'
# )
# # Génère :
# # GET    /clients/{client_id}/contacts/
# # POST   /clients/{client_id}/contacts/
# # GET    /clients/{client_id}/contacts/{id}/
# # PUT    /clients/{client_id}/contacts/{id}/
# # DELETE /clients/{client_id}/contacts/{id}/

# # Nested router pour activités sous clients
# clients_router.register(
#     r'activities', 
#     ClientActivityViewSet, 
#     basename='client-activities'
# )
# # Génère :
# # GET /clients/{client_id}/activities/


# ═══════════════════════════════════════════════════════════
# URL PATTERNS
# ═══════════════════════════════════════════════════════════

urlpatterns = [
    # Router URLs (auto-générées)
    path('', include(router.urls)),
    
    # Si nested routers activés :
    # path('', include(clients_router.urls)),
]

# Explication :
# include(router.urls) génère toutes les URLs
# Préfixe ajouté dans config/urls.py
# → /api/clients/...


# ═══════════════════════════════════════════════════════════
# APP NAME (pour reverse URLs)
# ═══════════════════════════════════════════════════════════

app_name = 'clients'
# Explication :
# Permet reverse() avec namespace
# reverse('clients:client-list')
# reverse('clients:client-detail', args=[client_id])
# reverse('clients:client-assign', args=[client_id])


# ═══════════════════════════════════════════════════════════
# DOCUMENTATION URLs GÉNÉRÉES
# ═══════════════════════════════════════════════════════════

"""
URLs complètes générées par le router :

┌─────────────────────────────────────────────────────────────┐
│ CLIENTS ENDPOINTS                                           │
├─────────────────────────────────────────────────────────────┤
│ GET    /api/clients/                                        │
│        → Liste clients (paginée, filtrée)                   │
│        Query params :                                       │
│          - status, industry, country, city                  │
│          - assigned_to, created_by                          │
│          - created_after, created_before                    │
│          - search, ordering                                 │
│          - page, page_size                                  │
│                                                             │
│ POST   /api/clients/                                        │
│        → Créer client                                       │
│        Body : ClientCreateSerializer                        │
│        Permission : ADMIN ou COMMERCIAL                     │
│                                                             │
│ GET    /api/clients/{id}/                                   │
│        → Détails client                                     │
│        Response : ClientDetailSerializer (nested)           │
│                                                             │
│ PUT    /api/clients/{id}/                                   │
│        → Update complet                                     │
│        Body : ClientUpdateSerializer                        │
│        Permission : ADMIN ou owner COMMERCIAL               │
│                                                             │
│ PATCH  /api/clients/{id}/                                   │
│        → Update partiel                                     │
│        Body : ClientUpdateSerializer (partial)              │
│                                                             │
│ DELETE /api/clients/{id}/                                   │
│        → Soft delete (is_active=False)                      │
│        Permission : ADMIN seulement                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ CLIENTS CUSTOM ACTIONS                                      │
├─────────────────────────────────────────────────────────────┤
│ POST   /api/clients/{id}/assign/                            │
│        → Réassigner à un commercial                         │
│        Body : {assigned_to: uuid}                           │
│        Permission : ADMIN seulement                         │
│                                                             │
│ POST   /api/clients/{id}/restore/                           │
│        → Réactiver client désactivé                         │
│        Permission : ADMIN seulement                         │
│                                                             │
│ GET    /api/clients/{id}/activities/                        │
│        → Historique activités client                        │
│        Response : ClientActivitySerializer[] (paginé)       │
│                                                             │
│ GET    /api/clients/{id}/contacts/                          │
│        → Contacts du client                                 │
│        Response : ContactMinimalSerializer[]                │
│                                                             │
│ GET    /api/clients/stats/                                  │
│        → Statistiques globales                              │
│        Response : {                                         │
│          total_clients: int,                                │
│          by_status: {LEAD: X, ...},                         │
│          by_industry: {IT: Y, ...},                         │
│          recent_count: int                                  │
│        }                                                    │
│                                                             │
│ GET    /api/clients/export/?format=csv                      │
│        → Export CSV/Excel                                   │
│        Query params : format (csv|excel)                    │
│        Permission : ADMIN, COMMERCIAL, FINANCE              │
│        Response : File download                             │
│                                                             │
│ POST   /api/clients/bulk-update/                            │
│        → Update multiple clients                            │
│        Body : {                                             │
│          client_ids: [uuid, ...],                           │
│          data: {status: 'CUSTOMER', ...}                    │
│        }                                                    │
│        Permission : ADMIN seulement                         │
│                                                             │
│ POST   /api/clients/bulk-delete/                            │
│        → Soft delete multiple clients                       │
│        Body : {client_ids: [uuid, ...]}                     │
│        Permission : ADMIN seulement                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ CONTACTS ENDPOINTS                                          │
├─────────────────────────────────────────────────────────────┤
│ GET    /api/clients/contacts/                               │
│        → Liste tous les contacts                            │
│        Query params : client, is_primary, search            │
│                                                             │
│ POST   /api/clients/contacts/                               │
│        → Créer contact                                      │
│        Body : ContactCreateSerializer + client_id           │
│                                                             │
│ GET    /api/clients/contacts/{id}/                          │
│        → Détails contact                                    │
│                                                             │
│ PUT    /api/clients/contacts/{id}/                          │
│        → Update contact                                     │
│                                                             │
│ PATCH  /api/clients/contacts/{id}/                          │
│        → Update partiel contact                             │
│                                                             │
│ DELETE /api/clients/contacts/{id}/                          │
│        → Supprimer contact (hard delete)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ACTIVITIES ENDPOINTS (Read-Only)                            │
├─────────────────────────────────────────────────────────────┤
│ GET    /api/clients/activities/                             │
│        → Liste activités (filtrées par RBAC)                │
│        Query params :                                       │
│          - client, activity_type, user                      │
│          - created_after, created_before                    │
│                                                             │
│ GET    /api/clients/activities/{id}/                        │
│        → Détails activité                                   │
└─────────────────────────────────────────────────────────────┘
"""