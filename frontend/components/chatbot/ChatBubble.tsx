"use client";

import { AgentType } from "@/lib/api";
import ReactMarkdown from "react-markdown";

interface ChatBubbleProps {
  message: string;
  isUser: boolean;
  agentType?: AgentType;
  timestamp?: string;
}

export default function ChatBubble({
  message,
  isUser,
  agentType,
  timestamp,
}: ChatBubbleProps) {
  const agentLabels: Record<AgentType, string> = {
    primary_assistant: "Assistant",
    movie_agent: "Movie Expert",
    booking_agent: "Booking Expert",
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-primary text-white rounded-br-md"
            : "bg-surface text-white rounded-bl-md"
        }`}
      >
        {!isUser && agentType && (
          <div className="text-xs text-text-muted mb-1 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span>{agentLabels[agentType]}</span>
          </div>
        )}
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0 whitespace-pre-wrap">{children}</p>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
              li: ({ children }) => <li className="text-sm">{children}</li>,
              code: ({ children }) => (
                <code className="bg-surface/50 px-1.5 py-0.5 rounded text-xs font-mono">
                  {children}
                </code>
              ),
            }}
          >
            {message}
          </ReactMarkdown>
        </div>
        {timestamp && (
          <div className="text-xs text-white/50 mt-2 text-right">
            {new Date(timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
        )}
      </div>
    </div>
  );
}
