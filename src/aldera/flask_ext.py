"""
Defines a Flask extension for initializing Aldera configuration for use
in Flask websites.

Copyright (c) 2025 Zachary Young.
All rights reserved.
"""

from aldera import config as aldera_config


class Aldera:
    """
    Flask extension for Aldera.

    Usage:

        from aldera.flask_ext import Aldera
        aldera = Aldera()

        def create_app():
            app = Flask(__name__)
            app.config['ALDERA_SMS_BACKEND'] = 'aws'
            app.config['ALDERA_AWS_REGION'] = 'us-east-1'
            aldera.init_app(app)
            return app
    """

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Bind Aldera configuration values from the Flask app to Aldera's
        internal configuration registry.
        """
        aldera_keys = {
            key.replace('ALDERA_', ''): app.config[key]
            for key in app.config
            if key.startswith('ALDERA_')
        }
        aldera_config.load_dict(**aldera_keys)
        aldera_config.set(DEBUG=getattr(app.config, 'DEBUG', False))
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['aldera'] = self

    @staticmethod
    def get_config(key, default=None):
        """
        Read Aldera config inside view functions.
        """
        return aldera_config.get(key, default)
