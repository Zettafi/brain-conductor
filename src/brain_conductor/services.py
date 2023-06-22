"""Services"""
import abc

import aiobotocore.client
from pydantic import EmailStr


class DeliveryError(Exception):
    """Error raised when email messages cannot be delivered"""

    pass


class EmailService(abc.ABC):
    """Email Service"""

    @abc.abstractmethod
    async def send_email(
        self,
        sender: EmailStr,
        recipients: list[EmailStr],
        subject: str,
        body_text: str,
        body_html: str,
    ) -> None:
        """
        Send an email
        :param sender: Address of the email sender
        :param recipients: Addresses of the email recipients
        :param subject: Subject of the email
        :param body_text: Body of the email message in plain text
        :param body_html: Body of the email message in HTML
        """
        raise NotImplementedError


class AWSSESEmailService(EmailService):
    """AWS SES-based email service implementation"""

    def __init__(
        self, client: "aiobotocore.client.SES"  # type: ignore[name-defined]
    ) -> None:
        self.client = client

    async def send_email(
        self,
        sender: EmailStr,
        recipients: list[EmailStr],
        subject: str,
        body_text: str,
        body_html: str,
    ) -> None:
        try:
            await self.client.send_email(
                Source=sender,
                Destination={"ToAddresses": recipients},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {
                        "Html": {"Data": body_html},
                        "Text": {"Data": body_text},
                    },
                },
            )
        except Exception as e:
            raise DeliveryError(e)
