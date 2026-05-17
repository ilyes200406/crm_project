import { forwardRef } from 'react';

export const Input = forwardRef(function Input({ label, id, icon: Icon, error, className = '', ...props }, ref) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
  const borderClass = error
    ? 'border-red-400 focus:ring-red-400 focus:border-red-400'
    : 'border-gray-300 focus:ring-sky-400 focus:border-sky-400';

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-sm font-semibold text-gray-700">
          {label}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <Icon size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
        )}
        <input
          ref={ref}
          id={inputId}
          className={`border ${borderClass} rounded-lg ${Icon ? 'pl-9' : 'px-3'} pr-3 py-2.5 text-sm w-full focus:outline-none focus:ring-2 transition-colors ${className}`}
          {...props}
        />
      </div>
    </div>
  );
});
