from lib.database import Conversation, Message, SessionLocal


def test_list_conversations_empty(client, auth_headers):
    response = client.get("/conversations", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


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
