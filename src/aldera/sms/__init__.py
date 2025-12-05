"""
Defines functions used to send SMS messages using AWS SNS.

Copyright (c) 2025 Zachary Young.
All rights reserved.
"""

from aldera.config import get as get_config
from aldera.sms import backends


DEFAULT_BACKEND = 'locmem'


def get_connection(backend=None, **kwargs):
    """
    Load an SMS backend and return an instance of it.
    """
    _backend = backend or get_config('SMS_BACKEND', DEFAULT_BACKEND)
    klass = backends.backend_classes.get(_backend)
    return klass(**kwargs)


def send_sms_message(
    message,
    recipient_number,
    connection=None
):
    """
    Send a message to the specified number.

    Args:
        message (str): The message to send
        recipient_number (str): The phone number to send to
        connection (connection class or None): the connection object
            that sends messages
    """
    sms = connection or get_connection()
    return sms.send_message(message, recipient_number)


async def send_async_message(
    message,
    recipient_number,
    connection=None
):
    """
    Send a message asynchronously.

    Args:
        message (str): The message to send
        recipient_number (str): The phone number to send to
        connection (connection class or None): the connection object
            that sends messages
    """
    sms = connection or get_connection()
    return await sms.send_message(message, recipient_number)
