import unittest
from unittest.mock import AsyncMock

from pydantic import EmailStr

from brain_conductor import AWSSESEmailService, DeliveryError


class AWSSESEmailServiceTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._client = AsyncMock()
        self._service = AWSSESEmailService(self._client)

    async def test_send_email_sends_email(self):
        await self._service.send_email(
            EmailStr("sender"), [EmailStr("recipient")], "subject", "text", "html"
        )
        self._client.send_email.assert_awaited_once_with(
            Source="sender",
            Destination={"ToAddresses": ["recipient"]},
            Message={
                "Subject": {"Data": "subject"},
                "Body": {
                    "Html": {"Data": "html"},
                    "Text": {"Data": "text"},
                },
            },
        )

    async def test_send_email_exception_is_delivery_error(self):
        self._client.send_email.side_effect = Exception
        with self.assertRaises(DeliveryError):
            await self._service.send_email(
                EmailStr("sender"), [EmailStr("recipient")], "subject", "text", "html"
            )


if __name__ == "__main__":
    unittest.main()
