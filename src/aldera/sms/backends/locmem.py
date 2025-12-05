"""
Defines an SMS backend that stores messages in memory. Used mainly for
unit testing an application.

Copyright (c) 2025 Zachary Young.
All rights reserved.
"""

from aldera import sms


class Message:

    def __init__(self, message, recipient_number):
        self.message = message
        self.recipient = recipient_number


class SmsBackend:

    def __init__(self, *args, **kwargs):
        """
        Stores all delivered SMS messages in a list.
        """
        if not hasattr(sms, 'messages'):
            sms.messages = []

    def send_message(self, message, recipient_number):
        """
        Redirect message to mock outbox list.
        """
        sms.messages.append(Message(message, recipient_number))
        return True
