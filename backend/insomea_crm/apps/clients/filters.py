"""
EXPLICATION :

Filters = Filtrage et recherche avancés

Architecture :
- Django Filter Backend pour filtres déclaratifs
- Search Filter pour recherche full-text
- Ordering Filter pour tri dynamique
- Custom filters pour logique complexe

Avantages :
- URL-based filtering : /clients/?status=CUSTOMER&industry=IT
- Performance optimisée (utilise indexes DB)
- Code réutilisable
- Documentation auto (Swagger/OpenAPI)

Performance :
- Tous les filtres utilisent indexes DB
- Pas de filtrage Python (lent)
- Queries optimisées par Django ORM
"""

import django_filters
from django.db.models import Q
from .models import Client, Contact, ClientActivity, ClientStatus, Industry


# ═══════════════════════════════════════════════════════════
# CLIENT FILTER
# ═══════════════════════════════════════════════════════════

class ClientFilter(django_filters.FilterSet):
    """
    Filtres pour modèle Client
    
    Usage :
    GET /api/clients/?status=CUSTOMER
    GET /api/clients/?industry=IT&country=Tunisie
    GET /api/clients/?assigned_to=uuid-here
    GET /api/clients/?created_after=2024-01-01
    GET /api/clients/?search=Dupont
    
    Explication :
    django_filters génère automatiquement filtres
    Basé sur model fields
    Utilise indexes DB pour performance
    """
    
    # ───────────────────────────────────────────────────────
    # EXACT FILTERS (égalité stricte)
    # ───────────────────────────────────────────────────────
    
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=ClientStatus.choices,
        label='Statut'
    )
    # Explication :
    # ChoiceFilter : liste déroulante dans Swagger
    # SQL : WHERE status = 'CUSTOMER'
    # Utilise index sur status
    
    industry = django_filters.ChoiceFilter(
        field_name='industry',
        choices=Industry.choices,
        label='Secteur d\'activité'
    )
    # SQL : WHERE industry = 'IT'
    # Utilise index sur industry
    
    country = django_filters.CharFilter(
        field_name='country',
        lookup_expr='iexact',
        label='Pays'
    )
    # Explication lookup_expr='iexact' :
    # Case-insensitive exact match
    # SQL : WHERE LOWER(country) = LOWER('tunisie')
    # 'Tunisie' = 'tunisie' = 'TUNISIE'
    
    city = django_filters.CharFilter(
        field_name='city',
        lookup_expr='icontains',
        label='Ville'
    )
    # Explication lookup_expr='icontains' :
    # Case-insensitive contains (LIKE)
    # SQL : WHERE city ILIKE '%tunis%'
    # 'Tunis' trouve 'Tunis', 'La Marsa, Tunis', etc.
    
    # ───────────────────────────────────────────────────────
    # FOREIGN KEY FILTERS
    # ───────────────────────────────────────────────────────
    
    assigned_to = django_filters.UUIDFilter(
        field_name='assigned_to__id',
        label='Assigné à (UUID)'
    )
    # Explication :
    # Filtre par UUID du commercial
    # SQL : WHERE assigned_to_id = 'uuid-here'
    # Utilise index sur assigned_to
    
    assigned_to_name = django_filters.CharFilter(
        method='filter_by_assigned_name',
        label='Assigné à (nom)'
    )
    # Explication :
    # Custom method pour recherche par nom commercial
    # Plus user-friendly que UUID
    
    created_by = django_filters.UUIDFilter(
        field_name='created_by__id',
        label='Créé par (UUID)'
    )
    
    # ───────────────────────────────────────────────────────
    # BOOLEAN FILTERS
    # ───────────────────────────────────────────────────────
    
    is_active = django_filters.BooleanFilter(
        field_name='is_active',
        label='Actif'
    )
    # Explication :
    # GET /clients/?is_active=true → clients actifs
    # GET /clients/?is_active=false → clients inactifs
    # SQL : WHERE is_active = TRUE
    
    # ───────────────────────────────────────────────────────
    # DATE RANGE FILTERS
    # ───────────────────────────────────────────────────────
    
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Créé après'
    )
    # Explication lookup_expr='gte' :
    # Greater Than or Equal (>=)
    # SQL : WHERE created_at >= '2024-01-01'
    # Utilise index sur created_at
    
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Créé avant'
    )
    # Explication lookup_expr='lte' :
    # Less Than or Equal (<=)
    # SQL : WHERE created_at <= '2024-12-31'
    
    created_date = django_filters.DateFromToRangeFilter(
        field_name='created_at',
        label='Créé entre (range)'
    )
    # Explication DateFromToRangeFilter :
    # Range de dates
    # GET /clients/?created_date_after=2024-01-01&created_date_before=2024-12-31
    # SQL : WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'
    
    updated_after = django_filters.DateFilter(
        field_name='updated_at',
        lookup_expr='gte',
        label='Modifié après'
    )
    
    # ───────────────────────────────────────────────────────
    # SEARCH FILTER (multi-champs)
    # ───────────────────────────────────────────────────────
    
    search = django_filters.CharFilter(
        method='filter_search',
        label='Recherche globale'
    )
    # Explication :
    # Recherche dans plusieurs champs
    # Custom method pour Q objects
    
    # ───────────────────────────────────────────────────────
    # SPECIAL FILTERS
    # ───────────────────────────────────────────────────────
    
    has_contacts = django_filters.BooleanFilter(
        method='filter_has_contacts',
        label='A des contacts'
    )
    # Explication :
    # Filtre clients avec/sans contacts
    # Custom method pour COUNT
    
    has_tenant = django_filters.BooleanFilter(
        method='filter_has_tenant',
        label='A un tenant Microsoft'
    )
    # Explication :
    # Clients avec tenant Microsoft configuré
    # Utile pour provisionnement
    
    # ───────────────────────────────────────────────────────
    # CUSTOM FILTER METHODS
    # ───────────────────────────────────────────────────────
    
    def filter_by_assigned_name(self, queryset, name, value):
        """
        Filtre par nom du commercial assigné
        
        Args:
            queryset: QuerySet de base
            name: Nom du filtre ('assigned_to_name')
            value: Valeur recherchée
        
        Returns:
            QuerySet filtré
        
        Explication :
        Recherche dans first_name et last_name du commercial
        
        Usage :
        GET /clients/?assigned_to_name=Ahmed
        """
        return queryset.filter(
            Q(assigned_to__first_name__icontains=value) |
            Q(assigned_to__last_name__icontains=value) |
            Q(assigned_to__email__icontains=value)
        )
        # Explication Q :
        # OR condition sur plusieurs champs
        # SQL : WHERE (first_name ILIKE '%ahmed%' 
        #           OR last_name ILIKE '%ahmed%'
        #           OR email ILIKE '%ahmed%')
    
    def filter_search(self, queryset, name, value):
        """
        Recherche globale multi-champs
        
        Cherche dans :
        - company_name
        - email
        - phone
        - city
        - notes
        - contacts.first_name
        - contacts.last_name
        
        Usage :
        GET /clients/?search=Dupont
        
        Explication :
        Full-text search basique
        Pour production : utiliser PostgreSQL full-text search
        """
        return queryset.filter(
            Q(company_name__icontains=value) |
            Q(email__icontains=value) |
            Q(phone__icontains=value) |
            Q(city__icontains=value) |
            Q(notes__icontains=value) |
            Q(contacts__first_name__icontains=value) |
            Q(contacts__last_name__icontains=value) |
            Q(contacts__email__icontains=value)
        ).distinct()
        # Explication distinct() :
        # Évite doublons si plusieurs contacts matchent
        # SQL : SELECT DISTINCT ...
    
    def filter_has_contacts(self, queryset, name, value):
        """
        Filtre clients avec/sans contacts
        
        Usage :
        GET /clients/?has_contacts=true → clients avec contacts
        GET /clients/?has_contacts=false → clients sans contacts
        
        Explication :
        Utilise COUNT aggregation
        """
        from django.db.models import Count
        
        queryset = queryset.annotate(
            contacts_count=Count('contacts')
        )
        
        if value:
            # A des contacts
            return queryset.filter(contacts_count__gt=0)
        else:
            # Aucun contact
            return queryset.filter(contacts_count=0)
        # Explication :
        # SQL : SELECT clients.*, COUNT(contacts.id)
        #       FROM clients LEFT JOIN contacts
        #       GROUP BY clients.id
        #       HAVING COUNT(contacts.id) > 0
    
    def filter_has_tenant(self, queryset, name, value):
        """
        Filtre clients avec/sans tenant Microsoft
        
        Explication :
        Clients configurés pour provisionnement M365
        """
        if value:
            # A un tenant
            return queryset.exclude(tenant_microsoft='')
        else:
            # Pas de tenant
            return queryset.filter(
                Q(tenant_microsoft='') | Q(tenant_microsoft__isnull=True)
            )
    
    # ───────────────────────────────────────────────────────
    # META
    # ───────────────────────────────────────────────────────
    
    class Meta:
        model = Client
        fields = {
            'status': ['exact'],
            'industry': ['exact'],
            'country': ['exact', 'icontains'],
            'city': ['icontains'],
            'is_active': ['exact'],
            'created_at': ['gte', 'lte', 'exact'],
            'updated_at': ['gte', 'lte'],
        }
        # Explication Meta.fields :
        # Génère automatiquement filtres basiques
        # Format : {field_name: [lookup_types]}
        # 
        # Exemple généré :
        # - status__exact (déjà défini manuellement)
        # - country__exact
        # - country__icontains
        # - created_at__gte
        # - created_at__lte
        # etc.


# ═══════════════════════════════════════════════════════════
# CONTACT FILTER
# ═══════════════════════════════════════════════════════════

class ContactFilter(django_filters.FilterSet):
    """
    Filtres pour modèle Contact
    
    Usage :
    GET /api/contacts/?client=uuid-here
    GET /api/contacts/?is_primary=true
    GET /api/contacts/?search=Jean
    """
    
    # ───────────────────────────────────────────────────────
    # BASIC FILTERS
    # ───────────────────────────────────────────────────────
    
    client = django_filters.UUIDFilter(
        field_name='client__id',
        label='Client (UUID)'
    )
    # SQL : WHERE client_id = 'uuid'
    
    is_primary = django_filters.BooleanFilter(
        field_name='is_primary',
        label='Contact principal'
    )
    
    # ───────────────────────────────────────────────────────
    # SEARCH
    # ───────────────────────────────────────────────────────
    
    search = django_filters.CharFilter(
        method='filter_search',
        label='Recherche'
    )
    
    first_name = django_filters.CharFilter(
        field_name='first_name',
        lookup_expr='icontains',
        label='Prénom'
    )
    
    last_name = django_filters.CharFilter(
        field_name='last_name',
        lookup_expr='icontains',
        label='Nom'
    )
    
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        label='Email'
    )
    
    position = django_filters.CharFilter(
        field_name='position',
        lookup_expr='icontains',
        label='Poste'
    )
    
    # ───────────────────────────────────────────────────────
    # CUSTOM METHODS
    # ───────────────────────────────────────────────────────
    
    def filter_search(self, queryset, name, value):
        """
        Recherche globale contacts
        
        Cherche dans :
        - first_name, last_name
        - email
        - position
        - phone, mobile
        """
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(email__icontains=value) |
            Q(position__icontains=value) |
            Q(phone__icontains=value) |
            Q(mobile__icontains=value)
        )
    
    class Meta:
        model = Contact
        fields = {
            'first_name': ['icontains'],
            'last_name': ['icontains'],
            'email': ['icontains'],
            'is_primary': ['exact'],
        }


# ═══════════════════════════════════════════════════════════
# CLIENT ACTIVITY FILTER
# ═══════════════════════════════════════════════════════════

class ClientActivityFilter(django_filters.FilterSet):
    """
    Filtres pour activités clients
    
    Usage :
    GET /api/activities/?client=uuid
    GET /api/activities/?activity_type=CREATED
    GET /api/activities/?user=uuid
    GET /api/activities/?created_after=2024-01-01
    """
    
    # ───────────────────────────────────────────────────────
    # BASIC FILTERS
    # ───────────────────────────────────────────────────────
    
    client = django_filters.UUIDFilter(
        field_name='client__id',
        label='Client (UUID)'
    )
    
    activity_type = django_filters.ChoiceFilter(
        field_name='activity_type',
        choices=ClientActivity.ActivityType.choices,
        label='Type d\'activité'
    )
    
    user = django_filters.UUIDFilter(
        field_name='user__id',
        label='Utilisateur (UUID)'
    )
    
    # ───────────────────────────────────────────────────────
    # DATE FILTERS
    # ───────────────────────────────────────────────────────
    
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Créé après'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Créé avant'
    )
    
    date_range = django_filters.DateFromToRangeFilter(
        field_name='created_at',
        label='Période'
    )
    # Usage :
    # GET /activities/?date_range_after=2024-01-01&date_range_before=2024-12-31
    
    # ───────────────────────────────────────────────────────
    # SEARCH
    # ───────────────────────────────────────────────────────
    
    search = django_filters.CharFilter(
        field_name='description',
        lookup_expr='icontains',
        label='Recherche dans description'
    )
    
    class Meta:
        model = ClientActivity
        fields = {
            'activity_type': ['exact'],
            'created_at': ['gte', 'lte'],
        }


# ═══════════════════════════════════════════════════════════
# ORDERING FILTER
# ═══════════════════════════════════════════════════════════

class ClientOrderingFilter(django_filters.OrderingFilter):
    """
    Filtre de tri personnalisé
    
    Usage :
    GET /clients/?ordering=company_name
    GET /clients/?ordering=-created_at (DESC)
    GET /clients/?ordering=status,company_name (multi-sort)
    
    Explication :
    - Préfixe '-' = DESC
    - Pas de préfixe = ASC
    - Virgule = tri multi-colonnes
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Champs autorisés pour tri
        self.extra['choices'] = [
            ('company_name', 'Raison sociale (A-Z)'),
            ('-company_name', 'Raison sociale (Z-A)'),
            ('created_at', 'Date création (anciens)'),
            ('-created_at', 'Date création (récents)'),
            ('updated_at', 'Date modification (anciens)'),
            ('-updated_at', 'Date modification (récents)'),
            ('status', 'Statut (A-Z)'),
            ('-status', 'Statut (Z-A)'),
            ('industry', 'Secteur (A-Z)'),
            ('-industry', 'Secteur (Z-A)'),
            ('city', 'Ville (A-Z)'),
            ('-city', 'Ville (Z-A)'),
        ]
        # Explication :
        # Liste affichée dans Swagger UI
        # User-friendly dropdown


# ═══════════════════════════════════════════════════════════
# ADVANCED FILTERS (Custom Complex Filters)
# ═══════════════════════════════════════════════════════════

class ClientAdvancedFilter(ClientFilter):
    """
    Filtres avancés pour rapports et analytics
    
    Hérite de ClientFilter
    Ajoute filtres complexes
    
    Usage :
    Endpoints spéciaux analytics/reports
    """
    
    # ───────────────────────────────────────────────────────
    # AGGREGATION FILTERS
    # ───────────────────────────────────────────────────────
    
    min_contacts = django_filters.NumberFilter(
        method='filter_min_contacts',
        label='Nombre minimum de contacts'
    )
    # Usage :
    # GET /clients/?min_contacts=3
    # → Clients avec au moins 3 contacts
    
    max_contacts = django_filters.NumberFilter(
        method='filter_max_contacts',
        label='Nombre maximum de contacts'
    )
    
    has_activity_in_days = django_filters.NumberFilter(
        method='filter_activity_recent',
        label='Activité dans les N derniers jours'
    )
    # Usage :
    # GET /clients/?has_activity_in_days=30
    # → Clients avec activité dans les 30 derniers jours
    
    # ───────────────────────────────────────────────────────
    # CUSTOM METHODS
    # ───────────────────────────────────────────────────────
    
    def filter_min_contacts(self, queryset, name, value):
        """Clients avec minimum N contacts"""
        from django.db.models import Count
        
        return queryset.annotate(
            contacts_count=Count('contacts')
        ).filter(contacts_count__gte=value)
        # SQL : HAVING COUNT(contacts) >= N
    
    def filter_max_contacts(self, queryset, name, value):
        """Clients avec maximum N contacts"""
        from django.db.models import Count
        
        return queryset.annotate(
            contacts_count=Count('contacts')
        ).filter(contacts_count__lte=value)
    
    def filter_activity_recent(self, queryset, name, value):
        """Clients avec activité récente"""
        from datetime import timedelta
        from django.utils import timezone
        from django.db.models import Max
        
        cutoff_date = timezone.now() - timedelta(days=value)
        
        return queryset.annotate(
            last_activity=Max('activities__created_at')
        ).filter(last_activity__gte=cutoff_date)
        # Explication :
        # Calcule date dernière activité
        # Filtre si > cutoff_date
        # SQL : HAVING MAX(activities.created_at) >= 'date'


# ═══════════════════════════════════════════════════════════
# SEARCH FILTER CONFIGURATION
# ═══════════════════════════════════════════════════════════

"""
Configuration pour DRF SearchFilter

Usage dans ViewSet :
from rest_framework.filters import SearchFilter

class ClientViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ClientFilter
    search_fields = ['company_name', 'email', 'phone', 'city']
    ordering_fields = ['company_name', 'created_at', 'status']
    ordering = ['-created_at']  # Default ordering

Explication :
SearchFilter : GET /clients/?search=Dupont
→ Cherche dans search_fields
→ Case-insensitive
→ Utilise ILIKE

OrderingFilter : GET /clients/?ordering=-created_at
→ Tri dynamique
→ Multi-colonnes supporté
"""