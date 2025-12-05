"""
Defines an SMS backend that sends messages using AWS SNS.

Copyright (c) 2025 Zachary Young.
All rights reserved.
"""

import os

import boto3
import botocore

from aldera.config import get as get_config


class SmsBackend:

    def __init__(self, *args, **kwargs):
        """
        Initializes boto3 client.
        """
        self.client = boto3.client(
            'sns',
            region_name=self._get_region()
        )

    def _get_region(self):
        """
        Determines AWS region in order of priority:
        1. Django ALDERA.AWS_REGION setting
        2. AWS_REGION environment variable
        3. AWS_DEFAULT_REGION environment variable
        4. 'us-east-1'
        """
        region = (
            get_config('AWS_REGION')
            or os.environ.get('AWS_REGION')
            or os.environ.get('AWS_DEFAULT_REGION')
            or 'us-east-1'
        )
        return region

    def send_message(self, message, recipient_number):
        """
        Send message using AWS SNS.
        """
        try:
            self.client.publish(
                PhoneNumber=recipient_number,
                Message=message,
            )
            return True
        except botocore.exceptions.ClientError as error:
            if get_config('DEBUG', False):
                raise
            return False
