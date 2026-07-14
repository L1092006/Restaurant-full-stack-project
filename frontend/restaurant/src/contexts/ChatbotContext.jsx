import { createContext, useContext, useEffect, useState, useMemo, useCallback, useRef } from "react";
import { useAuth } from "./AuthContext";
import { useCart } from "./CartContext";
import { useLocation, useNavigate, matchPath } from "react-router-dom";

const ChatbotContext = createContext();

const chatbotUrl = import.meta.env.VITE_CHATBOT_URL

const debugStr = import.meta.env.VITE_DEBUG
const DEBUG = debugStr == "true";
const web_name = "The V"
// The max number of attempts to connect to the chatbot server
const maxConnect = 10;

export default function ChatbotProvider({ children }) {
    const { callAPI, isAuthenticated, user } = useAuth();
    const { cartNumber, cartItems, addItem } = useCart();
    // Get the path info
    const location = useLocation();
    const navigate = useNavigate();

    const [ socket, setSocket ] = useState(null);
    // The number of attempts to connect to the chatbot server
    const [ connectNum, setConnectNum ] = useState(0);
    // The status of chatbot, ready = true of usable
    const  [ ready, setReady ] = useState(false);

    

    // Function to connect to the chatbot server.
    const connect = useCallback(() => {
        let num = connectNum;
        let socket = null;
        while(num < maxConnect) {
            num++;
            try {
                socket = new WebSocket(chatbotUrl);
                setSocket(socket);
                setConnectNum(num);
                return
            }
            catch (e) {
                continue;
            }
        }
        setReady(false);
        throw Error(`Error: cannot connect to chatbot backend.`);
    }, [connectNum])

    // Function to send a message with our custom format to the chatbot. Convert an object to a string to send
    const sendMessage = useCallback((message) => {
        // Check if the current socket is ready
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            setReady(false);
            return;
        }
        const message_str = JSON.stringify(message);
        socket.send(message_str);
    }, [socket])


    // All messages in this session conversation
    // Each message is an object follow openai chat message style (with role and content)
    const [ chatMessages, setChatMessages ] = useState([]);

    // Function to send a chat message with open ai format to server
    const sendChat = useCallback((openai_message) => {
        setChatMessages(l => [...l, openai_message]);
        try {
            const message = {
                type: "chat_message",
                content: {
                    message: openai_message.content,
                    web_state: {
                        web_name: web_name,
                        current_url: location.pathname
                    }
                }
            }
            sendMessage(message);
        }
        catch (e) {
            throw e;
        }
    }, [location, sendMessage])


    // Send a status update message
    const sendStatusUpdate = useCallback(() => {
        const message = {
            type: "status_update",
            content: {
                user_id: user ? user.id : null,
                username: user ? user.username : null,
                web_state: {
                    web_name: web_name,
                    current_url: location.pathname
                },
                paths_schema: {
                    "/": "The main page.",
                    "/menu": "The menu page where all menu items are displayed",
                    "/menu/:id": "The page which displays the specific infomation of an item. Notice that in the path, :id must be replaced with a valid menu item id.",
                    "/login": "The page for the user to login",
                    "/signup": "The page for the user to signup",
                    "/cart": "The page which displays all the item in the user cart and the total price",
                    "/checkout": "The page for the user to checkout all the items in their cart",
                    "/account": "The page which displays all the paths lead to various pages containing infomation about the user account",
                    "/account/orders": "The page which displays all the orders the user has in the past",
                    "/account/orders/:id": "The which displays all the item in the a user order and its status. Notice that in the path, :id must be replaced with a valid order id."
                }
            }
        }
        sendMessage(message);
    }, [sendMessage,  user, location]);

    
    

    // if the socket change, update the event handlers
    useEffect(() => {
        // Check if the current socket is ready
        if (!socket) {
            setReady(false);
            return;
        }
         // Send necessary client info upon connection
        socket.onopen = () => {
            sendStatusUpdate();
        }

        socket.onmessage = async (event) => {
            if(DEBUG) console.log(`In onmessage, event data: ${event.data}`)
            

            if (typeof event.data === "string") {
                const message = JSON.parse(event.data)
                const content = message.content;
                if(message.type === "chat_message") {
                    setChatMessages(l => [...l, {role: "assistant", content: content}]);
                }
                // Handle tool calls
                else if (message.type === "tool_call") {
                    const args = content["arguments"]
                    // Navigate tool call
                    if(content["tool_name"] === "navigate") {
                        const path = args["path"];
                        // Function to validate the path
                        const isValidRoute = (path) => {
                            // List the patterns your app supports
                            const patterns = [
                                '/',
                                '/login',
                                '/signup',
                                '/menu',
                                '/menu/:id',
                                '/cart',
                                '/checkout',
                                '/account',
                                '/account/orders',
                                '/account/orders/:id',
                            ];

                            return patterns.some(pattern => matchPath({ path: pattern, end: true }, path));
                        }

                        if (isValidRoute(path)) {
                            sendMessage({
                                "type": "tool_result",
                                "content": {
                                    "status": "success",
                                    "result": `The use web path has been navigated to ${content["arguments"]["path"]}`
                                }
                            })
                            console.log(`About to navigate to: ${path}`)
                            navigate(path);
                        }
                        else {
                            sendMessage({
                                "type": "tool_result",
                                "content": {
                                    "status": "fail",
                                    "result": `Invalid path`
                                }
                            })
                        }
                       
                    }

                    // Get menu items tool call
                    else if (content["tool_name"] == "get_items") {
                        // Helper function to get all items and categories
                        const getContent = async () => {
                            let cats = null;
                            let allItems = null;
                            try {
                                const catRes = await callAPI("/categories/");
                                const itemRes = await callAPI("/items/");

                                // If res is not ok, throw an error and return in the catch
                                if(!catRes.ok || !itemRes.ok) throw new Error('callAPI successfully but res is not ok');

                                cats = await catRes.json();
                                allItems = await itemRes.json();
                            }
                            catch (e) {
                                console.log(e.message);
                                return;
                            }

                            const response = {};
                            for(let cat of cats) {
                                response[cat.title] = [];
                            }
                            for(let item of allItems) {
                                response[item.category.title].push(item);
                            }
                            return response;
                        };

                        const response = await getContent();
                        sendMessage({
                            "type": "tool_result",
                            "content": {
                                "status": "success",
                                "result": JSON.stringify(response)
                            }
                        });

                    }
                        // Add item to cart tool call
                    else if(content["tool_name"] == "add_item") {
                        try {
                            const items = args["items"];
                            for(const item of items) {
                                await addItem(item["id"], item["num"]);
                            }
                            sendMessage({
                                "type": "tool_result",
                                "content": {
                                    "status": "success",
                                    "result": "Item(s) added."
                                }
                            });
                        }
                        catch (e) {
                            sendMessage({
                                "type": "tool_result",
                                "content": {
                                    "status": "fail",
                                    "result": e
                                }
                            });
                            throw e;
                        }
                    }
                    // Get cartitems tool call
                    else if(content["tool_name"] == "get_cartitems") {
                        // Get the total price of all items
                        let total_price = 0;
                        let total_price_after_tax = 0;
                        for(const item of cartItems) {
                            total_price += item.total_price;
                            total_price_after_tax += item.total_price_after_tax;
                        }
                        sendMessage({
                            "type": "tool_result",
                            "content": {
                                "status": "success",
                                "result": {
                                    "items": cartItems,
                                    "total_price": total_price,
                                    "total_price_after_tax": total_price_after_tax
                                }
                            }
                        });
                    }
                    // Get orders tool call
                    else if(content["tool_name"] == "get_orders") {
                        // Function to get all user orders
                        const getOrders = async () => {
                            try {
                                const res = await callAPI(
                                    `/orders/`, {auth: true}
                                );
                                if(!res.ok) throw new Error(`callAPI successfully but res code is ${res.status}`);

                                const body = await res.json();
                                body.reverse();

                                for (let i = 0; i < body.length; i++) {
                                    body[i].datetime = body[i].datetime.split("T")[0];
                                }
                                return body;

                            }
                            catch (e) {
                                console.log(e.message);
                            }
                        }
                        sendMessage({
                            "type": "tool_result",
                            "content": {
                                "status": "success",
                                "result": {
                                    "items": await getOrders(),
                                }
                            }
                        });
                    }

                }
                
                else throw TypeError(`In onmessage, unexpected message.type ${message.type}`)
            }
            else {
                console.log(`Error: In onmessage, event.data is ${typeof event.data}`);
                throw TypeError(`Error: In onmessage, event.data is of type ${typeof event.data}`);
            }
            
            
        }

        socket.onerror = (error) => {
            throw Error(`Websocket error: ${error}`)
        }

        // Try to reconnect if the server close and the numbers of tries is less than maxConnect
        socket.onclose = () => {
            if (connectNum <= maxConnect) connect();
            else setReady(false);
        }

        setReady(true);
    }, [socket, user, location, sendMessage, connect, sendStatusUpdate, cartItems, addItem]) ;

    // When the user is changed, send a status update
    useEffect(() => {sendStatusUpdate()}, [user])

    // Set up the connection upon load the web
    useEffect(() => {
        connect();
    }, [])

    const value = useMemo(() => ({ socket, ready, chatMessages, sendChat, sendMessage, sendStatusUpdate }), [ socket, ready, chatMessages, sendChat, sendMessage ]);
    return (
        <ChatbotContext.Provider value={value}>
            {children}
        </ChatbotContext.Provider>
    )
}

export function useChatbot() {
    return useContext(ChatbotContext);
}