"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { api, ChatMessageResponse, MessageEntry, SuggestedAction } from "@/lib/api";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import SuggestedActions from "./SuggestedActions";

interface ChatMessage extends MessageEntry {
  isUser: boolean;
}

interface ChatWindowProps {
  userId?: string;
  initialSessionId?: string;
  className?: string;
}

export default function ChatWindow({
  userId,
  initialSessionId,
  className = "",
}: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId || null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [lastResponse, setLastResponse] = useState<ChatMessageResponse | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

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
          // Store in localStorage for persistence
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
        // Remove the user message if the request failed
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, userId]
  );

  const handleActionClick = useCallback(
    (action: SuggestedAction) => {
      // Send the action as a message
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

  // Welcome message for new users
  useEffect(() => {
    if (messages.length === 0 && !isLoading) {
      const welcomeMessage: ChatMessage = {
        role: "assistant",
        content:
          "👋 Welcome to CineBook! I'm your movie assistant.\n\nI can help you with:\n- Finding movies and showtimes\n- Booking tickets\n- Managing your reservations\n\nWhat would you like to do?",
        agent: "primary_assistant",
        timestamp: new Date().toISOString(),
        isUser: false,
      };
      setMessages([welcomeMessage]);
    }
  }, [isLoading, messages.length]);

  if (isMinimized) {
    return (
      <button
        onClick={() => setIsMinimized(false)}
        className={`fixed bottom-6 right-6 w-14 h-14 bg-primary hover:bg-primary-hover rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-105 ${className}`}
        aria-label="Open chat"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-7 h-7 text-white"
        >
          <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z" />
          <path d="M7 9h10v2H7zm0-3h10v2H7z" />
        </svg>
        <span className="absolute top-1 right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
      </button>
    );
  }

  return (
    <div
      className={`fixed bottom-6 right-6 w-[400px] h-[600px] max-w-[calc(100vw-48px)] max-h-[calc(100vh-120px)] bg-background rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-border ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-surface border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-5 h-5 text-white"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
            </svg>
          </div>
          <div>
            <h3 className="font-semibold text-white">CineBook Assistant</h3>
            <p className="text-xs text-text-muted">Powered by AI</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearChat}
            className="p-2 text-text-muted hover:text-white transition-colors"
            title="Clear chat"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-5 h-5"
            >
              <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
            </svg>
          </button>
          <button
            onClick={() => setIsMinimized(true)}
            className="p-2 text-text-muted hover:text-white transition-colors"
            title="Minimize"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-5 h-5"
            >
              <path d="M19 13H5v-2h14v2z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
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
          <div className="bg-error/20 border border-error/50 rounded-lg p-3 text-error text-sm">
            {error}
          </div>
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-surface rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex items-center gap-2 text-text-muted">
                <span className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Actions */}
      {lastResponse?.suggested_actions && lastResponse.suggested_actions.length > 0 && !isLoading && (
        <SuggestedActions
          actions={lastResponse.suggested_actions}
          onActionClick={handleActionClick}
        />
      )}

      {/* Input */}
      <ChatInput
        onSendMessage={sendMessage}
        isLoading={isLoading}
        disabled={false}
      />
    </div>
  );
}
