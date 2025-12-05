"""
Defines an AppConfig subclass used to initialize the aldera
configuration object for use in Django websites.

Copyright (c) Zachary Young.
All rights reserved.
"""

from django.apps import AppConfig
from aldera import config
from django.conf import settings


class AlderaConfig(AppConfig):
    name = 'aldera'
    label = 'aldera'
    verbose_name = 'Aldera SMS'

    def ready(self):
        config.load_dict(getattr(settings, 'ALDERA', {}))
        config.set(DEBUG=getattr(settings, 'DEBUG', False))
