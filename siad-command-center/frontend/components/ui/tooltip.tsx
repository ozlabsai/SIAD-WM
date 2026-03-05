'use client';

import * as React from 'react';
import { useState } from 'react';

interface TooltipProps {
  children: React.ReactNode;
  content: string;
  className?: string;
}

export function Tooltip({ children, content, className = '' }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        {children}
      </div>
      {isVisible && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1
          bg-panel border border-border rounded text-xs text-text-primary whitespace-nowrap z-50
          shadow-lg">
          {content}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1
            border-4 border-transparent border-t-panel" />
        </div>
      )}
    </div>
  );
}

interface TooltipProviderProps {
  children: React.ReactNode;
}

export function TooltipProvider({ children }: TooltipProviderProps) {
  return <>{children}</>;
}

interface TooltipTriggerProps {
  children: React.ReactNode;
  asChild?: boolean;
}

export function TooltipTrigger({ children }: TooltipTriggerProps) {
  return <>{children}</>;
}

interface TooltipContentProps {
  children: React.ReactNode;
  className?: string;
}

export function TooltipContent({ children, className = '' }: TooltipContentProps) {
  return <div className={className}>{children}</div>;
}
