import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services.notification_service import notify_quality_control


class TestNotificationService(unittest.TestCase):
    def test_direct_feedback_report_contains_feedback_only(self):
        customer = SimpleNamespace(
            full_name="Yusuf Mohammed",
            hotel=SimpleNamespace(name="Ymc"),
        )
        sender = AsyncMock()

        with patch("services.notification_service._extract_chat_ids", return_value=["test"]), \
             patch("services.notification_service._send", sender):
            asyncio.run(
                notify_quality_control(
                    None,
                    None,
                    feedback="thanks",
                    customer=customer,
                )
            )

        report = sender.await_args.args[2]
        self.assertIn("Customer Feedback Report", report)
        self.assertIn("Ymc", report)
        self.assertIn("Yusuf Mohammed", report)
        self.assertIn("thanks", report)
        self.assertNotIn("Order", report)
        self.assertNotIn("Feedback & Rating Report", report)


if __name__ == "__main__":
    unittest.main()
