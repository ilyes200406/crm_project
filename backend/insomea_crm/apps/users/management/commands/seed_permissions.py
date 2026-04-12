"""
SEED PERMISSIONS MANAGEMENT COMMAND

Usage:
    python manage.py seed_permissions

What it does:
    1. Creates (or updates) every Permission row in rbac_permissions.
    2. Creates (or updates) every RolePermission row in rbac_role_permissions.

This is idempotent — safe to run multiple times.  It will never delete
existing rows (so manually granted extra permissions survive re-runs).

When to run:
    - After the first migration that creates the rbac_* tables.
    - After adding a new codename to the PERMISSIONS list below.
    - On each deployment if you want defaults to be guaranteed present.

Why this exists instead of a data migration:
    Data migrations run once and are hard to re-run.  A management command
    can be re-run safely any time and is easier to inspect/edit.
"""

from django.core.management.base import BaseCommand
from django.db import transaction


# ── Permission definitions ─────────────────────────────────────────────────
#
# Format: (codename, human-readable name)
# ADMIN is NOT included — it bypasses all permission checks in code.

PERMISSIONS = [
    # Opportunity
    ('opportunity.view',                    'Voir une opportunité'),
    ('opportunity.create',                  'Créer une opportunité'),
    ('opportunity.update',                  'Modifier une opportunité'),
    ('opportunity.delete',                  'Supprimer une opportunité'),
    ('opportunity.cancel',                  'Annuler une opportunité'),
    ('opportunity.request_supplier_quotes', 'Demander devis fournisseurs'),
    ('opportunity.create_insomea_quote',    'Créer devis Insomea'),
    ('opportunity.request_client_po',       'Demander BC client'),
    ('opportunity.upload_client_po',        'Uploader BC client reçu'),
    ('opportunity.update_insomea_quote',    'Réviser devis Insomea (négociation)'),
    ('opportunity.rollback_insomea_quote', 'Revenir au devis Insomea (modifier prix vente)'),
    ('opportunity.approve',                 'Approuver une opportunité'),
    ('opportunity.create_insomea_pos',      'Créer POs Insomea'),
    # Supplier quote
    ('supplier_quote.create',               'Créer devis fournisseur'),
    # Provision
    ('provision.view',                      'Voir les provisions'),
    ('provision.start',                     'Démarrer le provisionnement'),
    ('provision.complete',                  'Compléter le provisionnement'),
    ('provision.fail',                      'Signaler échec provisionnement'),
    ('provision.retry',                     'Relancer le provisionnement'),
    # Subscription
    ('subscription.view',                   'Voir les subscriptions'),
    ('subscription.create_renewal',         'Créer opportunité renouvellement'),
    ('subscription.cancel',                 'Annuler une subscription'),
    # InsomeaPO
    ('insomea_po.send',                     'Envoyer BC Insomea au fournisseur'),
    ('insomea_po.confirm',                  'Confirmer reception BC Insomea'),

]


# ── Role -> permission mapping ──────────────────────────────────────────────
#
# Each entry: role string -> list of codenames that role can perform.
# ADMIN is intentionally absent (it bypasses the table entirely).

ROLE_PERMISSIONS = {
    'COMMERCIAL': [
        'opportunity.view',
        'opportunity.create',
        'opportunity.update',
        'opportunity.delete',
        'opportunity.cancel',
        'opportunity.request_supplier_quotes',
        'opportunity.create_insomea_quote',
        'opportunity.request_client_po',
        'opportunity.upload_client_po',
        'opportunity.update_insomea_quote',
        'opportunity.rollback_insomea_quote',
        'supplier_quote.create',
        'provision.view',
        'subscription.view',
        'subscription.create_renewal',
    ],
    'FINANCE': [
        'opportunity.view',
        'opportunity.cancel',
        'opportunity.approve',
        'opportunity.create_insomea_pos',
        'insomea_po.send',
        'insomea_po.confirm',
        'provision.view',
        'subscription.view',
        'subscription.cancel',
    ],
    'TECHNICIEN': [
        'opportunity.view',
        'provision.view',
        'provision.start',
        'provision.complete',
        'provision.fail',
        'provision.retry',
        'subscription.view',
    ],
}



class Command(BaseCommand):
    help = 'Seed default RBAC permissions and role->permission mappings'

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.users.models.permission import Permission, RolePermission

        self.stdout.write('Seeding permissions…')

        # Step 1 — Create/update Permission rows
        perm_objects = {}
        created_count = 0
        for codename, name in PERMISSIONS:
            obj, created = Permission.objects.update_or_create(
                codename=codename,
                defaults={'name': name},
            )
            perm_objects[codename] = obj
            if created:
                created_count += 1
                self.stdout.write(f'  + Permission: {codename}')

        self.stdout.write(
            self.style.SUCCESS(
                f'  {created_count} new permission(s) created, '
                f'{len(PERMISSIONS) - created_count} already existed.'
            )
        )

        # Step 2 — Create/update RolePermission rows
        self.stdout.write('Seeding role->permission mappings…')
        rp_created = 0
        for role, codenames in ROLE_PERMISSIONS.items():
            for codename in codenames:
                perm = perm_objects.get(codename)
                if perm is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ Codename not found, skipping: {codename}'
                        )
                    )
                    continue
                _, created = RolePermission.objects.get_or_create(
                    role=role,
                    permission=perm,
                )
                if created:
                    rp_created += 1
                    self.stdout.write(f'  + {role} -> {codename}')

        self.stdout.write(
            self.style.SUCCESS(
                f'  {rp_created} new role->permission mapping(s) created.'
            )
        )
        self.stdout.write(self.style.SUCCESS('Done.'))
