"""
EXPLICATION :

Services = Couche de logique métier

Architecture pattern :
- Toute la business logic ici (PAS dans views)
- Services orchestrent : validation → création/update → audit
- Transactions atomiques (data integrity)
- Point unique pour écriture (Create, Update, Delete)

Avantages :
- Views ultra-minces (juste appels services)
- Logique réutilisable (API, admin, scripts)
- Testable isolément
- Transactions gérées proprement
- Audit centralisé

Principe :
Views appellent services pour écrire
→ Services valident + écrivent + loggent
→ Retournent objet créé/modifié
"""

from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from .models import Client, Contact, ClientActivity
from .validators import (
    validate_client_data,
    validate_contact_data,
    normalize_phone_number,
)
from .selectors import get_client_by_id, get_client_by_email


@transaction.atomic
def create_client(*, data: dict, user, ip_address=None):
    """
    Crée un nouveau client
    
    Args:
        data: Données client validées
        user: Utilisateur créateur
        ip_address: IP pour audit
    
    Returns:
        Client instance créée
    
    Raises:
        ValidationError: Si données invalides
        PermissionDenied: Si user sans permission
    
    Explication :
    @transaction.atomic : CRITICAL
    - Tout réussit ou tout échoue (rollback automatique)
    - Garantit cohérence données
    
    Flow :
    1. Vérification permissions
    2. Validation données
    3. Normalisation
    4. Vérification unicité email
    5. Création client
    6. Log activité
    7. Retour client créé
    
    Performance :
    Transaction = 1 commit DB
    Rollback automatique si erreur
    """
    
    # ───────────────────────────────────────────────────────
    # 1. VÉRIFICATION PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    # ───────────────────────────────────────────────────────
    # 2. VALIDATION DONNÉES
    # ───────────────────────────────────────────────────────
    
    validate_client_data(data)
    # Explication :
    # Appelle validator composite
    # Lève ValidationError si problème
    # → 400 Bad Request
    
    # ───────────────────────────────────────────────────────
    # 3. NORMALISATION
    # ───────────────────────────────────────────────────────
    
    if 'phone' in data and data['phone']:
        data['phone'] = normalize_phone_number(data['phone'])
    
    # Explication normalisation :
    # "+216 12 345 678" → "+21612345678"
    # Format uniforme en DB
    # Facilite recherches/comparaisons
    
    # ───────────────────────────────────────────────────────
    # 4. VÉRIFICATION UNICITÉ EMAIL
    # ───────────────────────────────────────────────────────
    
    email = data.get('email')
    if email:
        existing = get_client_by_email(email, is_active=True)
        if existing:
            raise ValidationError({
                'email': f'Un client actif existe déjà avec cet email : {existing.company_name}'
            })
    # Explication :
    # Constraint DB : email unique pour clients actifs
    # Vérification explicite pour message clair
    # Alternative : laisser DB lever IntegrityError (moins user-friendly)
    
    # ───────────────────────────────────────────────────────
    # 5. ASSIGNATION AUTO
    # ───────────────────────────────────────────────────────
    
    # Si commercial crée → s'auto-assigne
    if user.role_id == 'COMMERCIAL' and not data.get('assigned_to'):
        data['assigned_to'] = user
    # Explication business rule :
    # Commercial crée client → devient responsable
    # Admin peut assigner à quelqu'un d'autre
    
    # Créateur
    data['created_by'] = user
    
    # ───────────────────────────────────────────────────────
    # 6. CRÉATION CLIENT
    # ───────────────────────────────────────────────────────
    
    client = Client.objects.create(**data)
    # Explication :
    # Django ORM crée instance + INSERT en DB
    # UUID généré automatiquement
    # Timestamps (created_at) auto
    
    # ───────────────────────────────────────────────────────
    # 7. LOG ACTIVITÉ
    # ───────────────────────────────────────────────────────
    
    log_client_activity(
        client=client,
        activity_type=ClientActivity.ActivityType.CREATED,
        user=user,
        description=f'Client créé : {client.company_name}',
        ip_address=ip_address
    )
    # Explication audit :
    # Traçabilité complète
    # Qui a créé, quand, d'où (IP)
    
    # ───────────────────────────────────────────────────────
    # 8. RETOUR
    # ───────────────────────────────────────────────────────
    
    return client
    # Explication :
    # Retourne instance Django
    # View serialize → JSON


# ═══════════════════════════════════════════════════════════
# CLIENT UPDATE
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def update_client(*, client_id, data: dict, user, ip_address=None):
    """
    Met à jour un client existant
    
    Args:
        client_id: UUID du client
        data: Données à mettre à jour (partial)
        user: Utilisateur modifiant
        ip_address: IP pour audit
    
    Returns:
        Client instance mise à jour
    
    Raises:
        ValidationError: Si données invalides
        PermissionDenied: Si user sans permission
        Http404: Si client n'existe pas
    
    Explication :
    Update partiel (PATCH) ou complet (PUT)
    Validation transitions de statut
    Audit trail complet
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION CLIENT
    # ───────────────────────────────────────────────────────
    
    client = get_client_by_id(client_id, user=user, prefetch_all=False)
    # Explication :
    # Vérifie existence + permissions RBAC
    # 404 si n'existe pas
    # 403 si commercial pas owner
    
    # ───────────────────────────────────────────────────────
    # 2. VÉRIFICATION PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    if user.role_id == 'COMMERCIAL' and client.assigned_to != user:
        raise PermissionDenied(
            'Vous ne pouvez modifier que vos propres clients'
        )
    
    # ───────────────────────────────────────────────────────
    # 3. VALIDATION DONNÉES
    # ───────────────────────────────────────────────────────
    
    validate_client_data(data)
    
    # ───────────────────────────────────────────────────────
    # 4. VALIDATION TRANSITION STATUT
    # ───────────────────────────────────────────────────────
    
    # ───────────────────────────────────────────────────────
    # 5. NORMALISATION
    # ───────────────────────────────────────────────────────
    
    if 'phone' in data and data['phone']:
        data['phone'] = normalize_phone_number(data['phone'])
    
    # ───────────────────────────────────────────────────────
    # 6. VÉRIFICATION EMAIL UNIQUE
    # ───────────────────────────────────────────────────────
    
    if 'email' in data and data['email'] != client.email:
        existing = get_client_by_email(data['email'], is_active=True)
        if existing and existing.id != client.id:
            raise ValidationError({
                'email': f'Un client existe déjà avec cet email : {existing.company_name}'
            })
    
    # ───────────────────────────────────────────────────────
    # 7. DÉTECTION CHANGEMENTS
    # ───────────────────────────────────────────────────────
    
    changes = []
    metadata = {}
    
    for field, new_value in data.items():
        old_value = getattr(client, field)
        if old_value != new_value:
            changes.append(field)
            metadata[field] = {
                'old': str(old_value),
                'new': str(new_value)
            }
    # Explication audit :
    # Détecte champs modifiés
    # Log old/new values
    # Traçabilité complète
    
    # ───────────────────────────────────────────────────────
    # 8. UPDATE CLIENT
    # ───────────────────────────────────────────────────────
    
    for field, value in data.items():
        setattr(client, field, value)
    
    client.save()
    # Explication :
    # setattr() modifie attributs
    # save() → UPDATE en DB
    # updated_at auto-mis à jour
    
    # ───────────────────────────────────────────────────────
    # 9. LOG ACTIVITÉ
    # ───────────────────────────────────────────────────────
    
    if changes:
        description = f'Client modifié : {", ".join(changes)}'
        log_client_activity(
            client=client,
            activity_type=ClientActivity.ActivityType.UPDATED,
            user=user,
            description=description,
            metadata=metadata,
            ip_address=ip_address
        )
    return client


# ═══════════════════════════════════════════════════════════
# CLIENT SOFT DELETE
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def delete_client(*, client_id, user, ip_address=None):
    """
    Soft delete d'un client
    
    Explication :
    is_active = False (pas de DELETE FROM)
    
    Business rules :
    - Seul admin peut soft delete
    - Commercial ne peut pas (évite pertes données)
    
    Garde :
    - Tous les contacts
    - Toutes les activités
    - Toutes les relations (paniers, contrats)
    
    Récupération possible via restore_client()
    """
    
    # ───────────────────────────────────────────────────────
    # PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    # ───────────────────────────────────────────────────────
    # RÉCUPÉRATION + SOFT DELETE
    # ───────────────────────────────────────────────────────
    
    client = get_client_by_id(client_id, user=user, prefetch_all=False)
    
    if not client.is_active:
        raise ValidationError('Ce client est déjà désactivé')
    
    client.soft_delete()
    # Explication :
    # Appelle méthode model
    # is_active = False
    # UPDATE au lieu de DELETE
    
    # ───────────────────────────────────────────────────────
    # LOG ACTIVITÉ
    # ───────────────────────────────────────────────────────
    
    log_client_activity(
        client=client,
        activity_type=ClientActivity.ActivityType.DELETED,
        user=user,
        description=f'Client désactivé : {client.company_name}',
        ip_address=ip_address
    )

    return client


# ═══════════════════════════════════════════════════════════
# CLIENT RESTORE
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def restore_client(*, client_id, user, ip_address=None):
    """
    Réactive un client désactivé
    
    Explication :
    is_active = True
    Récupération après soft delete
    """
    
    # Récupère même si inactif
    client = Client.objects.select_related('assigned_to', 'created_by').get(id=client_id)
    
    if client.is_active:
        raise ValidationError('Ce client est déjà actif')
    
    client.restore()
    log_client_activity(
        client=client,
        activity_type=ClientActivity.ActivityType.RESTORED,
        user=user,
        description=f'Client réactivé : {client.company_name}',
        ip_address=ip_address
    )
    return client


# ═══════════════════════════════════════════════════════════
# CLIENT ASSIGNMENT
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def assign_client(*, client_id, assigned_to_id, user, ip_address=None):
    """
    Assigne un client à un commercial
    
    Args:
        client_id: UUID client
        assigned_to_id: UUID commercial cible
        user: Utilisateur effectuant assignation
        ip_address: IP audit
    
    Business rules :
    - Seul admin peut ré-assigner
    - assigned_to doit être COMMERCIAL
    
    Explication :
    Workflow métier important
    Change responsabilité client
    Audit trail obligatoire
    """
    
    # ───────────────────────────────────────────────────────
    # PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    # ───────────────────────────────────────────────────────
    # RÉCUPÉRATION CLIENT
    # ───────────────────────────────────────────────────────
    
    client = get_client_by_id(client_id, user=user, prefetch_all=False)
    
    # ───────────────────────────────────────────────────────
    # VALIDATION COMMERCIAL CIBLE
    # ───────────────────────────────────────────────────────
    
    from ..users.models.users import User
    
    try:
        new_assignee = User.objects.get(id=assigned_to_id)
    except User.DoesNotExist:
        raise ValidationError({'assigned_to': 'Utilisateur non trouvé'})
    
    if new_assignee.role_id != 'COMMERCIAL':
        raise ValidationError({
            'assigned_to': 'Seuls les commerciaux peuvent être assignés à des clients'
        })
    
    if not new_assignee.is_active:
        raise ValidationError({
            'assigned_to': 'Impossible d\'assigner à un utilisateur inactif'
        })
    
    # ───────────────────────────────────────────────────────
    # ASSIGNATION
    # ───────────────────────────────────────────────────────
    
    old_assignee = client.assigned_to
    
    if old_assignee == new_assignee:
        raise ValidationError('Le client est déjà assigné à ce commercial')
    
    client.assigned_to = new_assignee
    client.save(update_fields=['assigned_to', 'updated_at'])
    
    # ───────────────────────────────────────────────────────
    # LOG ACTIVITÉ
    # ───────────────────────────────────────────────────────
    
    description = f'Client réassigné : '
    if old_assignee:
        description += f'{old_assignee.get_full_name()} → {new_assignee.get_full_name()}'
    else:
        description += f'Assigné à {new_assignee.get_full_name()}'

    log_client_activity(
        client=client,
        activity_type=ClientActivity.ActivityType.ASSIGNED,
        user=user,
        description=description,
        metadata={
            'old_assignee_id': str(old_assignee.id) if old_assignee else None,
            'old_assignee_name': old_assignee.get_full_name() if old_assignee else None,
            'new_assignee_id': str(new_assignee.id),
            'new_assignee_name': new_assignee.get_full_name(),
        },
        ip_address=ip_address
    )
    return client


# ═══════════════════════════════════════════════════════════
# CONTACT SERVICES
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def create_contact(*, client_id, data: dict, user, ip_address=None):
    """
    Crée un contact pour un client
    
    Business rules :
    - Un seul contact principal par client
    - Si is_primary=True, démote l'ancien principal
    
    Explication :
    Relation composition : contact ⊂ client
    """
    
    # ───────────────────────────────────────────────────────
    # PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    client = get_client_by_id(client_id, user=user, prefetch_all=False)
    
    if user.role_id == 'COMMERCIAL' and client.assigned_to != user:
        raise PermissionDenied(
            'Vous ne pouvez ajouter de contacts que pour vos propres clients'
        )

    # ───────────────────────────────────────────────────────
    # VALIDATION
    # ───────────────────────────────────────────────────────
    
    validate_contact_data(data, client=client)
    
    # ───────────────────────────────────────────────────────
    # GESTION CONTACT PRINCIPAL
    # ───────────────────────────────────────────────────────
    
    if data.get('is_primary', False):
        # Démote l'ancien contact principal
        Contact.objects.filter(
            client=client,
            is_primary=True
        ).update(is_primary=False)
        # Explication :
        # Un seul principal par client
        # UPDATE contacts SET is_primary = False WHERE ...
    
    # ───────────────────────────────────────────────────────
    # CRÉATION CONTACT
    # ───────────────────────────────────────────────────────
    
    data['client'] = client
    contact = Contact.objects.create(**data)
    
    # ───────────────────────────────────────────────────────
    # LOG ACTIVITÉ
    # ───────────────────────────────────────────────────────
    log_client_activity(
        client=client,
        activity_type=ClientActivity.ActivityType.UPDATED,
        user=user,
        description=f'Contact ajouté : {contact.get_full_name()}',
        metadata={'contact_id': str(contact.id)},
        ip_address=ip_address
    )
    return contact


@transaction.atomic
def update_contact(*, contact_id, data: dict, user, ip_address=None):
    """
    Met à jour un contact existant
    
    Validation :
    - is_primary unique par client
    """
    
    try:
        contact = Contact.objects.select_related('client').get(id=contact_id)
    except Contact.DoesNotExist:
        raise ValidationError('Contact non trouvé')
    
    client = contact.client
    
    # Permissions
    if user.role_id == 'COMMERCIAL' and client.assigned_to != user:
        raise PermissionDenied('Vous ne pouvez modifier que vos propres contacts')

    # Validation
    data_with_id = {**data, 'id': contact_id}
    validate_contact_data(data_with_id, client=client)
    
    # Gestion contact principal
    if 'is_primary' in data and data['is_primary'] and not contact.is_primary:
        Contact.objects.filter(
            client=client,
            is_primary=True
        ).update(is_primary=False)
    
    # Update
    for field, value in data.items():
        setattr(contact, field, value)
    
    contact.save()
    # Log
    log_client_activity(
        client=client,
        activity_type=ClientActivity.ActivityType.UPDATED,
        user=user,
        description=f'Contact modifié : {contact.get_full_name()}',
        metadata={'contact_id': str(contact.id)},
        ip_address=ip_address
    )
    return contact


@transaction.atomic
def delete_contact(*, contact_id, user, ip_address=None):
    """
    Supprime un contact
    
    Explication :
    Hard delete (pas soft delete pour contacts)
    Contacts = données secondaires
    """
    
    try:
        contact = Contact.objects.select_related('client').get(id=contact_id)
    except Contact.DoesNotExist:
        raise ValidationError('Contact non trouvé')
    
    client = contact.client
    
    # Permissions
    if user.role_id == 'COMMERCIAL' and client.assigned_to != user:
        raise PermissionDenied('Vous ne pouvez supprimer que vos propres contacts')

    contact_name = contact.get_full_name()
    contact.delete()
    # Log
    log_client_activity(
        client=client,
        activity_type=ClientActivity.ActivityType.UPDATED,
        user=user,
        description=f'Contact supprimé : {contact_name}',
        ip_address=ip_address
    )

# ═══════════════════════════════════════════════════════════
# ACTIVITY LOGGING
# ═══════════════════════════════════════════════════════════

def log_client_activity(*, client, activity_type, user, description='', metadata=None, ip_address=None):

    # Log une activité client
    
    # Args:
    #    client: Client instance
    #    activity_type: Type d'activité (ActivityType enum)
    #    user: Utilisateur
    #    description: Description textuelle
    #    metadata: Données additionnelles (dict)
    #    ip_address: IP audit
    
    # Returns:
    #    ClientActivity instance
    
    # Explication :
    # Point central pour audit trail
    # Appelé par tous les services
    # Traçabilité complète

    
    return ClientActivity.objects.create(
        client=client,
        activity_type=activity_type,
        user=user,
        description=description,
        metadata=metadata or {},
        ip_address=ip_address
    )
