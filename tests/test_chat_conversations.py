import uuid

from backend.auth import create_conversation, create_user, delete_conversation, list_conversations, save_message


def test_create_conversation_and_message_flow():
    unique_email = f'convuser-{uuid.uuid4().hex[:8]}@example.com'
    user = create_user('Conversation User', unique_email, 'StrongPass123')
    conversation = create_conversation(user['id'], 'First thread')

    assert conversation['title'] == 'First thread'
    assert conversation['user_id'] == user['id']

    save_message(user['id'], conversation['id'], 'user', 'Hello there')
    save_message(user['id'], conversation['id'], 'assistant', 'Hi!')

    conversations = list_conversations(user['id'])
    assert any(item['id'] == conversation['id'] for item in conversations)


def test_delete_conversation_removes_thread_and_messages():
    unique_email = f'convdelete-{uuid.uuid4().hex[:8]}@example.com'
    user = create_user('Delete User', unique_email, 'StrongPass123')
    conversation = create_conversation(user['id'], 'To delete')

    save_message(user['id'], conversation['id'], 'user', 'Question')
    delete_conversation(user['id'], conversation['id'])

    assert list_conversations(user['id']) == []
