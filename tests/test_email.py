from unittest.mock import MagicMock, patch

from app.models import Inquiry
from app.services.email import send_inquiry_notification


def test_send_inquiry_notification_calls_smtp(app):
    with app.app_context():
        app.config["SMTP_HOST"] = "smtp.example.test"
        app.config["SMTP_PORT"] = 587
        app.config["SMTP_USER"] = "user"
        app.config["SMTP_PASSWORD"] = "pw"
        app.config["SMTP_FROM"] = "no-reply@grogblossoms.com"
        app.config["CONTACT_EMAIL"] = "chris@grogblossoms.com"
        inq = Inquiry(kind="booking", from_name="Cap'n", email="cap@y", message="Hi")

        with patch("app.services.email.smtplib.SMTP") as mock_smtp:
            instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = instance
            send_inquiry_notification(inq)
            instance.starttls.assert_called_once()
            instance.login.assert_called_once_with("user", "pw")
            instance.send_message.assert_called_once()


def test_send_inquiry_notification_noops_without_smtp_host(app, caplog):
    with app.app_context():
        app.config["SMTP_HOST"] = ""
        inq = Inquiry(kind="general", from_name="X", email="x@y", message="hi")
        # Should not raise.
        send_inquiry_notification(inq)
