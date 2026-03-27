import uuid

from django.db import models
from ...users.models.users import User
from ...suppliers.models import Supplier

def get_upload_path(instance, filename):
    return f'po/{instance.opportunity.reference}/supplier/{filename}'

class InsomeaPurchaseOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='Client_PO_created', limit_choices_to={'role': 'FINANCE'}, help_text="Finance créateur")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    po_number = models.CharField(max_length=100)
    document = models.FileField(upload_to=get_upload_path)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)