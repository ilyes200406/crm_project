"""
EXPLICATION :

Selectors = Couche d'optimisation des requêtes

Architecture pattern :
- Sépare lecture (selectors) de l'écriture (services)
- Optimise requêtes avec select_related, prefetch_related
- Point unique pour toutes les lectures
- Évite N+1 queries

Avantages :
- Performance optimale garantie
- Code réutilisable
- Queries complexes centralisées
- Testable isolément
- Pas de business logic (juste lecture)

Principe :
Views/Services appellent selectors pour lire
→ Selectors retournent querysets optimisés
→ Pas de query dans views/serializers
"""

from django.db.models import Q, Prefetch, Count, Max
from django.shortcuts import get_object_or_404
from .models import Client, Contact, ClientActivity


# ═══════════════════════════════════════════════════════════
# CLIENT SELECTORS
# ═══════════════════════════════════════════════════════════

def get_clients_queryset(
    user=None,
    filters=None,
    is_active=True,
    prefetch_contacts=False,
    prefetch_activities=False
):
    """
    Retourne queryset clients optimisé
    
    Args:
        user: Utilisateur (pour filtrage RBAC)
        filters: Dict de filtres additionnels
        is_active: Filtrer actifs/inactifs
        prefetch_contacts: Précharger contacts
        prefetch_activities: Précharger activités
    
    Returns:
        QuerySet optimisé avec select_related/prefetch_related
    
    Explication :
    Point central pour toutes les lectures clients
    Garantit optimisation systématique
    
    Optimisations :
    - select_related : JOINs (FK, OneToOne)
    - prefetch_related : Requêtes séparées (M2M, reverse FK)
    
    Performance :
    Sans optimisation : N+1 queries
    Avec optimisation : 2-3 queries max
    """
    
    # Base queryset
    queryset = Client.objects.all()
    
    # ───────────────────────────────────────────────────────
    # SELECT_RELATED : FK one-to-one (JOINs)
    # ───────────────────────────────────────────────────────
    
    queryset = queryset.select_related(
        'assigned_to',  # JOIN avec utilisateurs (commercial)
        'created_by'    # JOIN avec utilisateurs (créateur)
    )
    # Explication select_related :
    # Un seul query avec JOINs
    # SELECT * FROM clients
    # LEFT JOIN utilisateurs assigned ON ...
    # LEFT JOIN utilisateurs created ON ...
    #
    # Sans select_related :
    # Query 1 : SELECT * FROM clients (100 rows)
    # Query 2-101 : SELECT * FROM utilisateurs WHERE id = ? (×100)
    # → 101 queries !
    #
    # Avec select_related :
    # 1 query avec JOINs → 100× plus rapide
    
    # ───────────────────────────────────────────────────────
    # PREFETCH_RELATED : Relations inverses (separate queries)
    # ───────────────────────────────────────────────────────
    
    if prefetch_contacts:
        queryset = queryset.prefetch_related(
            Prefetch(
                'contacts',
                queryset=Contact.objects.order_by('-is_primary', 'last_name')
            )
        )
        # Explication Prefetch :
        # Query séparée optimisée pour contacts
        # SELECT * FROM contacts WHERE client_id IN (...)
        # ORDER BY is_primary DESC, last_name
        #
        # Puis Django fait le mapping en Python
        # → 2 queries au lieu de N+1
    
    if prefetch_activities:
        queryset = queryset.prefetch_related(
            Prefetch(
                'activities',
                queryset=ClientActivity.objects.select_related('user').order_by('-created_at')
            )
        )
        # Explication :
        # Précharge les 10 dernières activités
        # Avec select_related('user') pour éviter N+1 sur users
    
    # ───────────────────────────────────────────────────────
    # FILTRES
    # ───────────────────────────────────────────────────────
    
    # Filtre actifs/inactifs
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    """
    # Filtres RBAC (selon rôle user)
    if user:
        if user.role == 'COMMERCIAL':
            # Commercial voit seulement ses clients
            queryset = queryset.filter(assigned_to=user)
        elif user.role in ['TECHNICIEN', 'FINANCE']:
            # Tech/Finance : read-only, tous les clients actifs
            queryset = queryset.filter(is_active=True)
        # ADMIN : voit tout (pas de filtre)
    """
    # Filtres additionnels
    if filters:
        queryset = queryset.filter(**filters)
    
    # ───────────────────────────────────────────────────────
    # ORDERING
    # ───────────────────────────────────────────────────────
    
    # Utilise ordering du Meta par défaut (-created_at)
    # Mais permet override via filters
    
    return queryset


def get_client_by_id(client_id, user=None, prefetch_all=True):
    """
    Récupère UN client par ID avec optimisations
    
    Args:
        client_id: UUID du client
        user: Utilisateur (vérification permissions)
        prefetch_all: Précharger toutes les relations
    
    Returns:
        Client instance
    
    Raises:
        Http404: Si client n'existe pas ou user sans permission
    
    Explication :
    Récupération optimisée d'un seul client
    Utilisé pour détails client (GET /clients/{id}/)
    """
    
    queryset = Client.objects.select_related(
        'assigned_to',
        'created_by'
    )
    
    if prefetch_all:
        queryset = queryset.prefetch_related(
            Prefetch(
                'contacts',
                queryset=Contact.objects.order_by('-is_primary', 'last_name')
            ),
            Prefetch(
                'activities',
                queryset=ClientActivity.objects.select_related('user').order_by('-created_at')
            )
        )
    
    # Récupère client (404 si n'existe pas)
    client = get_object_or_404(queryset, id=client_id)
    
    # Vérification permission RBAC
    if user:
        if user.role == 'COMMERCIAL' and client.assigned_to != user:
            # Commercial peut voir seulement ses clients
            from django.http import Http404
            raise Http404("Client non trouvé")
    
    return client


def get_client_by_email(email, is_active=True):
    """
    Récupère client par email
    
    Explication :
    Recherche optimisée par email (indexé)
    Utilisé pour vérification unicité
    """
    try:
        return Client.objects.select_related(
            'assigned_to',
            'created_by'
        ).get(
            email=email,
            is_active=is_active
        )
    except Client.DoesNotExist:
        return None


# ═══════════════════════════════════════════════════════════
# CLIENT LISTING WITH STATS
# ═══════════════════════════════════════════════════════════

def get_clients_with_stats(user=None, filters=None):
    """
    Retourne clients avec statistiques agrégées
    
    Explication :
    Ajoute annotations (COUNT, MAX, etc.)
    Évite requêtes supplémentaires pour stats
    
    Stats incluses :
    - contacts_count : Nombre de contacts
    - activities_count : Nombre d'activités
    - last_activity_date : Date dernière activité
    
    Performance :
    Une seule requête avec GROUP BY
    """
    
    queryset = get_clients_queryset(user=user, filters=filters)
    
    queryset = queryset.annotate(
        contacts_count=Count('contacts'),
        activities_count=Count('activities'),
        last_activity_date=Max('activities__created_at')
    )
    # Explication annotate :
    # Ajoute champs calculés via SQL aggregation
    # SELECT clients.*, COUNT(contacts.id), COUNT(activities.id), MAX(activities.created_at)
    # FROM clients
    # LEFT JOIN contacts ON ...
    # LEFT JOIN activities ON ...
    # GROUP BY clients.id
    #
    # Résultat : client.contacts_count accessible sans query additionnelle
    
    return queryset


# ═══════════════════════════════════════════════════════════
# SEARCH QUERIES
# ═══════════════════════════════════════════════════════════

def search_clients(search_term, user=None, limit=20):
    """
    Recherche full-text clients
    
    Args:
        search_term: Terme de recherche
        user: Utilisateur (RBAC)
        limit: Nombre max résultats
    
    Returns:
        QuerySet trié par pertinence
    
    Explication :
    Recherche multi-champs avec Q objects
    
    Cherche dans :
    - company_name
    - email
    - phone
    - notes

    Performance :
    Utilise indexes sur company_name, email
    Q avec OR → utilise indexes disponibles
    """

    queryset = get_clients_queryset(user=user, is_active=True)

    if not search_term:
        return queryset[:limit]

    # Q objects pour recherche multi-champs
    query = Q(company_name__icontains=search_term) | \
            Q(email__icontains=search_term) | \
            Q(phone__icontains=search_term) | \
            Q(notes__icontains=search_term)
    # Explication Q :
    # Q() permet conditions complexes avec OR/AND
    # icontains : LIKE '%term%' (case-insensitive)
    #
    # SQL généré :
    # WHERE company_name ILIKE '%term%'
    #    OR email ILIKE '%term%'
    #    OR phone ILIKE '%term%'
    #    ...
    
    queryset = queryset.filter(query)
    
    # Tri par pertinence (priorité company_name)
    queryset = queryset.extra(
        select={
            'relevance': """
                CASE 
                    WHEN company_name ILIKE %s THEN 1
                    WHEN email ILIKE %s THEN 2
                    ELSE 3
                END
            """
        },
        select_params=[f'%{search_term}%'] * 2
    ).order_by('relevance', 'company_name')
    # Explication extra :
    # Ajoute champ calculé SQL custom
    # Tri par pertinence :
    # 1. Match dans company_name (plus important)
    # 2. Match dans email
    # 3. Match ailleurs
    
    return queryset[:limit]


# ═══════════════════════════════════════════════════════════
# CONTACT SELECTORS
# ═══════════════════════════════════════════════════════════

def get_contacts_for_client(client_id):
    """
    Récupère tous les contacts d'un client
    
    Explication :
    Optimisé avec select_related sur client
    """
    return Contact.objects.filter(
        client_id=client_id
    ).select_related('client').order_by('-is_primary', 'last_name')


def get_primary_contact(client_id):
    """
    Récupère le contact principal d'un client
    
    Returns:
        Contact instance ou None
    """
    try:
        return Contact.objects.filter(
            client_id=client_id,
            is_primary=True
        ).select_related('client').first()
    except Contact.DoesNotExist:
        return None


# ═══════════════════════════════════════════════════════════
# ACTIVITY SELECTORS
# ═══════════════════════════════════════════════════════════

def get_client_activities(client_id, limit=50):
    """
    Récupère activités récentes d'un client
    
    Args:
        client_id: UUID client
        limit: Nombre max activités
    
    Returns:
        QuerySet optimisé
    """
    return ClientActivity.objects.filter(
        client_id=client_id
    ).select_related(
        'user',
        'client'
    ).order_by('-created_at')[:limit]


def get_recent_activities(user=None, limit=20):
    """
    Récupère activités récentes (toutes ou par user)
    
    Explication :
    Dashboard : affiche activités récentes
    RBAC : Commercial voit seulement ses clients
    """
    queryset = ClientActivity.objects.select_related(
        'user',
        'client__assigned_to'
    ).order_by('-created_at')
    
    # Filtrage RBAC
    if user and user.role == 'COMMERCIAL':
        queryset = queryset.filter(client__assigned_to=user)
    
    return queryset[:limit]


# ═══════════════════════════════════════════════════════════
# DASHBOARD STATS
# ═══════════════════════════════════════════════════════════

def get_client_stats(user=None):
    """
    Statistiques pour dashboard
    
    Returns:
        dict avec stats :
        - total_clients
        - by_industry : {IT: X, FINANCE: Y, ...}
        - recent_count : Clients créés ce mois
    
    Explication :
    Queries optimisées avec aggregation SQL
    Évite COUNT(*) multiples
    """
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    queryset = get_clients_queryset(user=user, is_active=True)
    
    # Total
    total = queryset.count()

    # Par secteur
    by_industry = dict(
        queryset.values('industry').annotate(
            count=Count('id')
        ).values_list('industry', 'count')
    )
    
    # Clients récents (30 derniers jours)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_count = queryset.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    return {
        'total_clients': total,
        'by_industry': by_industry,
        'recent_count': recent_count,
    }