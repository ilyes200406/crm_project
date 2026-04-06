"""
EXPLICATION :

Serializers = Transformation données DB ↔ JSON

Architecture :
- Serializers en lecture (affichage)
- Serializers en écriture (création/update)
- Validation des données
- Nested serializers pour relations
- Optimisation queries (select_related)

Avantages :
- Validation automatique
- Transformation propre
- Relations gérées
- Code réutilisable
- Documentation auto (Swagger)

Performance :
- ReadOnly serializers légers
- Write serializers avec validation
- Évite N+1 avec context
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Client, Contact, ClientActivity, Industry
from .validators import (
    validate_client_data,
    validate_contact_data,
    normalize_phone_number,
)
from ..users.models.users import User


# ═══════════════════════════════════════════════════════════
# USER SERIALIZERS (pour relations)
# ═══════════════════════════════════════════════════════════

class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer minimal pour Utilisateur
    
    Usage :
    Affichage dans relations (assigned_to, created_by)
    Évite exposition de données sensibles
    
    Explication :
    Read-only pour sécurité
    Pas de password, email complet exposé
    """
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    # Explication source='get_full_name' :
    # Appelle method du model
    # Retourne first_name + last_name
    
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role']
        read_only_fields = ['id', 'email', 'full_name', 'role']
        # Explication read_only_fields :
        # Ces champs jamais modifiables via API
        # Sécurité : empêche mass assignment


# ═══════════════════════════════════════════════════════════
# CONTACT SERIALIZERS
# ═══════════════════════════════════════════════════════════

class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer complet pour Contact
    
    Usage :
    - Liste contacts d'un client
    - Détails contact
    - Création/modification contact
    
    Explication :
    CRUD complet avec validation
    """
    
    full_name = serializers.SerializerMethodField()
    # Explication SerializerMethodField :
    # Champ calculé custom
    # Appelle get_full_name()
    
    client_name = serializers.CharField(
        source='client.company_name',
        read_only=True
    )
    # Explication :
    # Affiche nom client dans réponse
    # Évite query additionnelle si client en select_related
    
    class Meta:
        model = Contact
        fields = [
            'id',
            'client',
            'client_name',
            'first_name',
            'last_name',
            'full_name',
            'position',
            'email',
            'phone',
            'is_primary',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'client_name', 'full_name']
    
    def get_full_name(self, obj):
        """Calcule nom complet"""
        return obj.get_full_name()
    
    def validate(self, data):
        """
        Validation globale
        
        Explication :
        Appelé après validation champs individuels
        Validation inter-champs
        
        Flow :
        1. Validation champs (validate_email, etc.)
        2. validate() (cette méthode)
        3. create() ou update()
        """
        
        # Récupère client depuis context ou data
        client = data.get('client') or getattr(self.instance, 'client', None)
        
        # Appelle validator custom
        validate_contact_data(data, client=client)
        
        return data


class ContactCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour création contact
    
    Différence avec ContactSerializer :
    - Pas de client dans fields (fourni via URL)
    - Validation création spécifique
    
    Usage :
    POST /clients/{client_id}/contacts/
    """
    
    class Meta:
        model = Contact
        fields = [
            'first_name',
            'last_name',
            'position',
            'email',
            'phone',
            'is_primary',
            'notes',
        ]
    
    def validate(self, data):
        """Validation avec client du context"""
        client = self.context.get('client')
        validate_contact_data(data, client=client)
        return data


class ContactMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer minimal pour nested display
    
    Usage :
    Affichage dans ClientDetailSerializer
    Liste légère sans tous les détails
    
    Explication :
    Performance : seulement champs essentiels
    """
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id',
            'full_name',
            'position',
            'email',
            'phone',
            'is_primary',
        ]
        read_only_fields = fields


# ═══════════════════════════════════════════════════════════
# CLIENT ACTIVITY SERIALIZERS
# ═══════════════════════════════════════════════════════════

class ClientActivitySerializer(serializers.ModelSerializer):
    """
    Serializer pour activités client
    
    Usage :
    - Historique activités
    - Audit trail
    - Timeline client
    
    Explication :
    Read-only (activités créées par système)
    """
    
    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True,
        default=None
    )
    # Explication default=None :
    # Si user supprimé (SET_NULL), retourne None
    # Pas d'erreur AttributeError
    
    activity_type_display = serializers.CharField(
        source='get_activity_type_display',
        read_only=True
    )
    # Explication :
    # 'CREATED' → 'Créé'
    # Django built-in pour choices
    
    client_name = serializers.CharField(
        source='client.company_name',
        read_only=True
    )
    
    class Meta:
        model = ClientActivity
        fields = [
            'id',
            'client',
            'client_name',
            'activity_type',
            'activity_type_display',
            'user',
            'user_name',
            'description',
            'metadata',
            'ip_address',
            'created_at',
        ]
        read_only_fields = fields
        # Explication :
        # Tous les champs read-only
        # Création via services.log_client_activity()


# ═══════════════════════════════════════════════════════════
# CLIENT SERIALIZERS (Base)
# ═══════════════════════════════════════════════════════════

class ClientListSerializer(serializers.ModelSerializer):
    """
    Serializer pour liste clients
    
    Usage :
    GET /clients/
    
    Explication :
    Léger pour performance
    Pas de nested data (contacts, activités)
    Optimisé pour pagination
    
    Performance :
    - Pas de N+1 queries
    - select_related sur FK
    - Pas de prefetch_related (pas de nested)
    """
    
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name',
        read_only=True,
        default=None
    )
    
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True,
        default=None
    )
    
    industry_display = serializers.CharField(
        source='get_industry_display',
        read_only=True
    )

    # Stats (si annotées via selectors)
    contacts_count = serializers.IntegerField(read_only=True, default=0)
    activities_count = serializers.IntegerField(read_only=True, default=0)
    last_activity_date = serializers.DateTimeField(read_only=True, default=None)

    class Meta:
        model = Client
        fields = [
            'id',
            'company_name',
            'email',
            'phone',
            'industry',
            'industry_display',
            'assigned_to',
            'assigned_to_name',
            'created_by',
            'created_by_name',
            'is_active',
            'created_at',
            'updated_at',
            # Stats
            'contacts_count',
            'activities_count',
            'last_activity_date',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name',
        ]


class ClientDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour un client
    
    Usage :
    GET /clients/{id}/
    
    Explication :
    Complet avec toutes les relations
    - Contacts nested
    - Activités récentes
    - User details
    
    Performance :
    Nécessite prefetch_related dans selector
    """
    
    # ───────────────────────────────────────────────────────
    # USER RELATIONS
    # ───────────────────────────────────────────────────────
    
    assigned_to_detail = UserMinimalSerializer(
        source='assigned_to',
        read_only=True
    )
    # Explication :
    # Nested serializer pour détails complets
    # Affiche {id, email, full_name, role}
    
    created_by_detail = UserMinimalSerializer(
        source='created_by',
        read_only=True
    )
    
    # ───────────────────────────────────────────────────────
    # NESTED RELATIONS
    # ───────────────────────────────────────────────────────
    
    contacts = ContactMinimalSerializer(many=True, read_only=True)
    # Explication many=True :
    # Relation OneToMany
    # Serialise liste de contacts
    # Utilise prefetch_related('contacts')
    
    recent_activities = serializers.SerializerMethodField()
    # Explication :
    # Limite à 10 activités récentes
    # Custom method pour contrôle
    
    # ───────────────────────────────────────────────────────
    # DISPLAY FIELDS
    # ───────────────────────────────────────────────────────
    
    industry_display = serializers.CharField(
        source='get_industry_display',
        read_only=True
    )

    class Meta:
        model = Client
        fields = [
            'id',
            'company_name',
            'industry',
            'industry_display',
            'email',
            'phone',
            'website',
            'address',
            'tenant_microsoft',
            'notes',
            'assigned_to',
            'assigned_to_detail',
            'created_by',
            'created_by_detail',
            'is_active',
            'created_at',
            'updated_at',
            # Nested
            'contacts',
            'recent_activities',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'created_by',
        ]
    
    def get_recent_activities(self, obj):
        """
        Retourne 10 activités récentes
        
        Explication :
        obj.activities préchargé via prefetch_related
        → Pas de query additionnelle
        Slice [:10] en Python (déjà chargé)
        """
        activities = obj.activities.all()[:10]
        return ClientActivitySerializer(activities, many=True).data


# ═══════════════════════════════════════════════════════════
# CLIENT WRITE SERIALIZERS
# ═══════════════════════════════════════════════════════════

class ClientCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour création client
    
    Usage :
    POST /clients/
    
    Explication :
    - Validation stricte
    - Normalisation données
    - Business rules
    
    Flow :
    1. validate_<field>() pour chaque champ
    2. validate() global
    3. create() appelé par view
    4. Service crée réellement (pas serializer)
    """
    
    class Meta:
        model = Client
        fields = [
            'company_name',
            'industry',
            'email',
            'phone',
            'website',
            'address',
            'tenant_microsoft',
            'notes',
            'assigned_to',
        ]

    def validate_email(self, value):
        from .selectors import get_client_by_email
        existing = get_client_by_email(value, is_active=True)
        if existing:
            raise serializers.ValidationError(
                f'Un client actif existe déjà avec cet email : {existing.company_name}'
            )
        return value

    def validate_phone(self, value):
        if value:
            return normalize_phone_number(value)
        return value

    def validate(self, data):
        validate_client_data(data)
        return data


class ClientUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mise à jour client
    
    Usage :
    PUT/PATCH /clients/{id}/
    
    Différence avec Create :
    - Validation transition statut
    - Champs optionnels (partial update)
    """
    
    class Meta:
        model = Client
        fields = [
            'company_name',
            'industry',
            'email',
            'phone',
            'website',
            'address',
            'tenant_microsoft',
            'notes',
            'assigned_to',
        ]

    def validate_email(self, value):
        from .selectors import get_client_by_email
        instance = self.instance
        existing = get_client_by_email(value, is_active=True)
        if existing and existing.id != instance.id:
            raise serializers.ValidationError(
                f'Un client existe déjà avec cet email : {existing.company_name}'
            )
        return value

    def validate_phone(self, value):
        if value:
            return normalize_phone_number(value)
        return value

    def validate(self, data):
        validate_client_data(data)
        return data


class ClientAssignSerializer(serializers.Serializer):
    """
    Serializer pour assignation client
    
    Usage :
    POST /clients/{id}/assign/
    Body : {assigned_to: uuid}
    
    Explication :
    Simple serializer (pas ModelSerializer)
    Juste validation UUID commercial
    """
    
    assigned_to = serializers.UUIDField(required=True)
    
    def validate_assigned_to(self, value):
        """
        Valide que UUID = commercial actif
        
        Explication :
        Business rule stricte
        Seulement COMMERCIAL actif
        """
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Utilisateur non trouvé')
        
        if user.role != 'COMMERCIAL':
            raise serializers.ValidationError(
                'Seuls les commerciaux peuvent être assignés'
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                'Impossible d\'assigner à un utilisateur inactif'
            )
        
        return value


# ═══════════════════════════════════════════════════════════
# STATS SERIALIZERS
# ═══════════════════════════════════════════════════════════

class ClientStatsSerializer(serializers.Serializer):
    """
    Serializer pour statistiques dashboard
    
    Usage :
    GET /clients/stats/
    
    Explication :
    Pas de model (Serializer simple)
    Juste structure JSON
    """
    
    total_clients = serializers.IntegerField()
    by_industry = serializers.DictField(child=serializers.IntegerField())
    recent_count = serializers.IntegerField()


class ClientExportSerializer(serializers.ModelSerializer):
    """
    Serializer pour export CSV/Excel
    
    Usage :
    GET /clients/export/
    
    Explication :
    Format plat (pas de nested)
    Tous les champs texte
    Facile à exporter
    """
    
    assigned_to_email = serializers.CharField(
        source='assigned_to.email',
        read_only=True,
        default=''
    )
    
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name',
        read_only=True,
        default=''
    )
    
    industry_display = serializers.CharField(
        source='get_industry_display',
        read_only=True
    )

    class Meta:
        model = Client
        fields = [
            'id',
            'company_name',
            'industry_display',
            'email',
            'phone',
            'website',
            'address',
            'assigned_to_email',
            'assigned_to_name',
            'is_active',
            'created_at',
            'updated_at',
        ]


# ═══════════════════════════════════════════════════════════
# BULK OPERATION SERIALIZERS
# ═══════════════════════════════════════════════════════════

class ClientBulkUpdateSerializer(serializers.Serializer):
    """
    Serializer pour bulk update
    
    Usage :
    POST /clients/bulk-update/
    Body : {
        client_ids: [uuid1, uuid2, ...],
        data: {status: 'CUSTOMER', ...}
    }
    
    Explication :
    ADMIN seulement
    Update multiple clients à la fois
    """
    
    client_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )
    # Explication :
    # Liste d'UUIDs
    # Min 1, max 100 (limite sécurité)
    
    data = serializers.DictField(required=True)
    # Explication :
    # Données à appliquer
    # Ex: {status: 'CUSTOMER', industry: 'IT'}
    
    def validate_data(self, value):
        """
        Valide données bulk
        
        Explication :
        Seulement certains champs bulk-updatable
        Status, industry, assigned_to
        Pas email (unicité)
        """
        allowed_fields = ['industry', 'assigned_to', 'notes']

        for field in value.keys():
            if field not in allowed_fields:
                raise serializers.ValidationError(
                    f'Champ "{field}" non autorisé pour bulk update. '
                    f'Champs autorisés : {", ".join(allowed_fields)}'
                )

        return value


class ClientBulkDeleteSerializer(serializers.Serializer):
    """
    Serializer pour bulk delete (soft)
    
    Usage :
    POST /clients/bulk-delete/
    Body : {client_ids: [uuid1, uuid2, ...]}
    """
    
    client_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=50
    )
    # Explication :
    # Max 50 pour delete (plus dangereux)