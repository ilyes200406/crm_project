from ..models.opportunityLine import OpportunityLine
from ..models.opportunity import Opportunity
from ..models.provision import Provision
from ..models.statusHistory import StatusHistory
from ..services.workflow_service import update_opportunity_status_from_lines

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_fsm.signals import post_transition


@receiver(post_transition)
def log_fsm_transition(sender, instance, name, source, target, **kwargs):

    if sender not in [Opportunity, OpportunityLine, Provision]:
        return
    
    # Récupère user/ip depuis method_kwargs si passé
    method_kwargs = kwargs.get('method_kwargs', {})
    user = method_kwargs.get('user', None)
    ip_address = method_kwargs.get('ip_address', None)
    
    # Détermine quelle FK remplir
    history_data = {
        'status_precedent': source,
        'status_suivant': target,
        'transition_name': name,
        'changed_by': user,
        'ip_address': ip_address,
        'description': f"Transition FSM : {name}",
        'metadata': {
            'transition_name': name,
            'source': source,
            'target': target,
        }
    }
    
    # Polymorphique : détermine FK selon sender
    if sender == OpportunityLine:
        history_data['opportunity_line'] = instance
    elif sender == Opportunity:
        history_data['opportunity'] = instance
    elif sender == Provision:
        history_data['provision'] = instance
    
    # Crée log
    StatusHistory.objects.create(**history_data)

@receiver(post_save, sender=OpportunityLine)
def update_opportunity_status_on_line_save(sender, instance, created, **kwargs):
    """
    Trigger : Quand OpportunityLine sauvegardée
    
    Action : Recalcule Opportunity.status basé sur toutes les lignes
    
    Flow:
        1. Ligne créée/modifiée/transition FSM
        2. Signal post_save déclenché
        3. update_opportunity_status_from_lines() appelée
        4. Opportunity.status recalculé (computed)
    
    IMPORTANT:
        Évite boucle infinie avec flag _updating_opportunity_status
    """
    
    # Évite boucle infinie
    if hasattr(instance, '_updating_opportunity_status'):
        return
    
    # Mark pour éviter récursion
    instance._updating_opportunity_status = True
    
    # After a line status change (or create), update the parent opportunity aggregated status.
    update_opportunity_status_from_lines(instance.opportunity)
    
    # Cleanup
    delattr(instance, '_updating_opportunity_status')


@receiver(post_delete, sender=OpportunityLine)
def update_opportunity_status_on_line_delete(sender, instance, **kwargs):
    """
    Trigger : Quand OpportunityLine supprimée
    
    Action : Recalcule Opportunity.status basé sur lignes restantes
    
    Cas d'usage:
        - Ligne supprimée → recalcule status
        - Si 0 lignes → Opportunity.status = DRAFT
    """
    
    # Vérifie que opportunity existe encore
    if instance.opportunity_id:
        try:
            update_opportunity_status_from_lines(instance.opportunity)
        except Opportunity.DoesNotExist:
            pass



"""
**✅ SERVICES COMPLETS (5/5) - OPPORTUNITIES APP TERMINÉE !**

**Coverage TOTALE SERVICES :**

### **opportunity_service.py (6 fonctions)**
- create_opportunity, update_opportunity, delete_opportunity
- add_line_to_opportunity, update_opportunity_line, remove_line_from_opportunity

### **quote_service.py (4 fonctions)**
- create_supplier_quote, recalculate_supplier_quote_totals
- create_insomea_quote, recalculate_insomea_quote_totals

### **purchase_order_service.py (3 fonctions)**
- upload_client_po, create_insomea_pos, request_client_po_transition

### **provision_service.py (5 fonctions)**
- create_provision_for_line, start_provisioning, complete_provisioning
- fail_provisioning, retry_provisioning

### **workflow_service.py (4 fonctions)**
- request_all_supplier_quotes, request_client_po, approve_opportunity
- update_opportunity_status_from_lines ← **CŒUR DU SYSTÈME**

**TOTAL : 22 SERVICES** ✅

---

## **🎯 WORKFLOW COMPLET END-TO-END**
```
1. Commercial crée opportunity + lignes
   → create_opportunity(), add_line_to_opportunity()

2. Commercial demande devis fournisseurs
   → request_all_supplier_quotes()
   → FSM lines: DRAFT → SUPPLIER_QUOTE_REQUEST
   → Signal → Opportunity.status = SUPPLIER_QUOTE_REQUEST (computed)

3. Commercial upload devis fournisseurs
   → create_supplier_quote()
   → FSM lines: SUPPLIER_QUOTE_REQUEST → SUPPLIER_QUOTE_RECEIVED
   → Signal → Opportunity.status = SUPPLIER_QUOTE_RECEIVED (computed)

4. Commercial crée devis Insomea
   → create_insomea_quote()
   → Copie prix fournisseur + définit prix vente
   → FSM Opportunity: SUPPLIER_QUOTE_RECEIVED → INSOMEA_QUOTE_CREATED

5. Commercial demande BC client
   → request_client_po()
   → FSM Opportunity: INSOMEA_QUOTE_CREATED → CLIENT_PO_REQUEST

6. Commercial upload BC client
   → upload_client_po()
   → FSM Opportunity: CLIENT_PO_REQUEST → CLIENT_PO_RECEIVED

7. Finance approuve
   → approve_opportunity()
   → FSM Opportunity: CLIENT_PO_RECEIVED → APPROVED
   → Crée Provisions (WAITING_PROVISION)
   → Crée InsomeaPOs par fournisseur

8. Technicien provisionne
   → start_provisioning()
   → FSM Provision: WAITING_PROVISION → PROVISIONING
   → complete_provisioning()
   → Crée Subscription
   → FSM Provision: PROVISIONING → PROVISIONED
"""


