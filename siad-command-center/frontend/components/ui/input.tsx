'use client';

import { cn } from '@/lib/utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function Input({ label, className, ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm text-text-secondary mb-2">{label}</label>
      )}
      <input
        className={cn(
          'w-full bg-background border border-border rounded px-3 py-2 text-text-primary',
          'placeholder:text-text-secondary',
          'hover:border-accent/50 focus:border-accent transition-colors',
          className
        )}
        {...props}
      />
    </div>
  );
}
