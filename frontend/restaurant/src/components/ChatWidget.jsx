import { useCallback, useEffect } from 'react';
import { useChatbot } from '../contexts/ChatbotContext';
import { Widget, addResponseMessage } from '@ryaneewx/react-chat-widget';
import "./component_css/chat_widget.css"
import  placeholder from "../assets/img/placeholder.jpg";

export default function ChatWidget() {
    // Get vars fromm chatbot context
    const { ready, sendChat, chatMessages } = useChatbot();

    const handleNewUserMessage = useCallback((message) => {
        const openai_message = {
            role: "user",
            content: message
        }
        sendChat(openai_message);
    }, [sendChat])

    // Add the chatbot messages to the UI whenever a new messages appears in the  chatMessages
    useEffect(() => {
        if(chatMessages && chatMessages.length > 0 && chatMessages[chatMessages.length-1].role === "assistant") {
            addResponseMessage(chatMessages[chatMessages.length-1].content);
        }
    }, [chatMessages]);

    return (
        <Widget
          handleNewUserMessage={handleNewUserMessage}
          profileAvatar={placeholder}
          title="Your assistant Vbot"
          subtitle="Welcome!"
          resizable={true}
          showCloseButton={true}
        />
    )
}