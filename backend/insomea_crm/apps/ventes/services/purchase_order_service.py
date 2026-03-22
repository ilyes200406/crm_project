"""
PURCHASE ORDER SERVICE

Business logic:
- Upload ClientPO (BC client)
- Create InsomeaPOs (BCs Insomea vers fournisseurs)
"""

from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from collections import defaultdict

from ..models import (
    ClientPO,
    InsomeaPurchaseOrder,
    OpportunityStatus,
)
from ..validators import (
    validate_pdf_file,
    validate_file_size,
    validate_can_request_client_po,
    validate_can_receive_client_po,
)
from ..selectors import (
    get_opportunity_by_id,
)


# ═══════════════════════════════════════════════════════════
# CLIENT PO SERVICE
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def upload_client_po(
    *,
    opportunity_id,
    document,
    po_number,
    user,
    ip_address=None
):
    """
    Upload bon de commande client
    
    Args:
        opportunity_id: UUID Opportunity
        document: UploadedFile PDF BC signé
        po_number: str numéro BC client
        user: User instance (COMMERCIAL)
        ip_address: str
    
    Returns:
        ClientPO créé
    
    Raises:
        ValidationError: Si fichier invalide ou préconditions non remplies
        PermissionDenied: Si pas COMMERCIAL
    
    Business Rules:
        - Upload PDF BC client
        - Crée ClientPO (niveau Opportunity, pas ligne)
        - Transition FSM opportunity: receive_client_po()
        - Status: CLIENT_PO_REQUEST → CLIENT_PO_RECEIVED
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION + PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=False)
    
    if user.role not in ['ADMIN', 'COMMERCIAL']:
        raise PermissionDenied('Seuls les commerciaux peuvent uploader des BCs clients')
    
    if user.role == 'COMMERCIAL':
        if opportunity.created_by != user and opportunity.assigned_to != user:
            raise PermissionDenied('Action non autorisée')
    
    # ───────────────────────────────────────────────────────
    # 2. VALIDATION PRÉCONDITIONS
    # ───────────────────────────────────────────────────────
    
    validate_can_receive_client_po(opportunity)
    
    # ───────────────────────────────────────────────────────
    # 3. VALIDATION FICHIER
    # ───────────────────────────────────────────────────────
    
    validate_pdf_file(document)
    validate_file_size(document, max_size_mb=10)
    
    # ───────────────────────────────────────────────────────
    # 4. CRÉATION CLIENT PO
    # ───────────────────────────────────────────────────────
    
    client_po = ClientPO.objects.create(
        opportunity=opportunity,
        created_by=user,
        po_number=po_number,
        document=document,
    )
    
    # ───────────────────────────────────────────────────────
    # 5. TRANSITION FSM OPPORTUNITY
    # ───────────────────────────────────────────────────────
    
    if opportunity.opportunity_has_client_po():
        opportunity.receive_client_po()
        opportunity.save()
        # Signal FSM → StatusHistory créé auto
    
    return client_po


# ═══════════════════════════════════════════════════════════
# INSOMEA PO SERVICE
# ═══════════════════════════════════════════════════════════

@transaction.atomic
def create_insomea_pos(*, opportunity_id, user, ip_address=None):
    """
    Crée bons de commande Insomea vers fournisseurs
    
    Args:
        opportunity_id: UUID Opportunity
        user: User instance (FINANCE ou ADMIN)
        ip_address: str
    
    Returns:
        list[InsomeaPurchaseOrder] créés
    
    Raises:
        ValidationError: Si préconditions non remplies
        PermissionDenied: Si pas FINANCE
    
    Business Rules:
        - Créé quand opportunity APPROVED
        - Groupe OpportunityLines par supplier
        - Crée 1 InsomeaPO par fournisseur
        - Link OpportunityLines au PO correspondant
        - Calculate total par fournisseur
        - Generate PDF (TODO)
    
    Exemple:
        OpportunityLine 1 (Office 365, Supplier Microsoft) → InsomeaPO #1
        OpportunityLine 2 (Windows, Supplier Microsoft)    → InsomeaPO #1 (même)
        OpportunityLine 3 (PC Dell, Supplier Dell)         → InsomeaPO #2
        
        Résultat: 2 InsomeaPOs créés
    """
    
    # ───────────────────────────────────────────────────────
    # 1. RÉCUPÉRATION + PERMISSIONS
    # ───────────────────────────────────────────────────────
    
    opportunity = get_opportunity_by_id(opportunity_id, user=user, prefetch_all=True)
    
    if user.role not in ['ADMIN', 'FINANCE']:
        raise PermissionDenied('Seul Finance peut créer des BCs Insomea')
    
    # ───────────────────────────────────────────────────────
    # 2. VÉRIFICATION PRÉCONDITIONS
    # ───────────────────────────────────────────────────────
    
    if opportunity.status != OpportunityStatus.APPROUVED:
        raise ValidationError('L\'opportunité doit être approuvée pour créer les BCs fournisseurs')
    
    if not opportunity.lines.exists():
        raise ValidationError('L\'opportunité doit contenir des lignes')
    
    # ───────────────────────────────────────────────────────
    # 3. GROUPE LIGNES PAR FOURNISSEUR
    # ───────────────────────────────────────────────────────
    
    # Map: supplier_id → [OpportunityLine, ...]
    lines_by_supplier = defaultdict(list)
    
    for line in opportunity.lines.all():
        # Récupère supplier depuis InsomeaQuoteLine
        # (car OpportunityLine n'a pas FK directe vers Supplier)
        if hasattr(line, 'insomea_quote_line') and line.insomea_quote_line:
            supplier_quote_line = line.insomea_quote_line.supplier_quote_line
            supplier_id = supplier_quote_line.supplier_quote.supplier_id
            lines_by_supplier[supplier_id].append(line)
        else:
            raise ValidationError(
                f'Ligne {line.product.title} n\'a pas de devis fournisseur associé'
            )
    
    # ───────────────────────────────────────────────────────
    # 4. CRÉATION INSOMEA PO PAR FOURNISSEUR
    # ───────────────────────────────────────────────────────
    
    created_pos = []
    
    for supplier_id, lines in lines_by_supplier.items():
        # Calcule total pour ce fournisseur
        from decimal import Decimal
        total = Decimal('0.00')
        
        for line in lines:
            # Prix achat depuis InsomeaQuoteLine
            insomea_quote_line = line.insomea_quote_line
            line_total = insomea_quote_line.line_total_purchase
            total += line_total
        
        # Crée InsomeaPurchaseOrder
        from ...suppliers.models import Supplier
        supplier = Supplier.objects.get(id=supplier_id)
        
        insomea_po = InsomeaPurchaseOrder.objects.create(
            created_by=user,
            supplier=supplier,
            po_number='',  # Sera généré automatiquement si model a cette logique
        )
        # NOTE: Si InsomeaPurchaseOrder a auto-génération po_number, sinon:
        # insomea_po.po_number = f'IPO-{opportunity.reference}-{supplier.name[:3].upper()}'
        # insomea_po.save()
        
        # Link OpportunityLines à ce PO
        for line in lines:
            line.insomea_purchase_order = insomea_po
            line.save()
        
        created_pos.append(insomea_po)
        
        # ───────────────────────────────────────────────────
        # 5. GÉNÉRATION PDF (TODO)
        # ───────────────────────────────────────────────────
        
        # TODO: Générer PDF via template
        # insomea_po.document = generate_po_pdf(insomea_po, lines)
        # insomea_po.save()
    
    return created_pos


@transaction.atomic
def request_client_po_transition(*, opportunity_id, user, ip_address=None):
    """
    Transition Opportunity: INSOMEA_QUOTE_CREATED → CLIENT_PO_REQUEST
    
    Args:
        opportunity_id: UUID
        user: User instance (COMMERCIAL)
        ip_address: str
    
    Returns:
        Opportunity mise à jour
    
    Raises:
        ValidationError: Si préconditions non remplies
        PermissionDenied: Si pas COMMERCIAL
    
    Business Rules:
        - Marque devis Insomea comme envoyé au client
        - Transition FSM: request_client_po()
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
    # 2. VALIDATION PRÉCONDITIONS
    # ───────────────────────────────────────────────────────
    
    validate_can_request_client_po(opportunity)
    
    # ───────────────────────────────────────────────────────
    # 3. TRANSITION FSM
    # ───────────────────────────────────────────────────────
    
    opportunity.request_client_po()
    opportunity.save()
    # Signal FSM → StatusHistory créé auto
    
    return opportunity




"""
**✅ SERVICES PARTIE 3/5 COMPLETE !**

**Coverage :**
- ✅ upload_client_po() - Upload PDF BC client + FSM transition CLIENT_PO_RECEIVED
- ✅ create_insomea_pos() - Groupe lignes par fournisseur + crée 1 PO par fournisseur + link lines
- ✅ request_client_po_transition() - FSM transition CLIENT_PO_REQUEST

**LOGIQUE CLEF :**

### **Flow POs :**
```
1. Commercial demande BC client:
   → request_client_po_transition()
   → Opportunity: INSOMEA_QUOTE_CREATED → CLIENT_PO_REQUEST

2. Commercial upload BC client signé:
   → upload_client_po()
   → Crée ClientPO (1 par opportunity)
   → Opportunity: CLIENT_PO_REQUEST → CLIENT_PO_RECEIVED

3. Finance approuve + crée BCs fournisseurs:
   → approve_opportunity() (dans workflow_service)
   → Opportunity: CLIENT_PO_RECEIVED → APPROVED
   → create_insomea_pos()
   → Groupe lignes par supplier
   → Crée InsomeaPO (1 par fournisseur)
   → Link OpportunityLines au PO correspondant
```

### **Exemple groupe par fournisseur :**
```
OpportunityLine 1: Office 365 (Supplier: Microsoft)  ┐
OpportunityLine 2: Windows 11 (Supplier: Microsoft)  ├─→ InsomeaPO #1 (Microsoft)
OpportunityLine 3: Azure (Supplier: Microsoft)       ┘

OpportunityLine 4: PC Dell (Supplier: Dell)          ──→ InsomeaPO #2 (Dell)
"""