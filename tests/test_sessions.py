"""Tests for session persistence."""

from memory.sessions import delete_session, list_sessions, load_session, save_session


def test_save_and_load(clean_client):
    messages = [
        {"role": "user", "content": "What about creatine timing?"},
        {"role": "assistant", "content": "Great question. Post-workout with carbs..."},
    ]
    save_session("creatine_research", messages, thread="performance", summary="creatine timing", client=clean_client)
    loaded = load_session("creatine_research", client=clean_client)
    assert loaded is not None
    assert loaded["session_id"] == "creatine_research"
    assert loaded["message_count"] == 2
    assert loaded["thread"] == "performance"
    assert "creatine" in loaded["messages"][0]["content"]


def test_load_nonexistent(clean_client):
    assert load_session("ghost_session", client=clean_client) is None


def test_list_sessions(clean_client):
    save_session("s1", [{"role": "user", "content": "q1"}], client=clean_client)
    save_session("s2", [{"role": "user", "content": "q2"}], client=clean_client)
    sessions = list_sessions(client=clean_client)
    ids = [s["session_id"] for s in sessions]
    assert "s1" in ids
    assert "s2" in ids


def test_delete_session(clean_client):
    save_session("to_delete", [{"role": "user", "content": "q"}], client=clean_client)
    assert delete_session("to_delete", client=clean_client)
    assert load_session("to_delete", client=clean_client) is None


def test_delete_nonexistent(clean_client):
    assert not delete_session("ghost", client=clean_client)


def test_session_content_truncation(clean_client):
    long_msg = [{"role": "user", "content": "x" * 10000}]
    save_session("long", long_msg, client=clean_client)
    loaded = load_session("long", client=clean_client)
    assert len(loaded["messages"][0]["content"]) <= 5000
