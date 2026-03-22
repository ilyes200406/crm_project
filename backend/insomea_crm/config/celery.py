"""
CELERY CONFIGURATION

Celery app pour tasks asynchrones
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery app
app = Celery('insomea_crm')

# Load config from Django settings (namespace CELERY)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task"""
    print(f'Request: {self.request!r}')