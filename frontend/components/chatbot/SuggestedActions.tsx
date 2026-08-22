"use client";

import { SuggestedAction } from "@/lib/api";

interface SuggestedActionsProps {
  actions: SuggestedAction[];
  onActionClick: (action: SuggestedAction) => void;
}

export default function SuggestedActions({
  actions,
  onActionClick,
}: SuggestedActionsProps) {
  if (!actions || actions.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 p-3 border-t border-border bg-surface/30">
      {actions.map((action, index) => (
        <button
          key={`${action.action}-${index}`}
          onClick={() => onActionClick(action)}
          className="px-3 py-1.5 text-sm bg-surface border border-border rounded-full text-white/80 hover:bg-border hover:text-white transition-colors cursor-pointer"
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
