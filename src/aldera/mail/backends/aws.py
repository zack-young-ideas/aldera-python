import boto3
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from botocore.exceptions import ClientError
import logging


logger = logging.getLogger(__name__)


class AWSEmailBackend(BaseEmailBackend):
    """
    Django email backend using AWS SES v2 API.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        aldera_config = getattr(settings, 'ALDERA', {})
        self.region_name = getattr(
            aldera_config,
            'AWS_REGION',
            'us-east-1'
        )
        self.configuration_set = getattr(
            aldera_config,
            'CONFIGURATION_SET',
            None
        )
        self._client = None

    @property
    def client(self):
        """
        Lazy initialization of boto3 SESv2 client.
        """
        if self._client is None:
            self._client = boto3.client('sesv2', region_name=self.region_name)
        return self._client

    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number sent.
        """
        if not email_messages:
            return 0

        sent_count = 0
        for message in email_messages:
            if self._send(message):
                sent_count += 1

        return sent_count

    def _send(self, message):
        """
        Send a single EmailMessage.
        """
        if not message.recipients():
            return False

        try:
            # Build the email content
            email_content = {
                'Simple': {
                    'Subject': {
                        'Data': message.subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {}
                }
            }

            # Add body content
            if message.content_subtype == 'html':
                email_content['Simple']['Body']['Html'] = {
                    'Data': message.body,
                    'Charset': 'UTF-8'
                }
            else:
                email_content['Simple']['Body']['Text'] = {
                    'Data': message.body,
                    'Charset': 'UTF-8'
                }

            # Handle multipart messages (text + html)
            if hasattr(message, 'alternatives') and message.alternatives:
                for alt_content, alt_type in message.alternatives:
                    if alt_type == 'text/html':
                        email_content['Simple']['Body']['Html'] = {
                            'Data': alt_content,
                            'Charset': 'UTF-8'
                        }

            # Build destination
            destination = {
                'ToAddresses': message.to,
            }

            if message.cc:
                destination['CcAddresses'] = message.cc

            if message.bcc:
                destination['BccAddresses'] = message.bcc

            # Build the request parameters
            params = {
                'FromEmailAddress': message.from_email,
                'Destination': destination,
                'Content': email_content,
            }

            # Add configuration set if specified
            if self.configuration_set:
                params['ConfigurationSetName'] = self.configuration_set

            # Add reply-to if specified
            if message.reply_to:
                params['ReplyToAddresses'] = message.reply_to

            # Handle attachments using Raw email if present
            if message.attachments:
                params = self._build_raw_email(message)

            # Send the email
            response = self.client.send_email(**params)

            logger.info(
                f"Email sent successfully. MessageId: {response['MessageId']}"
            )
            return True

        except ClientError as e:
            logger.error(
                f"Failed to send email: {e.response['Error']['Message']}"
            )
            if not self.fail_silently:
                raise
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            if not self.fail_silently:
                raise
            return False

    def _build_raw_email(self, message):
        """
        Build raw email format for messages with attachments.
        """
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders

        # Create message container
        msg = MIMEMultipart()
        msg['Subject'] = message.subject
        msg['From'] = message.from_email
        msg['To'] = ', '.join(message.to)

        if message.cc:
            msg['Cc'] = ', '.join(message.cc)

        if message.reply_to:
            msg['Reply-To'] = ', '.join(message.reply_to)

        # Add body
        if message.content_subtype == 'html':
            msg.attach(MIMEText(message.body, 'html'))
        else:
            msg.attach(MIMEText(message.body, 'plain'))

        # Add HTML alternative if present
        if hasattr(message, 'alternatives') and message.alternatives:
            for alt_content, alt_type in message.alternatives:
                if alt_type == 'text/html':
                    msg.attach(MIMEText(alt_content, 'html'))

        # Add attachments
        for attachment in message.attachments:
            if isinstance(attachment, MIMEBase):
                msg.attach(attachment)
            else:
                filename, content, mimetype = attachment
                part = MIMEBase(*mimetype.split('/'))
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{filename}"'
                )
                msg.attach(part)

        # Build destination
        destination = {'ToAddresses': message.to}
        if message.cc:
            destination['CcAddresses'] = message.cc
        if message.bcc:
            destination['BccAddresses'] = message.bcc

        # Build params for raw email
        params = {
            'Content': {
                'Raw': {
                    'Data': msg.as_bytes()
                }
            },
            'Destination': destination,
        }

        if self.configuration_set:
            params['ConfigurationSetName'] = self.configuration_set

        return params
