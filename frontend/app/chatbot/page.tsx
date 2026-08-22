"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { api, ChatMessageResponse, MessageEntry, SuggestedAction } from "@/lib/api";
import ChatBubble from "@/components/chatbot/ChatBubble";
import ChatInput from "@/components/chatbot/ChatInput";
import SuggestedActions from "@/components/chatbot/SuggestedActions";

interface ChatMessage extends MessageEntry {
  isUser: boolean;
}

export default function ChatbotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<ChatMessageResponse | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const user = api.getUser();
  const userId = user?.id;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = useCallback(
    async (messageText: string) => {
      setIsLoading(true);
      setError(null);

      // Add user message immediately
      const userMessage: ChatMessage = {
        role: "user",
        content: messageText,
        timestamp: new Date().toISOString(),
        isUser: true,
      };
      setMessages((prev) => [...prev, userMessage]);

      try {
        const response = await api.sendChatMessage({
          message: messageText,
          user_id: userId,
          session_id: sessionId || undefined,
        });

        // Update session ID if this is a new session
        if (!sessionId && response.session_id) {
          setSessionId(response.session_id);
          localStorage.setItem("chatbot_session_id", response.session_id);
        }

        // Store last response for suggested actions
        setLastResponse(response);

        // Add assistant response
        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: response.response,
          agent: response.agent_used,
          timestamp: response.timestamp || new Date().toISOString(),
          isUser: false,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to send message");
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, userId]
  );

  const handleActionClick = useCallback(
    (action: SuggestedAction) => {
      sendMessage(action.label);
    },
    [sendMessage]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setLastResponse(null);
    if (sessionId) {
      api.clearConversation(sessionId).catch(console.error);
    }
  }, [sessionId]);

  // Load existing session from localStorage
  useEffect(() => {
    const storedSessionId = localStorage.getItem("chatbot_session_id");
    if (storedSessionId && !sessionId) {
      setSessionId(storedSessionId);
    }
  }, [sessionId]);

  // Welcome message
  useEffect(() => {
    if (messages.length === 0 && !isLoading) {
      const welcomeMessage: ChatMessage = {
        role: "assistant",
        content:
          "👋 Welcome to CineBook Chat! 🎬\n\nI'm your AI movie assistant, here to help you:\n\n🎥 **Find Movies** - Search for films by title, genre, or actor\n\n📅 **Showtimes** - Check what's playing and when\n\n🎫 **Book Tickets** - Reserve seats for your favorite movies\n\n📋 **Manage Bookings** - View or cancel your reservations\n\nWhat would you like to do today?",
        agent: "primary_assistant",
        timestamp: new Date().toISOString(),
        isUser: false,
      };
      setMessages([welcomeMessage]);
    }
  }, [isLoading, messages.length]);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="bg-surface border-b border-border px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="w-6 h-6 text-white"
              >
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">CineBook Assistant</h1>
              <p className="text-sm text-text-muted">AI-powered movie helper</p>
            </div>
          </div>
          <button
            onClick={clearChat}
            className="px-4 py-2 text-sm bg-surface border border-border rounded-lg text-text-muted hover:text-white hover:border-primary transition-colors"
          >
            Clear Chat
          </button>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 max-w-4xl w-full mx-auto flex flex-col">
        <div
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto p-6 space-y-4"
        >
          {messages.map((msg, index) => (
            <ChatBubble
              key={index}
              message={msg.content}
              isUser={msg.isUser}
              agentType={msg.agent}
              timestamp={msg.timestamp}
            />
          ))}

          {error && (
            <div className="bg-error/20 border border-error/50 rounded-lg p-4 text-error">
              {error}
            </div>
          )}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-surface rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-full bg-primary animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <span
                    className="w-2 h-2 rounded-full bg-primary animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <span
                    className="w-2 h-2 rounded-full bg-primary animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Actions */}
        {lastResponse?.suggested_actions &&
          lastResponse.suggested_actions.length > 0 &&
          !isLoading && (
            <div className="px-6 py-3 bg-surface/50 border-t border-border">
              <p className="text-xs text-text-muted mb-2">Quick actions:</p>
              <SuggestedActions
                actions={lastResponse.suggested_actions}
                onActionClick={handleActionClick}
              />
            </div>
          )}

        {/* Input */}
        <div className="border-t border-border bg-surface/30">
          <div className="max-w-4xl mx-auto">
            <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
          </div>
        </div>
      </div>
    </div>
  );
}
