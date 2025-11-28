import React, { forwardRef } from 'react';
import { cn } from './Card'; // Reusing cn utility

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ label, error, className, ...props }, ref) => {
        return (
            <div className="w-full space-y-2">
                {label && (
                    <label className="text-sm font-medium text-secondary">
                        {label}
                    </label>
                )}
                <input
                    ref={ref}
                    className={cn(
                        "flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all disabled:cursor-not-allowed disabled:opacity-50",
                        error && "border-error focus:border-error focus:ring-error/20",
                        className
                    )}
                    {...props}
                />
                {error && <p className="text-xs text-error animate-fade-in">{error}</p>}
            </div>
        );
    }
);

Input.displayName = 'Input';
