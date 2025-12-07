"""
Flask extension for sending emails via AWS SES v2 (SESV2).
"""

import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import logging

import boto3
from botocore.exceptions import ClientError

from aldera import config as aldera_config


logger = logging.getLogger(__name__)


class Message:
    """
    Email message class.

    Args:
        subject (str): Email subject
        recipients (list): List of recipient email addresses
        body (str): Email body (plain text or HTML based on html parameter)
        sender (str, optional): Sender email address.
        cc (list, optional): List of CC recipients
        bcc (list, optional): List of BCC recipients
        reply_to (list, optional): List of reply-to addresses
        html (str, optional): HTML body content
        attachments (list, optional): List of attachments
        charset (str, optional): Character encoding. Defaults to 'UTF-8'
    """

    def __init__(self, subject='', recipients=None, body='', sender=None,
                 cc=None, bcc=None, reply_to=None, html=None,
                 attachments=None, charset='UTF-8'):
        self.subject = subject
        self.recipients = recipients or []
        self.body = body
        self.sender = sender
        self.cc = cc or []
        self.bcc = bcc or []
        self.reply_to = reply_to or []
        self.html = html
        self.attachments = attachments or []
        self.charset = charset

    def attach(self, filename, content_type, data):
        """
        Attach a file to the message.

        Args:
            filename (str): Name of the file
            content_type (str): MIME type (e.g., 'application/pdf')
            data (bytes): File content as bytes
        """
        self.attachments.append((filename, content_type, data))

    def attach_file(self, filepath):
        """
        Attach a file from filesystem.

        Args:
            filepath (str): Path to the file
        """
        import os
        import mimetypes

        filename = os.path.basename(filepath)
        content_type, _ = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = 'application/octet-stream'
        with open(filepath, 'rb') as f:
            data = f.read()
        self.attach(filename, content_type, data)


class AlderaEmail:
    """
    Flask extension for AWS SES v2 email sending.

    Usage:
        from flask import Flask
        from aldera.mail.flask_mail import AlderaEmail, Message

        mail = AlderaSMS()

        def create_app():
            app = Flask(__name__)
            app.config['ALDERA_AWS_REGION'] = 'us-east-1'
            app.config['ALDERA_CONFIGURATION_SET'] = 'config-set'
            mail.init_app(app)
            return app

        @app.route('/send')
        def send_email():
            msg = Message(
                subject='Hello',
                recipients=['user@example.com'],
                body='This is a test email'
            )
            mail.send(msg)
            return 'Email sent!'
    """

    def __init__(self, app=None):
        self.app = app
        self._client = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize the extension with a Flask app.
        """
        aldera_keys = {
            key.replace('ALDERA_', ''): app.config[key]
            for key in app.config
            if key.startswith('ALDERA_')
        }
        aldera_config.load_dict(**aldera_keys)
        aldera_config.set(DEBUG=getattr(app.config, 'DEBUG', False))
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['aldera_email'] = self

    @property
    def client(self):
        """
        Lazy initialization of boto3 SESv2 client.
        """
        if self._client is None:
            region = (
                aldera_config.get('AWS_REGION')
                or os.environ.get('AWS_REGION')
                or 'us-east-1'
            )
            self._client = boto3.client('sesv2', region_name=region)
        return self._client

    def send(self, message):
        """
        Send an email message.

        Args:
            message (Message): The message to send

        Returns:
            dict: Response from AWS SES containing MessageId

        Raises:
            ValueError: If message is invalid
            ClientError: If AWS SES returns an error
        """
        # Validate message
        if not message.recipients:
            raise ValueError("Message must have at least one recipient")
        if not message.subject:
            raise ValueError("Message must have a subject")
        if not message.sender:
            raise ValueError("Message must have a sender")
        # Send the message
        if message.attachments:
            return self._send_raw(message)
        else:
            return self._send_simple(message)

    def _send_simple(self, message):
        """
        Send a simple email without attachments.
        """
        # Build email content
        email_content = {
            'Simple': {
                'Subject': {
                    'Data': message.subject,
                    'Charset': message.charset
                },
                'Body': {}
            }
        }
        # Add text body
        if message.body:
            email_content['Simple']['Body']['Text'] = {
                'Data': message.body,
                'Charset': message.charset
            }
        # Add HTML body
        if message.html:
            email_content['Simple']['Body']['Html'] = {
                'Data': message.html,
                'Charset': message.charset
            }
        # Build destination
        destination = {
            'ToAddresses': message.recipients
        }
        if message.cc:
            destination['CcAddresses'] = message.cc
        if message.bcc:
            destination['BccAddresses'] = message.bcc
        # Build request parameters
        params = {
            'FromEmailAddress': message.sender,
            'Destination': destination,
            'Content': email_content
        }
        # Add configuration set if specified
        config_set = aldera_config.get('CONFIGURATION_SET', None)
        if config_set:
            params['ConfigurationSetName'] = config_set
        # Add reply-to if specified
        if message.reply_to:
            params['ReplyToAddresses'] = message.reply_to
        try:
            response = self.client.send_email(**params)
            logger.info(
                f"Email sent successfully. MessageId: {response['MessageId']}"
            )
            return response
        except ClientError as e:
            logger.error(
                f"Failed to send email: {e.response['Error']['Message']}"
            )
            raise

    def _send_raw(self, message):
        """
        Send a raw MIME email with attachments.
        """
        # Create MIME message
        msg = MIMEMultipart()
        msg['Subject'] = message.subject
        msg['From'] = message.sender
        msg['To'] = ', '.join(message.recipients)
        if message.cc:
            msg['Cc'] = ', '.join(message.cc)
        if message.reply_to:
            msg['Reply-To'] = ', '.join(message.reply_to)
        # Add text body
        if message.body:
            msg.attach(MIMEText(message.body, 'plain', message.charset))
        # Add HTML body
        if message.html:
            msg.attach(MIMEText(message.html, 'html', message.charset))
        # Add attachments
        for filename, content_type, data in message.attachments:
            part = MIMEBase(*content_type.split('/'))
            part.set_payload(data)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            msg.attach(part)
        # Build destination
        destination = {
            'ToAddresses': message.recipients
        }
        if message.cc:
            destination['CcAddresses'] = message.cc
        if message.bcc:
            destination['BccAddresses'] = message.bcc
        # Build request parameters
        params = {
            'Content': {
                'Raw': {
                    'Data': msg.as_bytes()
                }
            },
            'Destination': destination
        }
        # Add configuration set if specified
        config_set = aldera_config.get('CONFIGURATION_SET', None)
        if config_set:
            params['ConfigurationSetName'] = config_set
        try:
            response = self.client.send_email(**params)
            logger.info(
                f"Email sent successfully. MessageId: {response['MessageId']}"
            )
            return response
        except ClientError as e:
            logger.error(
                f"Failed to send email: {e.response['Error']['Message']}"
            )
            raise

    def send_message(self, subject, recipients, body, **kwargs):
        """
        Convenience method to send a message without creating a Message object.

        Args:
            subject (str): Email subject
            recipients (list or str): Recipient email address(es)
            body (str): Email body
            **kwargs: Additional arguments passed to Message constructor

        Returns:
            dict: Response from AWS SES
        """
        if isinstance(recipients, str):
            recipients = [recipients]
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            **kwargs
        )
        return self.send(msg)
