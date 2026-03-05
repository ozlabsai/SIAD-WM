'use client';

import * as React from 'react';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  className?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = '', ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={`w-full px-3 py-2 bg-background text-text-primary border border-border
          rounded-md focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
          placeholder:text-text-secondary disabled:opacity-50 disabled:cursor-not-allowed
          ${className}`}
        {...props}
      />
    );
  }
);

Textarea.displayName = 'Textarea';
