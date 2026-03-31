import uuid
from django.db import models

from .opportunity import Opportunity
from ...users.models.users import User

class ClientPO(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.OneToOneField(Opportunity, related_name="client_purchase_order", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='Client_po_created', limit_choices_to={'role': 'COMMERCIAL'}, help_text="Commercial créateur")
    
    po_number = models.CharField(max_length=100)
    document = models.FileField(upload_to='po/client/')
    recieved_at = models.DateTimeField(auto_now_add=True, db_index=True)

    @property
    def received_at(self):
        return self.recieved_at

    @property
    def created_at(self):
        return self.recieved_at
