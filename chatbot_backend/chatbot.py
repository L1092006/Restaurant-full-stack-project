from dotenv import load_dotenv, find_dotenv
import os
from typing import Literal
import uuid
from datetime import datetime, timezone, timedelta
import json
import sqlite3
import asyncio
from langchain_openrouter import ChatOpenRouter
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, RemoveMessage
from langchain.tools import tool
from langgraph.graph import MessagesState, START, END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel, Field
import aiosqlite
from pinecone import Pinecone
from prompts import system_prompts


# The state schema of the graph
class State(MessagesState):
    # Complete system_prompts of all the agents
    system_prompts: dict
    # Chunks of related memories. There are 2 types: memories about the past conversations and about the web. In each list, The most important ones are first.
    conversation_memories: list
    web_info: list

    # Summary of the conversation history older than current provided message messages
    summary: str
    # Latest user message to highlight in case the bot calls too many tools to flood it
    latest_user_message: str

class Chatbot:
    # Info about web backend
    backend: dict
    # Info about web client
    client: dict
    # All messages in the current run
    all_messages: dict
    # DEBUG=True allow the graph to print logs
    DEBUG: bool

    # Check if a tool is currently running
    tool_run: bool

    # chat model
    chat = None
    
    # The checkpoint db name
    checkpoint_db: str
    # The compiled graph
    compiled_graph = None
    # The uncompiled graph
    graph = None

    def __init__(self, connection, cloud=True, backend=None, client=None, checkpoint_db="assistant.db", DEBUG=False):
        """
        connection is the websocket connection with the current client
        cloud=True will use cloud model like openai
        checkpoint_db: the name of the sqlite db used for storing graph checkpoint
        """
        # Instance variables for the server to update
        # Info the backend web API
        # {
        #     "supported_urls": "list of urls and their descriptions for the chatbot can call",
        #     "additional_info": "info that we want to give to chatbot"
        # }
        if not backend:
            self.backend = {
                "supported_urls": [],
                "additional_info": "None"
            }
        else:
            self.backend = backend

        # Info about the client
        # {
        #     "user_id": "The user id from web backend",
        #     "username": "",
        #     "user_profile": "Most important info about the current user",
        #     "last_conversation": "Summary about the last conversation with the user when they visit the web",
        #     "web_state":  "Info about the current page displayed in the user browser. Updated by the client each time it sends a request. Check the newest by calling a tool"
        # }
        # Default to anonymous user and on the main page
        if not client:
            self.client = {
                "user_id": f"anonymous-{uuid.uuid4()}",
                "username": "Anonymous User",
                "user_profile": "An anonymous user who hasn't logged in",
                "last_conversation": "Unknown",
                "web_state":  {
                    "web_name": "The V",
                    "current_url": "/"
                },
                "paths_schema": {}
            }
        else:
            self.client = client

        # A list of all messages in the current connection
        self.all_messages = []
        self.DEBUG = DEBUG
        self.checkpoint_db = checkpoint_db


        # Get env
        load_dotenv(find_dotenv(), override=True)
        
        # Cloud model name
        cloud_model = os.getenv('OPENROUTER_MODEL')
        # Create chat models
        if cloud:
            self.chat = ChatOpenRouter(model=cloud_model, temperature=0.2, top_p=0.2,
                            reasoning={'effort': 'none'}
            )
        else: 
            self.chat = ChatOllama(model='hf.co/unsloth/gemma-4-26B-A4B-it-qat-GGUF:UD-Q4_K_XL', temperature=0.2, top_p=0.2, reasoning=False)
        

        # Set up pinecone connection
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        index_name = os.getenv('INDEX_NAME')
        pc = Pinecone(api_key=pinecone_api_key)
        # If the index name hasn't exist, create it
        if not pc.has_index(index_name):
            pc.create_index_for_model(
                name=index_name,
                cloud='aws',
                region='us-east-1',
                embed={
                    "model":"llama-text-embed-v2",
                    "field_map":{"text": "chunk_text"}
                }
            )
        index = pc.Index(index_name)

        # The limit of the input to the mmodel
        limit = (int(''.join(os.getenv('MODEL_CONTEXT').split(',')))/2) / 8
        # The maximum length (words) of each memory unit stored in pinecone
        memory_length = int(os.getenv('MEMORY_LENGTH'))
        # The maximum length (words) of the current summary stored in the graph
        summary_length = 500
        # The maximum number of interactions in the history
        history_length = 30


        # Define tools and chatbot with tools
        self.tool_run = False
        # Helper function: take a dict message and send to the client after tool_run is False, set tool_run to True
        async def send(message_dict):
             # wait
            while self.tool_run:
                await asyncio.sleep(0.1)
            self.tool_run = True
            message_str = json.dumps(message_dict)
            await connection.send(message_str)  

        # Helper function: wait for a message from client which contains the tool_result and return it. Set tool_run to False
        async def recv():
            # Wait for the client to return the result
            result_str = await connection.recv()
            self.tool_run = False
            result_dict = json.loads(result_str)
            content = result_dict["content"]
            return {
                "status": content["status"],
                "result": content["result"]
            }
        # FIXME: update the tools
        # Send message to the client 
        @tool
        async def send_message(message: str):
            """Send the message to the user. Just give your message as a string which contains only the content of your message. Do not put extra things"""
            print(message)

            await send({
                "type": "chat_message",
                "content": message
            })
            self.tool_run = False
            return {
                "status": "success",
                "result": "Sent."
            }

        # An empty function which is used by the chatbot to signify the end of the graph
        @tool
        def terminate():
            """End the current invocation after handling the user query. Do not call this with other tools in one message since it will stop you immediately and not execute other tools."""
            return {
                "status": "fail",
                "result": "If you receive this, it means you called this tool along with other tools in 1 message. This is forbidden. Call only terminate tool in your next message."
            }

        @tool
        async def get_items():
            """Get all items for sale on this web. The result is a json containing all items.
            """
            await send({
                "type": "tool_call",
                "content": {
                    "tool_name": "get_items",
                    "arguments": {}
                }
            })

            return await recv()
        
        @tool(description=f"""
            Navigate the web for the user in their browser to a specific path. Typically used when the user ask to show them somthing.
            INPUT: 
                path: a string which is the path to navigate to. DO NOT INCLUDE THE DOMAIN OF THE WEB. ONLY INCLUDE ONE PATH LIKE /, /cart,...
            
            ALL THE AVAILABLE PATHS IN THE FRONTEND WEB:
                {client['paths_schema']}
            path must be one of the above paths.
            
            """)
        async def navigate(path: str):
            await send({
                "type": "tool_call",
                "content": {
                    "tool_name": "navigate",
                    "arguments": {
                        "path": path
                    }
                }
            })

            return await recv()
        
        @tool
        async def add_item(items: list[dict]):
            """
            Add or remove num items with the id item_id to the user cart
            INPUT: a list of json objects each has the below schema
            {
                "id": the id of the item to add. THIS IS THE ID OF A MENU ITEM ON THE WEB, NOT THE ID OF THINGS LIKE CARTITEMS, ORDERITEMS,... IT'S THE ID OF ITEMS RETURNED WHEN CALLING GET_ITEMS TOOL
            }
            USE THE EXACT KEY IN EACH OBJECT
            num can be negative in which case num items will be removed from the cart.
            """

            await send({
                "type": "tool_call",
                "content": {
                    "tool_name": "add_item",
                    "arguments": {
                        "items": items
                    }
                }
            })

            return await recv()
        
        @tool
        async def get_cartitems():
            """
            Get all the items in the current cart of the user
            """
            await send({
                "type": "tool_call",
                "content": {
                    "tool_name": "get_cartitems",
                    "arguments": {}
                }
            })

            return await recv()
        
        @tool
        async def get_orders():
            """
            Get all orders of the user
            """
            await send({
                "type": "tool_call",
                "content": {
                    "tool_name": "get_orders",
                    "arguments": {}
                }
            })

            return await recv()


        
        tools = [send_message, terminate, navigate, get_items, add_item, get_cartitems, get_orders]
        string_parser = StrOutputParser()
        chat_with_tools = self.chat.bind_tools(tools)
        summary_agent = self.chat | string_parser
        

        # Helper function for the graph
        # Fetch related memories from pinecone
        def fetch_memory(query, namespace, top_k=int(limit / 2 / 4 / memory_length)) -> list:
            # FIXME adjust top_k 
            # top_k = 10
            results = index.search_records(
                namespace=namespace,
                query={
                    'inputs': {
                        'text': query
                    },
                    'top_k': top_k
                },
                fields=['chunk_text']
            )
            memories = [m['fields'] for m in results['result']['hits']]
            return memories


        # # Merge new memories with memories in the state
        # def update_memories(state: State, memories):
        #     return memories + state['memories'][(-1)*len(memories):]

        # Log a string
        def log(log):
            print(log)

        # DEFINE NODES OF THE GRAPH

        # Initialization node
        # Fetch data to make a complete system_prompt, add a status message to messages, remove all the tool result of the previous calls
        def init_node(state: State) -> dict:
            base_system_prompt = system_prompts["chatbot"]

            # The new state to return
            new_state = {}

            # If summary and latest_user_message don't exist yet, add empty values
            if "summary" not in state:
                new_state["summary"] = ""
            if "latest_user_message" not in state:
                new_state["latest_user_message"] = ""

            # Get memories
            conversation_memories = fetch_memory(state["latest_user_message"], self.client["username"])
            conversation_memories_str = '\n'.join([m.get('chunk_text', '') for m in conversation_memories]) if conversation_memories else ""
            web_info = fetch_memory(state["latest_user_message"], self.client["web_state"]["web_name"])
            web_info_str = '\n'.join([m.get('chunk_text', '') for m in web_info]) if web_info else ""

            chatbot_system_prompt = f"""
        {base_system_prompt}
        INPUT:
        USERNAME: {self.client["username"]}
        USERPROFILE: 
        {self.client["user_profile"]}
        CLIENT CURRENT URL: {self.client["web_state"]["current_url"]}
        CONVERSATION MEMORIES: 
        {conversation_memories_str}
        RELATED WEB INFO:
        {web_info_str}
        ADDITIONAL INFO:
        {self.backend["additional_info"]}
        LAST CONVERSATION:
        {self.client["last_conversation"]}
        SUMMARY:
        {state.get("summary", "")}
        LATEST USER MESSSAGE:
        {state.get("latest_user_message", "")}
        MESSAGES: will be given later
            """.strip()

            # The complete system prompt of summary agent
            sum_system_prompt = system_prompts["summary_agent"] + f"""
        RULES:
        - The length limit of the summary is {summary_length}

        INPUT:
        USERNAME: {self.client["username"]}
        USERPROFILE: 
        {self.client["user_profile"]}
        CONVERSATION MEMORIES: 
        {conversation_memories_str}
        LAST CONVERSATION:
        {self.client["last_conversation"]}
        SUMMARY: will be given later
        LATEST USER MESSSAGE:
        {state.get("latest_user_message", "")}
        MESSAGES: will be given later
        """.strip()

            system_prompt = {
                "chatbot": chatbot_system_prompt,
                "summary_agent": sum_system_prompt
            }

            status_message = HumanMessage(f"This is just a status message made and injected by the system, not by the user. Now is {datetime.now().isoformat()}. You have been invoked again to address a user query.")
            # Remove all the tool results of the previous invocation
            new_messages = [status_message] + [RemoveMessage(id=message.id) for message in state["messages"] if message.type == "tool"]
            new_state = {**new_state, "system_prompts": system_prompt, "conversation_memories": conversation_memories, "web_info": web_info, "messages": new_messages}
            
            if DEBUG:
                log(f"init_node\n{new_state}\n\n")
            
            return new_state

        # Node to call the chatbot
        def reasoning(state: State) -> State:
            if DEBUG:
                log(f"reasoning\nstate['messages']: {state['messages']}\n\n")
            ai_message = chat_with_tools.invoke([SystemMessage(state['system_prompts']['chatbot'])] + state["messages"])
            new_state = {"messages": [ai_message]}
            if DEBUG:
                log(f"Response: {new_state}\n\n")
            return new_state
        
        # If the history is long enough, summarize and add its first half to the summary and cut the excess first part of summary.
        def summarize(state: State) -> dict:
            # Do nothing if the history is still less than limit
            if len(state['messages']) <= history_length:
                return {}

            # Create interaction and emotions history str
            interation_history = []
            # Get only the first history_length interations
            for i,m in enumerate(state['messages'][:int((-1)*history_length/2)]):
                interation_history.append(f"{m.type}: {m.content}")

            interation_history = '\n'.join(interation_history)

            # message for adding to the current summary
            system_message = SystemMessage(state["system_prompts"]["summary_agent"])

            chat_message = HumanMessage(f"""\
        RULES: THE NEW SUMMARY MUST CONTAINS LESS THAN {summary_length} words
        SUMMARY: 
        {state["summary"]}
        MESSAGES:
        {interation_history}
        """.strip())

            new_summary = summary_agent.invoke([system_message, chat_message])
            # only get the last summary_length words
            new_summary = " ".join(new_summary.split())

            # # Get the remaining part of summary
            # remain_summary = ' '.join(state['summary'].split()[int((-1)*summary_length//2):])

            # The id to split messages
            split_id = int((-1)*history_length/2)
            
            # Create remove messages for the first few mMessagesState
            remove_messages = [RemoveMessage(id=m.id) for m in state['messages'][:split_id+1]]
            for m in state['messages'][:split_id+1]:
                self.all_messages.append(m)

            new_state = {'summary': new_summary, "messages": remove_messages}
            if DEBUG:
                log(f"summarize\n{new_state}\n\n")
            return new_state
        
        # If the function output normally. They are thinking and thus go here. This replace the last AI message with a new one with "Thought: " add before
        def think(state: State) -> dict:
            # # Remove the last message 
            # remove_message = RemoveMessage(id=state["messages"][-1].id)

            # # Add a new AI message
            # ai_message = AIMessage(f"ai think: {state["messages"][-1].content}")

            # new_state = {"messages": [remove_message, ai_message]}

            # new_state = {"messages": [HumanMessage("This is not sent by the user you're chatting with. This is injected by the server system to remind you that your previous response is your reasoning. Now you can call a tool or keep reasoning. DO NOT REPLY TO THIS.")]}
            new_state = {}

            # If the previous message is an assistant message, ask the chatbot to call a tool
            if state["messages"][-1].type == "ai":
                new_state = {"messages": [HumanMessage("This is a message injected by the server system, not by the user. Your previous message is your reasoning. Upon see this message, call a tool to continue your work or send a message to the user. DO NOT OUTPUT AN AI (ASSISTANT) MESSAGE AGAIN. YOU MUST CALL A TOOL NOW.")]}
            if DEBUG:
                log(f"think\n{new_state}\n\n")
            return new_state

        # Shutdown process: add the current messages to all_messages for summarization outside the graph
        def shutdown(state: State) -> dict:
            for m in state['messages']:
                self.all_messages.append(m)

            new_state = {}
            if DEBUG:
                log(f"shutdown\n{new_state}\n\n")
            return new_state

        # Create graph and add nodes
        graph = StateGraph(State)
        graph.add_node(init_node)
        graph.add_node(reasoning)
        graph.add_node(summarize)
        graph.add_node("tools", ToolNode(tools=tools))
        graph.add_node(think)
        graph.add_node(shutdown)
        # Define conditions for routing
        def routing_function(state: State) -> Literal[r"tools", r"think", r"shutdown"]:
            last_message = state["messages"][-1]

            # if the last message has tool calls
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                # If a tool called is terminate
                if "terminate" in [c["name"] for c in last_message.tool_calls] and len(last_message.tool_calls) == 1:
                    return "shutdown"
                else:
                    return "tools"
            else:
                return "think"
            
        # Add edges
        graph.add_edge(START, 'init_node')
        graph.add_edge('init_node', 'reasoning')
        graph.add_edge('reasoning', 'summarize')
        graph.add_conditional_edges(source="summarize", path=routing_function)
        graph.add_edge("think", "reasoning")
        graph.add_edge("tools", "reasoning")
        graph.add_edge('shutdown', END)

        self.graph = graph

    # Compile the graph
    async def compile(self):
        # Connect to db and create checkpointer
        db = await aiosqlite.connect(self.checkpoint_db, check_same_thread=False)
        checkpointer = AsyncSqliteSaver(db)

        # Compile the graph with checkpointer
        self.compiled_graph = self.graph.compile(checkpointer)

        # Invoke the graph with the new user message
    async def ainvoke(self, new_message):
        # Use user_id from web backend as thread_id
        config = {'configurable': {'thread_id': f"{self.client['user_id']}"}}
        await self.compiled_graph.ainvoke({"messages": [HumanMessage(new_message)], "latest_user_message": new_message}, config=config)


    # Get the updated user profile, last conversation summary and all messages for storage
    def get_summary_and_messages(self):
        # Conversation string
        con = [f"{m.type}: {m.content}" for m in self.all_messages]
        con = "\n".join(con)

        class Summary(BaseModel):
            summary: str = Field(description="The summary of the conversation")
            user_profile: str = Field(description="The updated user profile")
        chat_with_schema = self.chat.with_structured_output(Summary)
        res = chat_with_schema.invoke(f"""
        Below is a conversation between a chatbot assistant for a e-commerce web and a user: 
        {con}
        Below is the user profile which summarize the main points about the user:
        {self.client["user_profile"]}
        Generate a summary about this conversation and a new updated version of the user profile based on the new conversation.
        """)

        return {
            "user_id": self.client["user_id"],
            "summary": res.summary,
            "user_profile": res.user_profile,
            "messages": [m.content for m in self.all_messages if m.type == "human"]
        }
        
        


    