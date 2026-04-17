from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied
from django.utils import timezone
from ..models import (Opportunity, OpportunityLine, OpportunityStatus, OpportunityLineStatus, InsomeaPurchaseOrder)
from ..selectors import (get_opportunity_by_id, get_line_by_id)
from ..validators import (validate_opportunity_data, validate_can_approve, normalize_opportunity_name, validate_can_request_client_po)

@transaction.atomic
def create_opportunity(*, data: dict, user, ip_address=None):
    payload = data.copy()

    name = normalize_opportunity_name(payload.get('name'))
    if not name:
        raise ValidationError("Le nom de l'opportunité est requis")

    payload['name'] = name

    validate_opportunity_data(payload)

    payload['status'] = OpportunityStatus.DRAFT
    payload['created_by'] = user

    if user.role == 'COMMERCIAL' and not payload.get('assigned_to'):
        payload['assigned_to'] = user

    opportunity = Opportunity.objects.create(**payload)

    return opportunity


@transaction.atomic
def update_opportunity(*, opportunity_id, data: dict, user, ip_address=None):
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=False)

    unrestricted_fields = {'notes', 'assigned_to'}
    restricted_fields = set(data.keys()) - unrestricted_fields
    
    if restricted_fields and not opportunity.can_edit():
        raise ValidationError(
            f'L\'opportunité {opportunity.reference} ne peut plus être modifiée. '
            f'Statut actuel : {opportunity.get_status_display()}'
        )

    validate_opportunity_data(data, opportunity=opportunity)
    
    for field, value in data.items():
        setattr(opportunity, field, value)
    
    opportunity.save()
    
    return opportunity


@transaction.atomic
def delete_opportunity(*, opportunity_id, user, ip_address=None):
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=True)

    if opportunity.status == OpportunityStatus.CANCELLED:
        raise ValidationError('L\'opportunité est déjà annulée')
    
    for line in opportunity.lines.all():
        if line.status != OpportunityLineStatus.CANCELLED:
            line.cancel(reason='Opportunité supprimée')
            line.save()

    opportunity.cancel(reason='Suppression via interface')
    opportunity.cancellation_reason = 'Suppression par utilisateur'
    opportunity.save()


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
    
    from ..tasks import send_supplier_quote_request_email
    for supplier, lines in lines_by_supplier.items():
        send_supplier_quote_request_email.delay(
            opportunity_id=str(opportunity.id),
            supplier_id=str(supplier.id),
            line_ids=[str(line.id) for line in lines],
        )

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

    # ───────────────────────────────────────────────────────
    # 2. TRANSITION FSM
    # ───────────────────────────────────────────────────────

    opportunity.request_client_po()
    opportunity.save()
    # Signal FSM → StatusHistory créé auto

    insomea_quote = _get_related_or_none(opportunity, 'insomea_quote')
    if insomea_quote:
        from ..tasks import send_client_quote_pdf_email
        send_client_quote_pdf_email.delay(
            opportunity_id=str(opportunity.id),
            insomea_quote_id=str(insomea_quote.id),
        )
    
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

    # ───────────────────────────────────────────────────────
    # 2. VALIDATION PRÉCONDITIONS
    # ───────────────────────────────────────────────────────

    validate_can_approve(opportunity)

    # ───────────────────────────────────────────────────────
    # 3. TRANSITION FSM OPPORTUNITY
    # ───────────────────────────────────────────────────────

    opportunity.approved_by = user   # Layer 2: record which Finance user approved
    opportunity.approuve()
    opportunity.save()
    # Signal FSM → StatusHistory créé auto
    
    # ───────────────────────────────────────────────────────
    # 4. CRÉATION PROVISIONS (1 par OpportunityLine)
    # ───────────────────────────────────────────────────────
    """
    provisions = []
    
    for line in opportunity.lines.all():
        # Vérifie que provision n'existe pas déjà
        if _get_related_or_none(line, 'provision') is None:
            provision = create_provision_for_line(
                opportunity_line_id=line.id,
                user=user
            )
            provisions.append(provision)
    """
    # ───────────────────────────────────────────────────────
    # 5. CRÉATION INSOMEA POs (1 par fournisseur)
    # ───────────────────────────────────────────────────────
    
    
    result = send_insomea_pos(
        opportunity_id=opportunity.id,
        user=user,
        ip_address=ip_address
    )

    return result

def generate_insomea_po_reference(supplier):
    """
    Générer référence Insomea PO
    
    Format: IPO-YYYYMMDD-SUPPLIER-XXX
    """
    from django.db.models import Count
    
    today = timezone.now().date()
    count = InsomeaPurchaseOrder.objects.filter(
        supplier=supplier,
        created_at__date=today
    ).count()
    
    supplier_code = supplier.name[:3].upper()
    
    return f"IPO-{today.strftime('%Y%m%d')}-{supplier_code}-{count + 1:03d}"


@transaction.atomic
def send_insomea_pos(*, opportunity_id, user, ip_address=None):
    """
    Send Insomea Purchase Orders to suppliers
    
    ✅ REFACTORÉ: Crée 1 PO par SupplierQuote (pas par ligne)
    
    Triggered by: approve_opportunity() (Finance)
    
    Flow:
        1. Get all SupplierQuotes from opportunity lines
        2. Pour chaque SupplierQuote:
           - Create 1 InsomeaPurchaseOrder
           - Link all OpportunityLines to this PO
           - Transition all lines: SUPPLIER_QUOTE_RECEIVED → INSOMEA_PO_SENT
        3. Send 1 email per supplier (with all lines)
        4. Opportunity auto-transition: APPROVED → INSOMEA_PO_SENT
    
    Returns:
        dict {
            'opportunity': Opportunity,
            'pos_created': [InsomeaPurchaseOrder, ...],
            'emails_sent': int
        }
    """
    
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=True)
    
    # Check status
    if opportunity.status != OpportunityStatus.APPROUVED:
        raise ValidationError(
            f"Opportunity must be APPROVED. Current: {opportunity.get_status_display()}"
        )
    
    # Check lines
    if not opportunity.lines.exists():
        raise ValidationError("Opportunity has no lines")
    
    # ✅ NOUVEAU: Group lines by SupplierQuote
    supplier_quotes_map = {}  # {supplier_quote_id: [lines]}
    
    for line in opportunity.lines.all():
        
        # Check status
        if line.status != OpportunityLineStatus.SUPPLIER_QUOTE_RECIEVED:
            raise ValidationError(
                f"Line {line.id} must be SUPPLIER_QUOTE_RECIEVED. Current: {line.get_status_display()}"
            )
        
        # Get SupplierQuoteLine
        if not hasattr(line, 'supplier_quote_line') or not line.supplier_quote_line:
            raise ValidationError(f"Line {line.id} has no supplier quote")
        
        supplier_quote = line.supplier_quote_line.supplier_quote
        
        if supplier_quote.id not in supplier_quotes_map:
            supplier_quotes_map[supplier_quote.id] = {
                'supplier_quote': supplier_quote,
                'lines': []
            }
        
        supplier_quotes_map[supplier_quote.id]['lines'].append(line)
    
    # ✅ Create 1 PO per SupplierQuote
    pos_created = []
    emails_queued = 0

    from ..tasks import send_insomea_po_email
    import logging
    logger = logging.getLogger(__name__)
    for sq_data in supplier_quotes_map.values():
        
        supplier_quote = sq_data['supplier_quote']
        lines = sq_data['lines']
        supplier = supplier_quote.supplier
        
        # Check if PO already exists (related_name='insomea_pos')
        existing_po = supplier_quote.insomea_pos.first()
        if existing_po:
            logger.warning(f"⚠️  PO already exists for SupplierQuote {supplier_quote.id}")
            po = existing_po
        else:
            # Generate reference
            po_number = generate_insomea_po_reference(supplier)

            # ✅ Create InsomeaPurchaseOrder (1 per SupplierQuote)
            po = InsomeaPurchaseOrder.objects.create(
                supplier=supplier,
                supplier_quote=supplier_quote,  # ✅ Link to quote (not line)
                po_number=po_number,
                sent_at=timezone.now(),
                created_by=user,
            )
        
        # Link all lines to this PO + transition
        for line in lines:
            line.insomea_purchase_order = po
            line.send_insomea_po()
            line.save()
        
        pos_created.append(po)
        send_insomea_po_email.delay(
            supplier_id=str(supplier.id),
            po_id=str(po.id),
            opportunity_id=str(opportunity.id),
        )
        emails_queued += 1
    
    # Refresh opportunity
    opportunity.refresh_from_db()
    
    # Check if all lines transitioned → auto-transition opportunity
    all_lines_sent = all(
        line.status == OpportunityLineStatus.INSOMEA_PO_SENT
        for line in opportunity.lines.all()
    )
    
    if all_lines_sent:
        opportunity.all_insomea_pos_sent()
        opportunity.save()
    
    return {
        'opportunity': opportunity,
        'pos_created': pos_created,
        'emails_queued': emails_queued
    }


@transaction.atomic
def confirm_insomea_po(*, line_id, user, ip_address=None):
    """
    Confirm Insomea PO received by supplier
    
    ✅ MODIFIÉ: Confirmation par ligne, mais check si toutes lignes du PO confirmées
    
    Args:
        line_id: OpportunityLine UUID
        user: User instance
    
    Flow:
        1. Check line status = INSOMEA_PO_SENT
        2. Transition line: INSOMEA_PO_SENT → INSOMEA_PO_CONFIRMED
        3. Check if ALL lines of this PO confirmed
        4. If yes: Update PO.confirmed_at
        5. Check if all opportunity lines confirmed → create provisions
    """
    
    line = get_line_by_id(line_id)
    
    # Check permissions
    #check_can_update_opportunity(user, line.opportunity)
    
    # Check status
    if line.status != OpportunityLineStatus.INSOMEA_PO_SENT:
        raise ValidationError(
            f"Line must be INSOMEA_PO_SENT. Current: {line.get_status_display()}"
        )
    
    # Get PO
    if not line.insomea_purchase_order:
        raise ValidationError("Line has no Insomea PO")
    
    po = line.insomea_purchase_order
    
    # FSM transition line
    line.confirm_insomea_po()
    line.save()
    
    # ✅ Check if ALL lines of this PO confirmed
    all_po_lines = OpportunityLine.objects.filter(
        insomea_purchase_order=po
    )
    
    all_po_lines_confirmed = all(
        l.status == OpportunityLineStatus.INSOMEA_PO_CONFIRMED
        for l in all_po_lines
    )
    
    # Update PO if all lines confirmed
    if all_po_lines_confirmed and not po.confirmed_at:
        po.confirmed_at = timezone.now()
        po.save()
    
    # Check if ALL opportunity lines confirmed
    opportunity = line.opportunity
    all_opp_lines_confirmed = all(
        l.status == OpportunityLineStatus.INSOMEA_PO_CONFIRMED
        for l in opportunity.lines.all()
    )
    
    provisions_created = False
    
    if all_opp_lines_confirmed:
        # Auto-transition opportunity
        opportunity.all_insomea_pos_confirmed()
        opportunity.save()
        
        # Create provisions
        from .provision_service import create_provisions
        
        create_provisions(
            opportunity_id=opportunity.id,
            user=user,
            ip_address=ip_address
        )
        
        provisions_created = True
    
    return {
        'line': line,
        'po': po,
        'po_fully_confirmed': all_po_lines_confirmed,
        'all_confirmed': all_opp_lines_confirmed,
        'provisions_created': provisions_created
    }


@transaction.atomic
def confirm_all_insomea_pos(*, opportunity_id, user, ip_address=None):
    """
    Confirm all Insomea POs for opportunity
    
    ✅ MODIFIÉ: Confirme toutes lignes
    """
    
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=True)
    
    # Check permissions
    # check_can_update_opportunity(user, opportunity)
    
    # Check status
    if opportunity.status != OpportunityStatus.INSOMEA_POS_SENT:
        raise ValidationError(
            f"Opportunity must be INSOMEA_POS_SENT. Current: {opportunity.get_status_display()}"
        )
    
    lines_confirmed = 0
    
    for line in opportunity.lines.all():
        if line.status == OpportunityLineStatus.INSOMEA_PO_SENT:
            confirm_insomea_po(
                line_id=line.id,
                user=user,
                ip_address=ip_address
            )
            lines_confirmed += 1
    
    # Refresh
    opportunity.refresh_from_db()
    
    provisions_created = (
        opportunity.status == OpportunityStatus.INSOMEA_POS_CONFIRMED
    )
    
    return {
        'lines_confirmed': lines_confirmed,
        'opportunity': opportunity,
        'provisions_created': provisions_created
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


