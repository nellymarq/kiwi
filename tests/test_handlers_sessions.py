"""Tier 65 — smoke tests for handlers/sessions.py."""


def test_sessions_handlers_importable():
    from handlers.sessions import (
        handle_log,
        handle_resume_session,
        handle_save_session,
        handle_sessions,
    )
    for h in (handle_save_session, handle_resume_session, handle_sessions, handle_log):
        assert callable(h)
