import uuid

from django.db import models
from ...users.models.users import User
from ...suppliers.models import Supplier


class InsomeaPurchaseOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='Client_PO_created', limit_choices_to={'role': 'FINANCE'}, help_text="Finance créateur")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL)

    po_number = models.CharField(max_length=100)
    document = models.FileField(upload_to="po/")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)