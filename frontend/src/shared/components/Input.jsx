import { forwardRef } from 'react';

export const Input = forwardRef(function Input({ label, id, className = '', ...props }, ref) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <label className="flex flex-col gap-1.5" htmlFor={inputId}>
      {label ? <span className="text-sm font-semibold text-gray-700">{label}</span> : null}
      <input
        ref={ref}
        id={inputId}
        className={`border border-gray-300 rounded-lg px-3 py-2.5 text-sm w-full focus:outline-none focus:ring-2 focus:ring-sky-400 focus:border-sky-400 ${className}`}
        {...props}
      />
    </label>
  );
});
