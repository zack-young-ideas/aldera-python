"""
Defines a function that retrieves secrets using AWS Secrets Manager.

If no secret with the specified name exists, or AWS Secrets Manager
is unable to be reached, os.environ.get() will be used to see if
the value is available as an environment variable.

Usage:

    from aldera.secrets import get_secret

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'database',
            'USER': get_secret('DB_USER'),
            'PASSWORD': get_secret('DB_PASSWORD'),
            'HOST': get_secret('DB_HOST'),
            'PORT': 3306,
        }
    }
"""

import boto3
import json
import os

from aldera.config import get as get_config


class Secrets:

    def __init__(self):
        self._settings = None
        # self._source is either 'aws' or 'systemd', indicating where
        # secrets should be retrieved from.
        self._source = os.environ.get('ALDERA_SECRETS_SOURCE')

    def _get_aws_secrets(self):
        """
        Retrieves secrets from AWS Secrets Manager.
        """
        region = (
            get_config('AWS_REGION')
            or os.environ.get('AWS_REGION')
            or os.environ.get('AWS_DEFAULT_REGION')
            or 'us-east-1'
        )
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region
        )
        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError:
            get_secret_value_response = {
                'SecretString': os.environ.get(secret_name)
            }

        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret) if secret.startswith('{') else secret
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response['SecretBinary']
            )
            return json.loads(decoded_binary_secret)

    def _get_systemd_secrets(self):
        """
        Retrieve secrets from encrypted credential file.

        The environment variable ALDERA_SECRETS references a file on the
        local filesystem that contains secrets. These secrets are used
        to define Django settings.
        """
        creds_file = os.environ.get('ALDERA_SECRETS')
        if creds_file is None:
            raise ValueError(''.join([
                "Environment variable 'ALDERA_SECRETS' is not defined. ",
                'Unable to locate secrets file.'
            ]))
        with open(creds_file, 'r') as secrets:
            return json.loads(secrets.read().strip())

    def _settings(self):
        if self._settings is None:
            if self._source == 'aws':
                self._settings = self._get_aws_secrets()
            else:
                self._settings = self._get_systemd_secrets()
        return self._settings


def secrets_wrapper():
    secrets = Secrets()

    def get_secret(secret_name):
        """
        Convenience function for retrieving values from secrets._settings.
        """
        return secrets._settings[secret_name]

    return get_secret


get_secret = secrets_wrapper()
