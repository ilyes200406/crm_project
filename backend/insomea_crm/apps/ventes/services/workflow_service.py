from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied

from ..models import (
    Opportunity,
    OpportunityLine,
    OpportunityStatus,
    OpportunityLineStatus,
)
from ..validators import (
    validate_can_approve,
)
from ..selectors import (
    get_opportunity_by_id,
)
from .provision_service import create_provision_for_line
from ..emails.services import send_supplier_quote_request, send_client_quote_with_pdf


def _get_related_or_none(instance, attr_name):
    try:
        return getattr(instance, attr_name)
    except ObjectDoesNotExist:
        return None


# ═══════════════════════════════════════════════════════════
# BATCH TRANSITIONS (TOUTES LIGNES)
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def request_all_supplier_quotes(*, opportunity_id, user, ip_address=None):
    """
    Demande devis fournisseurs pour TOUTES les lignes
    
    Args:
        opportunity_id: UUID Opportunity
        user: User instance (COMMERCIAL)
        ip_address: str
    
    Returns:
        Opportunity mise à jour
    
    Raises:
        ValidationError: Si opportunité sans lignes
        PermissionDenied: Si pas COMMERCIAL
    
    Business Rules:
        - Pour TOUTES les OpportunityLines en DRAFT:
          → Transition FSM: request_supplier_quote()
          → DRAFT → SUPPLIER_QUOTE_REQUEST
        - Trigger update_opportunity_status_from_lines() via signal
        - Result: Opportunity.status = SUPPLIER_QUOTE_REQUEST (computed)
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION + PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=True)
    
    if user.role not in ['ADMIN', 'COMMERCIAL']:
        raise PermissionDenied('Seuls les commerciaux peuvent demander des devis fournisseurs')
    
    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Vous ne pouvez gérer que vos propres opportunités')
    
    # ───────────────────────────────────────────────────────
    # 2. VÉRIFICATION
    # ───────────────────────────────────────────────────────
    
    if not opportunity.lines.exists():
        raise ValidationError('L\'opportunité doit contenir au moins une ligne')
    
    # ───────────────────────────────────────────────────────
    # 3. TRANSITION FSM TOUTES LIGNES EN DRAFT
    # ───────────────────────────────────────────────────────
    
    for line in opportunity.lines.all():
        if line.status == OpportunityLineStatus.DRAFT:
            # FSM transition
            line.request_supplier_quote()
            line.save()
            # Signal FSM → StatusHistory créé auto
            # Signal post_save → update_opportunity_status_from_lines()
    
    # ───────────────────────────────────────────────────────
    # 4. TRIGGER UPDATE OPPORTUNITY STATUS
    # ───────────────────────────────────────────────────────
    
    # NOTE: update_opportunity_status_from_lines() appelé auto via signal
    # Mais on peut forcer si besoin:
    update_opportunity_status_from_lines(opportunity)

    
    # Groupe lignes par fournisseur (via product.supplier si existe)
    from collections import defaultdict
    lines_by_supplier = defaultdict(list)
    
    for line in opportunity.lines.all():
        # Get supplier depuis product (si FK existe)
        # Sinon, skip email (supplier sera choisi lors création SupplierQuote)
        supplier = getattr(line.product, 'supplier', None)
        if supplier:
            lines_by_supplier[supplier].append(line)
    
    # Envoi email par fournisseur
    for supplier, lines in lines_by_supplier.items():
        try:
            send_supplier_quote_request(
                opportunity=opportunity,
                supplier=supplier,
                lines=lines
            )
        except Exception as e:
            # Log error mais continue (email pas critique)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending email to supplier {supplier.name}: {e}")
    
    # Recharge opportunity (status recalculé via signal)
    opportunity.refresh_from_db()
    
    return opportunity


@transaction.atomic
def request_client_po(*, opportunity_id, user, ip_address=None):
    """
    Demande BC client (marque devis Insomea comme envoyé)
    
    Args:
        opportunity_id: UUID Opportunity
        user: User instance (COMMERCIAL)
        ip_address: str
    
    Returns:
        Opportunity mise à jour
    
    Raises:
        ValidationError: Si préconditions non remplies
        PermissionDenied: Si pas COMMERCIAL
    
    Business Rules:
        - Transition FSM: INSOMEA_QUOTE_CREATED → CLIENT_PO_REQUEST
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION + PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=False)
    
    if user.role not in ['ADMIN', 'COMMERCIAL']:
        raise PermissionDenied('Seuls les commerciaux peuvent demander un BC client')
    
    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Action non autorisée')
    
    # ───────────────────────────────────────────────────────
    # 2. TRANSITION FSM
    # ───────────────────────────────────────────────────────
    
    opportunity.request_client_po()
    opportunity.save()
    # Signal FSM → StatusHistory créé auto

    # Get InsomeaQuote
    insomea_quote = _get_related_or_none(opportunity, 'insomea_quote')
    if insomea_quote:
        try:
            send_client_quote_with_pdf(
                opportunity=opportunity,
                insomea_quote=insomea_quote
            )
        except Exception as e:
            # Log error mais continue
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending email to client: {e}")
    
    return opportunity


# ═══════════════════════════════════════════════════════════
# APPROVE OPPORTUNITY (FINANCE)
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def approve_opportunity(*, opportunity_id, user, ip_address=None):
    """
    Approuve opportunité (FINANCE)
    
    Args:
        opportunity_id: UUID Opportunity
        user: User instance (FINANCE ou ADMIN)
        ip_address: str
    
    Returns:
        dict {
            'opportunity': Opportunity,
            'provisions': [Provision, ...],
            'insomea_pos': [InsomeaPurchaseOrder, ...],
        }
    
    Raises:
        ValidationError: Si préconditions non remplies
        PermissionDenied: Si pas FINANCE
    
    Business Rules:
        - Transition FSM: CLIENT_PO_RECEIVED → APPROVED
        - Crée Provisions pour TOUTES les OpportunityLines
        - Crée InsomeaPurchaseOrders (1 par fournisseur)
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION + PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=True)
    
    if user.role not in ['ADMIN', 'FINANCE']:
        raise PermissionDenied('Seul Finance peut approuver des opportunités')
    
    # ───────────────────────────────────────────────────────
    # 2. VALIDATION PRÉCONDITIONS
    # ───────────────────────────────────────────────────────
    
    validate_can_approve(opportunity)
    
    # ───────────────────────────────────────────────────────
    # 3. TRANSITION FSM OPPORTUNITY
    # ───────────────────────────────────────────────────────
    
    opportunity.approuve()
    opportunity.save()
    # Signal FSM → StatusHistory créé auto
    
    # ───────────────────────────────────────────────────────
    # 4. CRÉATION PROVISIONS (1 par OpportunityLine)
    # ───────────────────────────────────────────────────────
    
    provisions = []
    
    for line in opportunity.lines.all():
        # Vérifie que provision n'existe pas déjà
        if _get_related_or_none(line, 'provision') is None:
            provision = create_provision_for_line(
                opportunity_line_id=line.id,
                user=user
            )
            provisions.append(provision)
    
    # ───────────────────────────────────────────────────────
    # 5. CRÉATION INSOMEA POs (1 par fournisseur)
    # ───────────────────────────────────────────────────────
    
    from .purchase_order_service import create_insomea_pos
    
    insomea_pos = create_insomea_pos(
        opportunity_id=opportunity.id,
        user=user,
        ip_address=ip_address
    )
    
    # ───────────────────────────────────────────────────────
    # 6. RETOUR
    # ───────────────────────────────────────────────────────
    
    return {
        'opportunity': opportunity,
        'provisions': provisions,
        'insomea_pos': insomea_pos,
    }


# ═══════════════════════════════════════════════════════════
# UPDATE OPPORTUNITY STATUS FROM LINES (COMPUTED)
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def update_opportunity_status_from_lines(opportunity: Opportunity):
    """
    Recalcule Opportunity.status basé sur statuts des lignes
    
    Args:
        opportunity: Opportunity instance
    
    Returns:
        None (modifie opportunity en place)
    
    Business Logic:
        - Si 0 lignes → DRAFT
        - Si TOUTES lignes = même statut → ce statut
        - Si lignes mixtes → garde statut actuel Opportunity
          (car Opportunity a son propre workflow après phase devis)
    
    Appelé automatiquement par:
        - Signal post_save OpportunityLine
        - Signal post_delete OpportunityLine
    
    Note:
        OpportunityLine suit phase devis fournisseur seulement:
          DRAFT → SUPPLIER_QUOTE_REQUEST → SUPPLIER_QUOTE_RECEIVED
        
        Opportunity continue ensuite indépendamment:
          → INSOMEA_QUOTE_CREATED → CLIENT_PO_REQUEST → CLIENT_PO_RECEIVED → APPROVED
    """
    
    
    # ───────────────────────────────────────────────────────
    # CAS 7 : APRÈS PHASE DEVIS (Opportunity indépendant)
    # ───────────────────────────────────────────────────────
    
    # Si Opportunity déjà au-delà de la phase devis fournisseur
    # (INSOMEA_QUOTE_CREATED, CLIENT_PO_REQUEST, etc.)
    # → Ne pas toucher au statut, Opportunity a son propre workflow FSM
    
    if opportunity.status in [
        OpportunityStatus.INSOMEA_QUOTE_CREATED,
        OpportunityStatus.CLIENT_PO_REQUEST,
        OpportunityStatus.CLIENT_PO_RECIEVED,
        OpportunityStatus.APPROUVED,
    ]:
        # Ne touche pas au statut, Opportunity gère son workflow indépendamment
        return
    
    # ───────────────────────────────────────────────────────
    # CAS 1 : RÉCUPÈRE STATUTS UNIQUES
    # ───────────────────────────────────────────────────────

    statuses = set(opportunity.lines.values_list('status', flat=True))    
    
    # ───────────────────────────────────────────────────────
    # CAS 2 : PAS DE LIGNES
    # ───────────────────────────────────────────────────────
    
    if not statuses:
        if opportunity.status != OpportunityStatus.DRAFT:
            opportunity.status = OpportunityStatus.DRAFT
            opportunity.save(update_fields=['status'])
        return
    

    
    
    # ───────────────────────────────────────────────────────
    # CAS 3 : TOUTES LIGNES ANNULÉES
    # ───────────────────────────────────────────────────────
    
    if statuses == {OpportunityLineStatus.CANCELLED}:
        if opportunity.status != OpportunityStatus.CANCELLED:
            opportunity.cancel("Toutes les lignes annulées")
            opportunity.save(update_fields=['status', 'cancellation_reason'])
        return
    
    # ───────────────────────────────────────────────────────
    # CAS 4 : TOUTES LIGNES EN SUPPLIER_QUOTE_REQUEST
    # ───────────────────────────────────────────────────────
    
    if statuses == {OpportunityLineStatus.SUPPLIER_QUOTE_REQUEST}:
        if opportunity.status == OpportunityStatus.DRAFT:
            # Transition FSM
            opportunity.all_supplier_quotes_requested()
            opportunity.save(update_fields=['status'])
        return
    
    # ───────────────────────────────────────────────────────
    # CAS 5 : TOUTES LIGNES EN SUPPLIER_QUOTE_RECEIVED
    # ───────────────────────────────────────────────────────
    
    if statuses == {OpportunityLineStatus.SUPPLIER_QUOTE_RECIEVED}:
        if opportunity.status == OpportunityStatus.SUPPLIER_QUOTE_REQUEST:
            # Transition FSM
            opportunity.all_supplier_quotes_received()
            opportunity.save(update_fields=['status'])
        return
    
    # ───────────────────────────────────────────────────────
    # CAS 6 : LIGNES MIXTES (certaines DRAFT, d'autres en REQUEST, etc.)
    # ───────────────────────────────────────────────────────
    
    # Si lignes mixtes pendant phase devis → garde statut le MOINS avancé
    # Ordre: DRAFT < SUPPLIER_QUOTE_REQUEST < SUPPLIER_QUOTE_RECEIVED
    
    if OpportunityLineStatus.DRAFT in statuses:
        # Au moins une ligne encore en DRAFT → Opportunity reste DRAFT
        if opportunity.status != OpportunityStatus.DRAFT:
            opportunity.status = OpportunityStatus.DRAFT
            opportunity.save(update_fields=['status'])
        return
    
    if OpportunityLineStatus.SUPPLIER_QUOTE_REQUEST in statuses:
        # Au moins une ligne en REQUEST → Opportunity reste REQUEST
        if opportunity.status not in [
            OpportunityStatus.DRAFT,
            OpportunityStatus.SUPPLIER_QUOTE_REQUEST
        ]:
            # Ne revient pas en arrière si déjà plus avancé
            return
        
        if opportunity.status == OpportunityStatus.DRAFT:
            opportunity.all_supplier_quotes_requested()
            opportunity.save(update_fields=['status'])
        return
    

    
# ═══════════════════════════════════════════════════════════
# SIGNAL HANDLER (appelé dans signals.py)
# ═══════════════════════════════════════════════════════════

def handle_opportunity_line_save(opportunity_line):
    """
    Handler appelé par signal post_save OpportunityLine
    
    Args:
        opportunity_line: OpportunityLine instance sauvegardée
    
    Returns:
        None
    
    Note:
        Cette fonction doit être appelée dans signals.py
    """
    
    opportunity = opportunity_line.opportunity
    update_opportunity_status_from_lines(opportunity)
