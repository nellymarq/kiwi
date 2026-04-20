"""Tier 64 — smoke tests for handlers/delivery.py."""


def test_delivery_handlers_importable():
    from handlers.delivery import (
        handle_accepted,
        handle_pdf,
        handle_pdf_last,
        handle_preferences,
        handle_rejected,
    )
    for h in (handle_pdf_last, handle_pdf, handle_accepted, handle_rejected, handle_preferences):
        assert callable(h)
