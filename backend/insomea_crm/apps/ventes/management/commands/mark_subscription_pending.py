from django.core.management.base import BaseCommand
from apps.ventes.models import Subscription, SubscriptionStatus


class Command(BaseCommand):
    help = '[Dev] Mark ACTIVE subscription(s) as PENDING_RENEWAL to test the renewal flow'

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            type=str,
            dest='subscription_id',
            help='UUID of a specific subscription (omit to process all ACTIVE subscriptions)',
        )

    def handle(self, *args, **options):
        subscription_id = options.get('subscription_id')

        qs = Subscription.objects.filter(status=SubscriptionStatus.ACTIVE)
        if subscription_id:
            qs = qs.filter(id=subscription_id)
            if not qs.exists():
                self.stderr.write(self.style.ERROR(
                    f'No ACTIVE subscription found with id={subscription_id}'
                ))
                return

        count = 0
        for sub in qs:
            sub.mark_pending_renewal()
            sub.save(update_fields=['status'])
            self.stdout.write(f'  → {sub.subscription_number} ({sub.client}) marked PENDING_RENEWAL')
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Done: {count} subscription(s) updated.'))
