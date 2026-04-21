from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied
from decimal import Decimal

from ..models import (
    SupplierQuote,
    SupplierQuoteLine,
    InsomeaQuote,
    InsomeaQuoteLine,
    OpportunityLineStatus,
    OpportunityStatus,
)
from ..validators import (
    validate_pdf_file,
    validate_file_size,
    validate_can_create_insomea_quote,
    validate_insomea_quote_lines_pricing,
    validate_sale_price_greater_than_purchase,
)
from ..selectors import (
    get_opportunity_by_id,
    get_supplier_quote_by_id,
    get_insomea_quote_by_id,
)


def _get_related_or_none(instance, attr_name):
    try:
        return getattr(instance, attr_name)
    except ObjectDoesNotExist:
        return None


@transaction.atomic
def create_supplier_quote(*, supplier_id, document, lines_data: list, reference='', discount_percent=Decimal('0.00'), user, ip_address=None):
    """
    Crée devis fournisseur avec lignes
    
    Args:
        supplier_id: UUID Supplier
        document: UploadedFile PDF
        lines_data: list[dict] données lignes
            [
                {
                    'line_id': UUID OpportunityLine,
                    'unit_price_purchase': Decimal,
                    'sku': str (optionnel),
                    'currency': str (optionnel),
                    'delivery_time': int (optionnel)
                },
                ...
            ]
        reference: str référence devis fournisseur (optionnel)
        discount_percent: Decimal remise % (optionnel)
        user: User instance (COMMERCIAL)
        ip_address: str
    
    Returns:
        SupplierQuote créé
    
    Raises:
        ValidationError: Si fichier invalide ou lignes invalides
        PermissionDenied: Si pas COMMERCIAL
    
    Business Rules:
        - Upload PDF devis
        - Crée SupplierQuote
        - Crée SupplierQuoteLine pour chaque OpportunityLine
        - Transition FSM lines: SUPPLIER_QUOTE_REQUEST → SUPPLIER_QUOTE_RECEIVED
        - Calculate totals
    """
    
    if user.role not in ['ADMIN', 'COMMERCIAL']:
        raise PermissionDenied('Seuls les commerciaux peuvent créer des devis fournisseurs')
    
    validate_pdf_file(document)
    validate_file_size(document, max_size_mb=10)
    
    # ───────────────────────────────────────────────────────
    # 3. VALIDATION LIGNES
    # ───────────────────────────────────────────────────────
    
    if not lines_data:
        raise ValidationError('Au moins une ligne requise')
    
    # Vérifie que toutes les OpportunityLines existent
    from ..models import OpportunityLine
    line_ids = [ld['line_id'] for ld in lines_data]
    existing_lines = OpportunityLine.objects.filter(id__in=line_ids)
    
    if existing_lines.count() != len(line_ids):
        raise ValidationError('Certaines lignes sont introuvables')
    
    # Vérifie que toutes les lignes appartiennent à la même opportunity
    opportunities = set(existing_lines.values_list('opportunity_id', flat=True))
    if len(opportunities) > 1:
        raise ValidationError('Toutes les lignes doivent appartenir à la même opportunité')
    
    # Vérifie permissions sur opportunity
    opportunity = existing_lines.first().opportunity
    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Vous ne pouvez gérer que vos propres opportunités')
    
    # ───────────────────────────────────────────────────────
    # 4. CRÉATION SUPPLIER QUOTE
    # ───────────────────────────────────────────────────────
    
    from ...suppliers.models import Supplier
    supplier = Supplier.objects.get(id=supplier_id)
    
    supplier_quote = SupplierQuote.objects.create(
        supplier=supplier,
        created_by=user,
        reference=reference,
        document=document,
        discount_percent=discount_percent,
    )
    
    # ───────────────────────────────────────────────────────
    # 5. CRÉATION SUPPLIER QUOTE LINES + TRANSITION FSM
    # ───────────────────────────────────────────────────────
    
    for line_data in lines_data:
        line_id = line_data['line_id']
        unit_price = line_data['unit_price_purchase']
        
        # Récupère OpportunityLine
        opp_line = existing_lines.get(id=line_id)
        
        # Crée SupplierQuoteLine
        SupplierQuoteLine.objects.create(
            supplier_quote=supplier_quote,
            opportunity_line=opp_line,
            unit_price_purchase=unit_price,
            sku=line_data.get('sku', ''),
            currency=line_data.get('currency', 'EUR'),
            delivery_time=line_data.get('delivery_time'),
        )
        # NOTE: calculate totals appelé dans save() de SupplierQuoteLine
        
        # FSM transition
        if opp_line.status == OpportunityLineStatus.SUPPLIER_QUOTE_REQUEST:
            opp_line.supplier_quote_received()
            opp_line.save()
            # Signal FSM → StatusHistory créé auto
    
    # ───────────────────────────────────────────────────────
    # 6. RECALCULE TOTAUX (au cas où)
    # ───────────────────────────────────────────────────────
    
    recalculate_supplier_quote_totals(supplier_quote.id)
    
    return supplier_quote


@transaction.atomic
def recalculate_supplier_quote_totals(supplier_quote_id):
    """
    Recalcule totaux SupplierQuote
    
    Args:
        supplier_quote_id: UUID
    
    Returns:
        SupplierQuote mis à jour
    
    Business Logic:
        - Agrège SupplierQuoteLines
        - Applique discount
        - Update totals
    """
    
    supplier_quote = get_supplier_quote_by_id(supplier_quote_id)
    
    # Appelle méthode model
    supplier_quote.calculate_totals()
    
    return supplier_quote


# ═══════════════════════════════════════════════════════════
# INSOMEA QUOTE SERVICE
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def create_insomea_quote(*, opportunity_id, lines_pricing: list, discount_percent=Decimal('0.00'), notes='', user, ip_address=None):
    """
    Crée devis Insomea pour le client
    
    Args:
        opportunity_id: UUID Opportunity
        lines_pricing: list[dict] pricing par ligne
            [
                {
                    'line_id': UUID OpportunityLine,
                    'unit_price_sale': Decimal
                },
                ...
            ]
        discount_percent: Decimal remise globale % (optionnel)
        notes: str notes (optionnel)
        user: User instance (COMMERCIAL)
        ip_address: str
    
    Returns:
        InsomeaQuote créé
    
    Raises:
        ValidationError: Si préconditions non remplies ou pricing invalide
        PermissionDenied: Si pas COMMERCIAL
    
    Business Rules:
        - Vérifie TOUTES lignes ont SupplierQuoteLine
        - Crée InsomeaQuote
        - Crée InsomeaQuoteLines:
          * Copie unit_price_purchase depuis SupplierQuoteLine choisie
          * Utilise unit_price_sale fourni
          * Valide sale >= purchase
        - Calculate totals (purchase + sale + margin)
        - Transition FSM opportunity: create_insomea_quote()
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION + PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=True)
    
    if user.role not in ['ADMIN', 'COMMERCIAL']:
        raise PermissionDenied('Seuls les commerciaux peuvent créer des devis Insomea')
    
    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Action non autorisée')
    
    # ───────────────────────────────────────────────────────
    # 2. VALIDATION PRÉCONDITIONS
    # ───────────────────────────────────────────────────────
    
    validate_can_create_insomea_quote(opportunity)
    
    # ───────────────────────────────────────────────────────
    # 3. VALIDATION PRICING
    # ───────────────────────────────────────────────────────
    
    if not lines_pricing:
        raise ValidationError('Au moins une ligne requise')

    line_ids = [lp['line_id'] for lp in lines_pricing]
    opportunity_lines = opportunity.lines.filter(id__in=line_ids).select_related('supplier_quote_line')

    if opportunity_lines.count() != len(line_ids):
        raise ValidationError('Certaines lignes ne font pas partie de cette opportunité')

    line_map = {str(line.id): line for line in opportunity_lines}

    for lp in lines_pricing:
        opp_line = line_map.get(str(lp['line_id']))
        if not opp_line:
            raise ValidationError(f"Ligne {lp['line_id']} introuvable dans cette opportunité")

        supplier_quote_line = _get_related_or_none(opp_line, 'supplier_quote_line')

        if supplier_quote_line is None:
            raise ValidationError(
                f'Aucun devis fournisseur pour la ligne {opp_line.id}'
            )
        lp['supplier_quote_line'] = supplier_quote_line
        lp['unit_price_purchase'] = supplier_quote_line.unit_price_purchase

        validate_sale_price_greater_than_purchase(
            lp['unit_price_purchase'],
            lp['unit_price_sale']
        )
    
    # Validation composite
    validate_insomea_quote_lines_pricing(lines_pricing)
    
    # ───────────────────────────────────────────────────────
    # 4. CRÉATION INSOMEA QUOTE
    # ───────────────────────────────────────────────────────
    
    insomea_quote = InsomeaQuote.objects.create(
        opportunity=opportunity,
        created_by=user,
        discount_percent=discount_percent,
    )
    # NOTE: reference auto-généré dans save() du model
    
    # ───────────────────────────────────────────────────────
    # 5. CRÉATION INSOMEA QUOTE LINES
    # ───────────────────────────────────────────────────────
    
    for lp in lines_pricing:
        opp_line = line_map[str(lp['line_id'])]

        InsomeaQuoteLine.objects.create(
            insomea_quote=insomea_quote,
            opportunity_line=opp_line,
            supplier_quote_line=lp['supplier_quote_line'],
            unit_price_purchase=lp['unit_price_purchase'],
            unit_price_sale=lp['unit_price_sale'],
            line_margin=lp['unit_price_sale'] - lp['unit_price_purchase'],
        )
        # NOTE: calculate totals appelé dans save() de InsomeaQuoteLine
    
    # ───────────────────────────────────────────────────────
    # 6. RECALCULE TOTAUX
    # ───────────────────────────────────────────────────────
    
    recalculate_insomea_quote_totals(insomea_quote.id)
    
    # ───────────────────────────────────────────────────────
    # 7. TRANSITION FSM OPPORTUNITY
    # ───────────────────────────────────────────────────────

    opportunity.refresh_from_db()
    if opportunity.has_insomea_quote():
        opportunity.create_insomea_quote()
        opportunity.save()
        # Signal FSM → StatusHistory créé auto
    
    # ───────────────────────────────────────────────────────
    # 8. GÉNÉRATION PDF (best-effort)
    # ───────────────────────────────────────────────────────

    try:
        pdf_file = generate_quote_pdf(insomea_quote)
        insomea_quote.document.save(pdf_file.name, pdf_file, save=True)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"PDF generation skipped for InsomeaQuote {insomea_quote.id}: {e}"
        )

    return insomea_quote

from django.template.loader import render_to_string
from django.core.files.base import ContentFile


def generate_po_pdf(insomea_po):
    """
    Generate PDF for an InsomeaPurchaseOrder and return a Django ContentFile.
    Uses WeasyPrint.
    """
    import io
    from weasyprint import HTML
    from django.template.loader import render_to_string

    lines = insomea_po.supplier_quote.lines.select_related(
        'opportunity_line',
        'opportunity_line__product',
        'opportunity_line__opportunity',
        'opportunity_line__opportunity__client',
    )

    first_line = lines.first()
    opportunity = first_line.opportunity_line.opportunity if first_line else None

    context = {
        'po': insomea_po,
        'supplier': insomea_po.supplier,
        'supplier_quote': insomea_po.supplier_quote,
        'opportunity': opportunity,
        'lines': lines,
    }

    html_string = render_to_string('pdf/insomea_purchase_order.html', context)
    buf = io.BytesIO()
    HTML(string=html_string).write_pdf(buf)

    filename = f"po_{insomea_po.po_number}.pdf"
    return ContentFile(buf.getvalue(), name=filename)


def generate_quote_pdf(insomea_quote):
    """
    Generate PDF for an InsomeaQuote and return a Django ContentFile.
    Uses WeasyPrint (works natively on Linux/Docker).
    """
    import io
    from weasyprint import HTML

    # 1. Load related data
    lines = insomea_quote.lines.select_related(
        'opportunity_line',
        'opportunity_line__product',
        'supplier_quote_line'
    )

    # 2. Prepare context
    context = {
        'quote': insomea_quote,
        'lines': lines,
        'opportunity': insomea_quote.opportunity,
        'client': insomea_quote.opportunity.client,
    }

    # 3. Render HTML from template
    html_string = render_to_string('pdf/insomea_quote.html', context)

    # 4. Generate PDF
    buf = io.BytesIO()
    HTML(string=html_string).write_pdf(buf)

    # 5. Return Django ContentFile
    filename = f"quote_{insomea_quote.reference}.pdf"
    return ContentFile(buf.getvalue(), name=filename)


@transaction.atomic
def recalculate_insomea_quote_totals(insomea_quote_id):
    """
    Recalcule totaux InsomeaQuote

    Args:
        insomea_quote_id: UUID

    Returns:
        InsomeaQuote mis à jour

    Business Logic:
        - Agrège InsomeaQuoteLines (purchase + sale)
        - Applique discount
        - Calcule margin
        - Update totals
    """

    insomea_quote = get_insomea_quote_by_id(insomea_quote_id)

    # Appelle méthode model
    insomea_quote.calculate_totals()

    return insomea_quote


@transaction.atomic
def rollback_insomea_quote(*, opportunity_id, user, ip_address=None):
    """
    Revert INSOMEA_QUOTE_CREATED → SUPPLIER_QUOTE_RECIEVED.

    Deletes the existing InsomeaQuote (and its lines via CASCADE) so the
    commercial can re-enter sale prices and generate a new one.

    Args:
        opportunity_id: UUID
        user: User instance (COMMERCIAL or ADMIN)
        ip_address: str

    Returns:
        Opportunity mise à jour

    Raises:
        ValidationError: If status is not INSOMEA_QUOTE_CREATED
        PermissionDenied: If not owner (COMMERCIAL) or ADMIN
    """

    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=False)

    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Action non autorisée')

    if opportunity.status not in (OpportunityStatus.INSOMEA_QUOTE_CREATED, OpportunityStatus.CLIENT_PO_REQUEST):
        raise ValidationError(
            f"L'opportunité doit être en INSOMEA_QUOTE_CREATED ou CLIENT_PO_REQUEST pour modifier le devis. "
            f"Statut actuel : {opportunity.get_status_display()}"
        )

    # Delete ClientPO if rolling back from CLIENT_PO_REQUEST
    existing_po = _get_related_or_none(opportunity, 'client_purchase_order')
    if existing_po:
        existing_po.delete()

    # Delete existing InsomeaQuote (InsomeaQuoteLines cascade)
    existing = _get_related_or_none(opportunity, 'insomea_quote')
    if existing:
        existing.delete()

    # FSM rollback transition
    opportunity.revert_to_supplier_quote_received()
    opportunity.save()

    return opportunity
