from unittest.mock import patch

from app.models import Inquiry


def test_submit_general_inquiry_persists_and_notifies(client, app):
    with patch("app.blueprints.public.views.send_inquiry_notification") as mock_notify:
        r = client.post(
            "/crows-nest/submit",
            data={
                "kind": "general",
                "from_name": "Cap'n Salt",
                "email": "salt@y.test",
                "message": "Hello",
            },
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"thank" in r.data.lower() or b"hoist" in r.data.lower()
        mock_notify.assert_called_once()

    with app.app_context():
        inq = Inquiry.query.first()
        assert inq is not None
        assert inq.from_name == "Cap'n Salt"
        assert inq.kind == "general"


def test_submit_booking_inquiry_keeps_booking_fields(client, app):
    with patch("app.blueprints.public.views.send_inquiry_notification"):
        r = client.post(
            "/crows-nest/submit",
            data={
                "kind": "booking",
                "from_name": "Promoter",
                "email": "p@y",
                "phone": "555-1212",
                "event_date": "2027-10-15",
                "venue": "The Tavern",
                "city": "Boston",
                "message": "Renfest dates?",
            },
            follow_redirects=True,
        )
        assert r.status_code == 200

    with app.app_context():
        inq = Inquiry.query.filter_by(kind="booking").one()
        assert inq.venue == "The Tavern"
        assert inq.city == "Boston"
        assert str(inq.event_date) == "2027-10-15"


def test_submit_missing_required_fields_400(client, app):
    r = client.post("/crows-nest/submit", data={"kind": "general"})
    assert r.status_code in (400, 422)
