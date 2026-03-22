from django_fsm import can_proceed
from .stateMachine import OpportunityStateMachine


class OpportunityService:

    @staticmethod
    def receive_supplier_quote(opportunity):

        sm = OpportunityStateMachine()

        if not can_proceed(sm.receive_supplier_quote):
            raise Exception("Invalid transition")

        sm.receive_supplier_quote(opportunity)
        opportunity.save()


    @staticmethod
    def create_client_quote(opportunity):

        sm = OpportunityStateMachine()

        if not can_proceed(sm.create_client_quote):
            raise Exception("Invalid transition")

        sm.create_client_quote(opportunity)
        opportunity.save()


    @staticmethod
    def receive_client_po(opportunity):

        sm = OpportunityStateMachine()

        if not can_proceed(sm.receive_client_po):
            raise Exception("Invalid transition")

        sm.receive_client_po(opportunity)
        opportunity.save()


    @staticmethod
    def start_provisioning(opportunity):

        sm = OpportunityStateMachine()

        if not can_proceed(sm.start_provisioning):
            raise Exception("Invalid transition")

        sm.start_provisioning(opportunity)
        opportunity.save()


    @staticmethod
    def create_contract(opportunity):

        sm = OpportunityStateMachine()

        if not can_proceed(sm.create_contract):
            raise Exception("Invalid transition")

        sm.create_contract(opportunity)
        opportunity.save()