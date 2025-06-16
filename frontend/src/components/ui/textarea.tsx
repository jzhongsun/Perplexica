import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { forwardRef } from 'react';

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  isSaving?: boolean;
  onSave?: (value: string) => void;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, isSaving, onSave, ...props }, ref) => {
    return (
      <div className="relative">
        <textarea
          className={cn(
            "placeholder:text-sm text-sm w-full flex items-center justify-between p-3 bg-light-secondary dark:bg-dark-secondary rounded-lg hover:bg-light-200 dark:hover:bg-dark-200 transition-colors",
            className
          )}
          ref={ref}
          rows={4}
          onBlur={(e) => onSave?.(e.target.value)}
          {...props}
        />
        {isSaving && (
          <div className="absolute right-3 top-3">
            <Loader2
              size={16}
              className="animate-spin text-black/70 dark:text-white/70"
            />
          </div>
        )}
      </div>
    );
  }
);

Textarea.displayName = "Textarea";

export { Textarea }; 