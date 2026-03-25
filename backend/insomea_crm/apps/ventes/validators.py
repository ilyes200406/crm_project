"""
VALIDATORS - APP OPPORTUNITIES

Validation business rules :
- Pricing (prix, marges, remises)
- Quantities
- FSM Guards (preconditions)
- Files (PDFs)
- Composite validations
"""

from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _


# ═══════════════════════════════════════════════════════════
# PRICING VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_price_positive(value):
    """
    Valide que prix > 0
    
    Args:
        value: Decimal price
    
    Raises:
        ValidationError: Si prix <= 0
    """
    if value is None:
        return
    
    if value <= Decimal('0.00'):
        raise ValidationError(
            _('Le prix doit être supérieur à zéro'),
            code='price_not_positive'
        )


def validate_sale_price_greater_than_purchase(purchase_price, sale_price):
    """
    Valide prix vente >= prix achat (pas de vente à perte)
    
    Args:
        purchase_price: Decimal
        sale_price: Decimal
    
    Raises:
        ValidationError: Si sale < purchase
    """
    if purchase_price is None or sale_price is None:
        return
    
    if sale_price < purchase_price:
        raise ValidationError(
            _(
                f'Prix de vente ({sale_price}€) doit être supérieur ou égal '
                f'au prix d\'achat ({purchase_price}€)'
            ),
            code='sale_price_too_low'
        )


def validate_margin_acceptable(purchase_price, sale_price, min_margin_percent=Decimal('5.00')):
    """
    Valide marge minimale acceptable
    
    Args:
        purchase_price: Decimal
        sale_price: Decimal
        min_margin_percent: Decimal (default 5%)
    
    Raises:
        ValidationError: Si marge < minimum
    """
    if purchase_price is None or sale_price is None:
        return
    
    if purchase_price <= 0:
        return
    
    margin = sale_price - purchase_price
    margin_percent = (margin / purchase_price) * Decimal('100.00')
    
    if margin_percent < min_margin_percent:
        raise ValidationError(
            _(
                f'Marge insuffisante : {margin_percent:.2f}%. '
                f'Marge minimale requise : {min_margin_percent}%. '
                f'(Achat: {purchase_price}€, Vente: {sale_price}€)'
            ),
            code='insufficient_margin'
        )


def validate_discount_percent(value):
    """
    Valide remise % (0-100)
    
    Args:
        value: Decimal
    
    Raises:
        ValidationError: Si < 0 ou > 100
    """
    if value is None:
        return
    
    if value < Decimal('0.00'):
        raise ValidationError(
            _('La remise ne peut pas être négative'),
            code='negative_discount'
        )
    
    if value > Decimal('100.00'):
        raise ValidationError(
            _('La remise ne peut pas dépasser 100%'),
            code='discount_too_high'
        )


# ═══════════════════════════════════════════════════════════
# QUANTITY VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_quantity(value):
    """
    Valide quantité licences (1-10000)
    
    Args:
        value: int quantity
    
    Raises:
        ValidationError: Si hors limites
    """
    if value is None:
        return
    
    if value < 1:
        raise ValidationError(
            _('La quantité doit être au moins 1'),
            code='invalid_quantity'
        )
    
    if value > 10000:
        raise ValidationError(
            _('La quantité ne peut pas dépasser 10 000'),
            code='quantity_too_high'
        )


def validate_product_unique_in_opportunity(product, opportunity, exclude_line_id=None):
    """
    Valide qu'un produit n'existe pas déjà dans l'opportunité
    
    Args:
        product: Product instance
        opportunity: Opportunity instance
        exclude_line_id: UUID (pour update, exclure ligne courante)
    
    Raises:
        ValidationError: Si produit déjà présent
    """
    from .models import OpportunityLine
    
    query = OpportunityLine.objects.filter(
        opportunity=opportunity,
        product=product
    )
    
    if exclude_line_id:
        query = query.exclude(id=exclude_line_id)
    
    if query.exists():
        existing = query.first()
        raise ValidationError(
            _(
                f'Ce produit existe déjà dans l\'opportunité : {existing.product.title}. '
                f'Modifiez la quantité au lieu d\'ajouter une nouvelle ligne.'
            ),
            code='duplicate_product'
        )


# ═══════════════════════════════════════════════════════════
# FSM GUARDS (PRECONDITIONS)
# ═══════════════════════════════════════════════════════════

def validate_can_request_supplier_quote(line):
    """
    Précondition : Demander devis fournisseur
    
    Args:
        line: OpportunityLine instance
    
    Raises:
        ValidationError: Si préconditions non remplies
    """
    from .models import OpportunityLineStatus
    
    if line.status != OpportunityLineStatus.DRAFT:
        raise ValidationError(
            _('La ligne doit être en brouillon pour demander un devis fournisseur'),
            code='invalid_status'
        )
    
    if not line.product_id:
        raise ValidationError(
            _('Produit requis'),
            code='missing_product'
        )


def validate_can_receive_supplier_quote(line):
    """
    Précondition : Recevoir devis fournisseur
    
    Args:
        line: OpportunityLine instance
    
    Raises:
        ValidationError: Si préconditions non remplies
    """
    from .models import OpportunityLineStatus
    
    if line.status != OpportunityLineStatus.SUPPLIER_QUOTE_REQUEST:
        raise ValidationError(
            _('La ligne doit être en attente de devis fournisseur'),
            code='invalid_status'
        )
    
    # Vérifie SupplierQuoteLine existe
    if not line.has_supplier_quote():
        raise ValidationError(
            _('Devis fournisseur requis'),
            code='missing_supplier_quote'
        )


def validate_can_create_insomea_quote(opportunity):
    """
    Précondition : Créer devis Insomea
    
    Args:
        opportunity: Opportunity instance
    
    Raises:
        ValidationError: Si préconditions non remplies
    """
    from .models import OpportunityStatus
    
    if opportunity.status != OpportunityStatus.SUPPLIER_QUOTE_RECIEVED:
        raise ValidationError(
            _('Devis fournisseur requis avant création devis Insomea'),
            code='invalid_status'
        )
    
    # Vérifie que TOUTES les lignes ont SupplierQuoteLine
    for line in opportunity.lines.all():
        if not line.has_supplier_quote():
            raise ValidationError(
                _(f'Devis fournisseur manquant pour : {line.product.title}'),
                code='missing_supplier_quote'
            )


def validate_can_request_client_po(opportunity):
    """
    Précondition : Demander BC client
    
    Args:
        opportunity: Opportunity instance
    
    Raises:
        ValidationError: Si préconditions non remplies
    """
    from .models import OpportunityStatus
    
    if opportunity.status != OpportunityStatus.INSOMEA_QUOTE_CREATED:
        raise ValidationError(
            _('Devis Insomea requis avant demande BC client'),
            code='invalid_status'
        )
    
    # Vérifie InsomeaQuote existe
    try:
        if not opportunity.insomea_quote:
            raise ValidationError(
                _('Devis Insomea requis'),
                code='missing_insomea_quote'
            )
    except opportunity.__class__.insomea_quote.RelatedObjectDoesNotExist:
        raise ValidationError(
            _('Devis Insomea requis'),
            code='missing_insomea_quote'
        )


def validate_can_receive_client_po(opportunity):
    """
    Précondition : Recevoir BC client
    
    Args:
        opportunity: Opportunity instance
    
    Raises:
        ValidationError: Si préconditions non remplies
    """
    from .models import OpportunityStatus
    
    if opportunity.status != OpportunityStatus.CLIENT_PO_REQUEST:
        raise ValidationError(
            _('La demande BC client doit être envoyée'),
            code='invalid_status'
        )
    
    # Vérifie ClientPO uploadé
    if not opportunity.opportunity_has_client_po():
        raise ValidationError(
            _('Bon de commande client requis'),
            code='missing_client_po'
        )


def validate_can_upload_client_po(opportunity):
    from .models import OpportunityStatus
    
    if opportunity.status != OpportunityStatus.CLIENT_PO_REQUEST:
        raise ValidationError(
            _('La demande BC client doit être envoyée'),
            code='invalid_status'
        )


def validate_can_approve(opportunity):
    """
    Précondition : Approuver opportunité
    
    Args:
        opportunity: Opportunity instance
    
    Raises:
        ValidationError: Si préconditions non remplies
    """
    from .models import OpportunityStatus
    
    if opportunity.status != OpportunityStatus.CLIENT_PO_RECIEVED:
        raise ValidationError(
            _('BC client requis avant approbation'),
            code='invalid_status'
        )


def validate_can_start_provisioning(provision):
    """
    Précondition : Démarrer provisionnement
    
    Args:
        provision: Provision instance
    
    Raises:
        ValidationError: Si préconditions non remplies
    """
    from .models import ProvisionStatus
    
    if provision.status != ProvisionStatus.WAITING_PROVISION:
        raise ValidationError(
            _('La provision doit être en attente'),
            code='invalid_status'
        )


def validate_can_complete_provisioning(provision):
    """
    Précondition : Terminer provisionnement
    
    Args:
        provision: Provision instance
    
    Raises:
        ValidationError: Si préconditions non remplies
    """
    from .models import ProvisionStatus
    
    if provision.status != ProvisionStatus.PROVISIONING:
        raise ValidationError(
            _('Le provisionnement doit être en cours'),
            code='invalid_status'
        )
    
    # Vérifie Subscription créée
    if not provision.has_subscription():
        raise ValidationError(
            _('Subscription Microsoft requis'),
            code='missing_subscription'
        )
    
def validate_complete_provisioning_data(provision, subscription_data):
    """Valide données complete provisioning selon initial vs renewal"""
    if provision.is_initial():
        if not subscription_data.get('subscription_number'):
            raise ValidationError('subscription_number required for initial')
    else:
        if subscription_data.get('subscription_number'):
            raise ValidationError('subscription_number not allowed for renewal')


# ═══════════════════════════════════════════════════════════
# FILE VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_pdf_file(file):
    """
    Valide fichier PDF
    
    Vérifie :
    - Extension .pdf
    - Content-Type
    - Magic bytes (signature PDF)
    
    Args:
        file: UploadedFile
    
    Raises:
        ValidationError: Si pas un PDF valide
    """
    if not file:
        return
    
    # Vérifie extension
    ext_validator = FileExtensionValidator(allowed_extensions=['pdf'])
    ext_validator(file)
    
    # Vérifie Content-Type
    if file.content_type != 'application/pdf':
        raise ValidationError(
            _(f'Type de fichier invalide : {file.content_type}. PDF requis.'),
            code='invalid_file_type'
        )
    
    # Vérifie magic bytes (signature PDF)
    file.seek(0)
    header = file.read(5)
    file.seek(0)
    
    if header != b'%PDF-':
        raise ValidationError(
            _('Le fichier ne semble pas être un PDF valide'),
            code='invalid_pdf_signature'
        )


def validate_file_size(file, max_size_mb=10):
    """
    Valide taille fichier
    
    Args:
        file: UploadedFile
        max_size_mb: int (default 10MB)
    
    Raises:
        ValidationError: Si fichier trop volumineux
    """
    if not file:
        return
    
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file.size > max_size_bytes:
        raise ValidationError(
            _(
                f'Fichier trop volumineux : {file.size / (1024*1024):.2f} MB. '
                f'Taille maximale : {max_size_mb} MB'
            ),
            code='file_too_large'
        )


# ═══════════════════════════════════════════════════════════
# COMPOSITE VALIDATORS
# ═══════════════════════════════════════════════════════════

def validate_opportunity_data(data, opportunity=None):
    """
    Validation composite opportunité
    
    Valide ensemble des champs Opportunity
    
    Args:
        data: dict données à valider
        opportunity: Opportunity instance (pour update)
    
    Raises:
        ValidationError: Si validation échoue
    
    Returns:
        data: dict validé
    """
    errors = {}
    
    # Valide name
    if 'name' in data:
        name = data['name']
        if not name or len(name.strip()) < 3:
            errors['name'] = [_('Le nom doit contenir au moins 3 caractères')]
    
    # Valide discount
    if 'discount_percent' in data:
        try:
            validate_discount_percent(data['discount_percent'])
        except ValidationError as e:
            errors['discount_percent'] = e.messages
    
    if errors:
        raise ValidationError(errors)
    
    return data


def validate_opportunity_line_data(data, opportunity, line=None):
    """
    Validation composite ligne opportunité
    
    Args:
        data: dict données à valider
        opportunity: Opportunity instance
        line: OpportunityLine instance (pour update)
    
    Raises:
        ValidationError: Si validation échoue
    
    Returns:
        data: dict validé
    """
    errors = {}
    
    # Valide quantity
    if 'quantity' in data:
        try:
            validate_quantity(data['quantity'])
        except ValidationError as e:
            errors['quantity'] = e.messages
    
    # Valide produit unique
    if 'product' in data:
        try:
            exclude_id = line.id if line else None
            validate_product_unique_in_opportunity(
                data['product'],
                opportunity,
                exclude_id
            )
        except ValidationError as e:
            errors['product'] = e.messages
    
    if errors:
        raise ValidationError(errors)
    
    return data


def validate_line_editable(line):
    """Valide qu'une ligne reste modifiable."""
    if not line.opportunity.can_edit():
        raise ValidationError(
            _('Cette ligne ne peut plus etre modifiee'),
            code='line_not_editable'
        )


def validate_insomea_quote_lines_pricing(lines_pricing):
    """
    Valide cohérence pricing pour création devis Insomea
    
    Vérifie que TOUS les prix vente >= prix achat
    
    Args:
        lines_pricing: list[dict] avec unit_price_purchase et unit_price_sale
    
    Raises:
        ValidationError: Si incohérence pricing
    """
    errors = []
    
    for i, line_data in enumerate(lines_pricing):
        purchase = line_data.get('unit_price_purchase')
        sale = line_data.get('unit_price_sale')
        
        if purchase and sale:
            try:
                validate_sale_price_greater_than_purchase(purchase, sale)
                validate_margin_acceptable(purchase, sale)
            except ValidationError as e:
                errors.append({
                    'line_index': i,
                    'line_id': line_data.get('line_id'),
                    'error': e.messages
                })
    
    if errors:
        raise ValidationError({
            'lines_pricing': _('Erreurs de pricing sur certaines lignes'),
            'details': errors
        })


# ═══════════════════════════════════════════════════════════
# NORMALIZERS
# ═══════════════════════════════════════════════════════════

def normalize_opportunity_name(name):
    if not name:
        return name
    name = name.strip()
    if name:
        name = name[0].upper() + name[1:]
    return name


def validate_opportunity_name(name):
    """Valide un nom d'opportunite simple et le normalise pour les serializers."""
    normalized = normalize_opportunity_name(name)
    if not normalized or len(normalized) < 3:
        raise ValidationError(
            _('Le nom doit contenir au moins 3 caracteres'),
            code='invalid_name'
        )
    return normalized


def validate_opportunity_editable(opportunity):
    """Valide qu'une opportunite est encore editable."""
    if not opportunity.can_edit():
        raise ValidationError(
            _('Cette opportunite ne peut plus etre modifiee'),
            code='opportunity_not_editable'
        )
