from lib.database import Conversation, Message, SessionLocal


def test_list_conversations_empty(client, auth_headers):
    response = client.get("/conversations", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_conversations_requires_auth(client):
    response = client.get("/conversations")
    assert response.status_code == 401


def test_list_conversations_with_data(client, auth_headers):
    db = SessionLocal()
    convo = Conversation(user_id="test@aura.local", user_role="admin", title="Listed Convo")
    db.add(convo)
    db.commit()
    db.close()

    response = client.get("/conversations", headers=auth_headers)
    assert response.status_code == 200
    titles = [c["title"] for c in response.json()]
    assert "Listed Convo" in titles


def test_get_conversation(client, auth_headers):
    # Seed a conversation directly
    db = SessionLocal()
    convo = Conversation(user_id="test@aura.local", user_role="admin", title="Test Convo")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    convo_id = convo.id
    db.close()

    response = client.get(f"/conversations/{convo_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == convo_id
    assert data["title"] == "Test Convo"
    assert data["messages"] == []


def test_get_conversation_requires_auth(client, auth_headers):
    db = SessionLocal()
    convo = Conversation(user_id="test@aura.local", user_role="admin", title="Auth Guard Convo")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    convo_id = convo.id
    db.close()

    response = client.get(f"/conversations/{convo_id}")
    assert response.status_code == 401


def test_get_conversation_other_user_404(client, auth_headers):
    """A conversation belonging to another user must return 404."""
    db = SessionLocal()
    convo = Conversation(user_id="other@aura.local", user_role="admin", title="Other User Convo")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    convo_id = convo.id
    db.close()

    response = client.get(f"/conversations/{convo_id}", headers=auth_headers)
    assert response.status_code == 404


def test_get_conversation_not_found(client, auth_headers):
    response = client.get("/conversations/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404


def test_rename_conversation_not_found(client, auth_headers):
    response = client.patch(
        "/conversations/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
        json={"title": "Ghost"},
    )
    assert response.status_code == 404


def test_rename_conversation_requires_auth(client, auth_headers):
    db = SessionLocal()
    convo = Conversation(user_id="test@aura.local", user_role="admin", title="No Auth Rename")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    convo_id = convo.id
    db.close()

    response = client.patch(f"/conversations/{convo_id}", json={"title": "Hacked"})
    assert response.status_code == 401


def test_delete_conversation_not_found(client, auth_headers):
    response = client.delete(
        "/conversations/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_delete_conversation_requires_auth(client, auth_headers):
    db = SessionLocal()
    convo = Conversation(user_id="test@aura.local", user_role="admin", title="No Auth Delete")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    convo_id = convo.id
    db.close()

    response = client.delete(f"/conversations/{convo_id}")
    assert response.status_code == 401


def test_rename_conversation(client, auth_headers):
    db = SessionLocal()
    convo = Conversation(user_id="test@aura.local", user_role="admin", title="Old Title")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    convo_id = convo.id
    db.close()

    response = client.patch(f"/conversations/{convo_id}", headers=auth_headers, json={"title": "New Title"})
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


def test_delete_conversation(client, auth_headers):
    db = SessionLocal()
    convo = Conversation(user_id="test@aura.local", user_role="admin", title="To Delete")
    db.add(convo)
    db.commit()
    db.refresh(convo)
    convo_id = convo.id
    db.close()

    response = client.delete(f"/conversations/{convo_id}", headers=auth_headers)
    assert response.status_code == 200

    response = client.get(f"/conversations/{convo_id}", headers=auth_headers)
    assert response.status_code == 404
