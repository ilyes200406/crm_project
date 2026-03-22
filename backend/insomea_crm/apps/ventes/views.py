from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Opportunity
from .services import OpportunityService


class ReceiveSupplierQuote(APIView):

    def post(self, request, pk):

        opportunity = Opportunity.objects.get(pk=pk)

        OpportunityService.receive_supplier_quote(opportunity)

        return Response({"status": opportunity.status})