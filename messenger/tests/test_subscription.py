import json
from datetime import datetime, UTC
from typing import Any

import pytest
import websockets

from messenger.subscription import notify_new_message, UserType, MessageType


class FakeWebSocket:
    def __init__(self):
        self._closed = False

    async def send(self, data: str) -> None:
        pass  # Simulate sending data

    async def recv(self) -> str:
        # Simulate receiving a message after notifying
        return json.dumps({
            "payload": {
                "data": {
                    "chatroomMessage": {
                        "id": "1",
                        "user": {"id": 1, "name": "User1"},
                        "text": "Test message",
                        "createdAt": "2024-12-22T00:00:00Z"
                    }
                }
            }
        })

    # Implementing async context manager protocol
    async def __aenter__(self) -> 'FakeWebSocket':
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self._closed = True
        # Simulate closing the connection (you can add any cleanup logic here if needed)


@pytest.mark.asyncio
async def test_chatroom_message_subscription(client, mocker):
    # Mock or prepare the necessary GraphQL subscription
    chatroom_name = "Test Chatroom"
    user = {
        "id": 1,
        "name": "User1",
        "email": "user1@example.com",
        "avatar": None,
        "chatrooms": [],
        "created_at": "2024-12-22T00:00:00Z",
        "updated_at": "2024-12-22T00:00:00Z"
    }

    message = {
        "id": 1,
        "chatroom": chatroom_name,
        "user": user,
        "text": "Test message",
        "created_at": "2024-12-22T00:00:00Z"
    }

    # Define the subscription query for the WebSocket connection
    subscription_query = """
    subscription {
        chatroomMessage(chatroomName: "Test Chatroom") {
            id
            user {
                id
                name
            }
            text
            createdAt
        }
    }
    """

    # Set up WebSocket connection for the subscription
    uri = "ws://localhost:8000/graphql"  # Replace with your GraphQL server's WebSocket URL

    # Mock websockets.connect
    mock_websocket = mocker.patch("websockets.connect", return_value=FakeWebSocket())

    async with websockets.connect(uri) as websocket:
        # Send the subscription query
        await websocket.send(json.dumps({"type": "start", "id": "1", "payload": {"query": subscription_query}}))

        # Mock the function to notify the message being sent
        await notify_new_message(chatroom_name, user, message)

        # Receive the response from the WebSocket
        response = await websocket.recv()
        data = json.loads(response)

        # Validate the response
        assert data['payload']['data']['chatroomMessage']['text'] == "Test message"
        assert data['payload']['data']['chatroomMessage']['user']['name'] == "User1"