import asyncio
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosedOK
import json
import uuid
from pathlib import Path
import sqlite3
from chatbot import Chatbot

DEBUG = True
db_name = "users.db"

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
        
    chatbot = None
    # Start the main loop
    try:
         # SET UP
        # Ask the client about web state by receive an status_update message. Close the connection if the client doesn't send a status update upon connection
        data = await recv()
        if data["type"] != types[0]:
            await websocket.close(code=1008, reason=f"Make sure the first message upon connection is a {types[0]}")
            return
        # Info about the client
        client = data["content"]

        # Helper: get the user_profile and last_conversation from user id from web backend
        def get_userinfo(user_id):
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            res = cursor.execute("""SELECT "id", "user_profile", "last_conversation" FROM "users" WHERE "backend_id" = ?;""", (user_id,))
            res_tup = res.fetchall()
            # If there's no user like that, insert a new user:
            if len(res_tup) == 0:
                cursor.executemany('INSERT INTO users ("backend_id", "user_profile", "last_conversation") VALUES(?, ?, ?)', [(user_id, "First time user", "None")])
                res_tup = [(None, "First time user", "None")]
                conn.commit()
            cursor.close()
            return {
                "id": res_tup[0][0],
                "user_profile": res_tup[0][1],
                "last_conversation": res_tup[0][2]
            }
        # Add user_profile and last_conversation from the chatbot_db
        # If the user hasn't logged in, add some extra info
        if not client["user_id"]:
            client["user_id"] = f"anonymous-{uuid.uuid4()}"
            client["username"] = "Anonymous User"
            client["user_profile"] = "An anonymous user who hasn't logged in"
            client["last_conversation"] = "Unknown"
        else:
            data = get_userinfo(client["user_id"])
            client["user_profile"] = data["user_profile"]
            client["last_conversation"] = data["last_conversation"]

        # Get the backend info
        # FIXME: send the request to backend to get info
        backend = {
            "supported_urls": [],
            "additional_info": "None"
        }
    
        chatbot = Chatbot(websocket, cloud=True, backend=backend, client=client, DEBUG=DEBUG)
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
                if "user_id" in content:
                    data = get_userinfo(content["user_id"])
                    chatbot.client["user_profile"] = data["user_profile"]
                    chatbot.client["last_conversation"] = data["last_conversation"]
            else:
                print(f"Receive {message['type']} unexpectedly")
    except ConnectionClosedOK as e:
        return
    except Exception as e:
        print("close2", e)
        # await websocket.close(code=1011, reason=f"Server error. Server raised exception {e}")
        raise Exception(f"Server error. Server raised exception {e}")
    # Update the user info
    finally:
        if chatbot:
            data = chatbot.get_summary_and_messages()
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            # Update the profile and last conversation
            cursor.execute("""
            UPDATE "users"
            SET "user_profile" = ?, "last_conversation" = ?
            WHERE "backend_id" = ?
            """, (data["user_profile"], data["summary"], data["user_id"],))

            # Insert the new messages
            userinfo = get_userinfo(data["user_id"])
            new_messages = [(userinfo["id"], m) for m in data["messages"]]
            cursor.executemany('INSERT INTO user_messages("user_id", "content") VALUES(?, ?)', new_messages)
            conn.commit()
            conn.close()

async def main():

    # Init the db if not exist
    if not Path("users.db").exists():
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                "id" INTEGER PRIMARY KEY,
                "backend_id" TEXT NOT NULL UNIQUE,
                "user_profile" TEXT,
                "last_conversation"
            );
        """)
        cursor.execute("""
            CREATE TABLE user_messages (
                "id" INTEGER PRIMARY KEY,
                "user_id" INTEGER,
                "content" TEXT,
                FOREIGN KEY("user_id") REFERENCES "users"("id")
            );""")
        conn.commit()
        conn.close()
    async with serve(handler, "", 8001) as server:
        await server.serve_forever()
    

if __name__ == "__main__":
    asyncio.run(main())