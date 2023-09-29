import os

REDIS_HOST = os.getenv('REDIS_HOST', '172.17.0.1')
REDIS_AUTH = os.getenv('REDIS_AUTH', '***')
BROKER_URL = os.getenv('BROKER_URL', 'redis://:{REDIS_AUTH}@{REDIS_HOST}:6379/0'.format(REDIS_AUTH=REDIS_AUTH, REDIS_HOST=REDIS_HOST))
