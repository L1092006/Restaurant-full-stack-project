import asyncio
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosedOK
import json
import uuid
from chatbot import Chatbot

DEBUG = True

"""
A MESSAGE SENT BY THE CLIENT IS A JSON STRING WITH THE SCHEMA:
{
    "type": "status_update | chat_message | tool_result",
    "content": "The content corresponding to each type"
}

For type status_update, the content value is a dict that can have any of the below key-value pairs:
{
    "user_id": "",
    "username": "",
    "web_state": {
        "web_name": "",
        "current_url": "",
    },
    paths_schema: a json describing all the paths available in the frontend
}

For type chat_message, the content value is:
{
    "message": "str",
    "web_state": "like above"
}

For type tool_result, the content value is:
{
    "status": "success | fail,
    "result": "the result of a previous tool call",
    "web_state": "like above",
}


A MESSAGE SENT BY THIS SEVER IS A JSON STRING WITH THE SCHEMA:
{
    "type": "chat_message | tool_call",
    "content": "The content corresponding to each type"

For chat_message, content is a string
For tool_call, content is:
{
    "tool_name": "Name of the tool",
    "arguments": "a json containing arguments"
}
"""



types = ["status_update", "chat_message", "tool_result"]

async def handler(websocket):
    # Helper functions
    # Receive the message from the client and transform it into a dict
    async def recv():
        message = await websocket.recv()
        print(message)

        try:
            data = json.loads(message)
            # Check if the message is in correct format by access all the keys
            message_type = data["type"]
            content = data["content"]
            if data["type"] == types[0]:
                user_id = content["user_id"]
                username = content["username"]
            elif data["type"] == types[1]:
                content_message = content["message"]
            
            # web_state is in all types of messages
            web_state = content["web_state"]
            web_name = web_state["web_name"]
            current_url = web_state["current_url"]
            print("Here")
            return data
            
        except Exception as e:
            print("Close", e)
            await websocket.close(code=1008, reason=f"Incorrect message format. Server raised exception {e}")
            raise e
        
    # SET UP
    # Ask the client about web state by receive an status_update message. Close the connection if the client doesn't send a status update upon connection
    data = await recv()
    if data["type"] != types[0]:
        await websocket.close(code=1008, reason=f"Make sure the first message upon connection is a {types[0]}")
        return
    # Info about the client
    client = data["content"]
    # Add user_profile and last_conversation from the chatbot_db
    # If the user hasn't logged in, add some extra info
    if not client["user_id"]:
        client["user_id"] = f"anonymous-{uuid.uuid4()}"
        client["username"] = "Anonymous User"
        client["user_profile"] = "An anonymous user who hasn't logged in"
        client["last_conversation"] = "Unknown"
    # FIXME: use user_profile and last_conversation from the chatbot_db
    else:
        client["user_profile"] = "No info. First time customer"
        client["last_conversation"] = "None"

    # Get the backend info
    # FIXME: send the request to backend to get info
    backend = {
        "supported_urls": [],
        "additional_info": "None"
    }
    
    # Start the main loop
    try:
        chatbot = Chatbot(websocket, cloud=False, backend=backend, client=client, DEBUG=DEBUG)
        await chatbot.compile()
        while True:
            message = await recv()
            print("here2")
            
            content = message["content"]
            # Always update web_state
            chatbot.client["web_state"] = content["web_state"]
            print(types)
            # Handle chat message
            if message["type"] == types[1]:
                await chatbot.ainvoke(content["message"])
            # Handle status update by update user info
            elif message["type"] == types[0]:
                # Only update the values present in the content
                chatbot.client = {**chatbot.client, **content}
                # If the user is updated, update all the user info
                # FIXME: use user_profile and last_conversation from the chatbot_db
                if "user" in content:
                    chatbot.client["user_profile"] = "No info. First time customer"
                    chatbot.client["last_conversation"] = "None"
            else:
                print(f"Receive {message['type']} unexpectedly")
    except ConnectionClosedOK as e:
        return
    except Exception as e:
        print("close2", e)
        # await websocket.close(code=1011, reason=f"Server error. Server raised exception {e}")
        raise Exception(f"Server error. Server raised exception {e}")

async def main():
    async with serve(handler, "", 8001) as server:
        await server.serve_forever()
    

if __name__ == "__main__":
    asyncio.run(main())