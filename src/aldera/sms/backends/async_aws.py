"""
Defines an SMS backend that sends messages asynchronously.

Copyright (c) 2025 Zachary Young.
All rights reserved.
"""

from __future__ import annotations

import asyncio
import os

import aioboto3
import botocore

from aldera.config import get as get_config


class SmsSendError(Exception):
    """Raised when an SMS cannot be sent after retries."""


class AsyncSmsBackend:
    """
    Async backend that publishes SMS messages via AWS SNS using aioboto3.

    Methods are 'async def' and intended for use in async contexts.
    """

    def __init__(self):
        """
        Initialize important values.
        """
        self._max_retries = 3
        self._backoff_base = 0.5
        self._backoff_factor = 2.0
        self._semaphore = asyncio.Semaphore(2)

    def _get_region(self) -> str:
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

    async def _create_sns_client(self):
        """
        Create an aioboto3 SNS client using a session.

        Caller must be async.
        """
        session = aioboto3.Session()
        # Use context manager to ensure client cleanup
        client = await session.client(
            'sns',
            region_name=self._get_region()
        ).__aenter__()
        return client, session

    async def send_message(self, message, recipient_number):
        """
        Send an SMS message asynchronously.
        """
        attempt = 0
        last_exception = None
        # Acquire semaphore to limit concurrent publishes
        async with self._semaphore:
            while attempt <= self._max_retries:
                try:
                    # create client and ensure we close it
                    session = aioboto3.Session()
                    async with session.client(
                        'sns',
                        region_name=self._get_region()
                    ) as client:
                        publish_kwargs = {
                            'PhoneNumber': recipient_number,
                            'Message': message,
                        }
                        response = await client.publish(**publish_kwargs)
                        # Success: response typically contains 'MessageId'
                        message_id = response.get('MessageId')
                        return message_id
                except botocore.exceptions.ClientError as err:
                    # These are AWS-reported errors (4xx/5xx)
                    # Determine if transient: throttling, service
                    # unavailable, 5xx, etc.
                    code = getattr(
                        err,
                        'response',
                        {}
                    ).get(
                        'Error',
                        {}
                    ).get('Code', '')
                    # Common retriable codes: Throttling,
                    # RequestLimitExceeded, InternalError
                    retriable = any(
                        token in str(code).lower()
                        for token in (
                            'throttling',
                            'requestlimit',
                            'internal',
                            'service',
                            'unavailable'
                        )
                    )
                    last_exception = err
                    attempt += 1
                    if attempt > self._max_retries or not retriable:
                        break
                    await asyncio.sleep(
                        self._backoff_base
                        * (self._backoff_factor ** (attempt - 1))
                    )
                    continue
                except (
                    botocore.exceptions.EndpointConnectionError,
                    asyncio.TimeoutError
                ) as exc:
                    # Network or endpoint issues — retry
                    last_exception = exc
                    attempt += 1
                    if attempt > self._max_retries:
                        break
                    await asyncio.sleep(
                        self._backoff_base
                        * (self._backoff_factor ** (attempt - 1))
                    )
                    continue
                except Exception as exc:
                    # Unknown error; do not retry
                    last_exception = exc
                    break
        # If we got here, all retries exhausted or non-retriable failure
        raise SmsSendError(
            f'Failed to send message to {recipient_number}'
        ) from last_exception

    def send_message_sync(self, message, recipient_number):
        """
        Run the async send_message from synchronous code.
        """
        return asyncio.run(
            self.send_message(message, recipient_number)
        )
