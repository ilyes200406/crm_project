from config.settings import *  # noqa: F401, F403

DATABASES['default']['HOST'] = 'localhost'
DATABASES['default']['OPTIONS'] = {'options': '-c lc_messages=C'}
