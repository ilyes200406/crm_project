export function Button({ children, variant = 'primary', loading = false, className = '', ...props }) {
  const base = 'w-full py-2.5 px-4 rounded-xl text-white font-semibold cursor-pointer border-0 disabled:opacity-60 disabled:cursor-not-allowed transition-colors';
  const variants = {
    primary:   'bg-slate-900 hover:bg-slate-800',
    secondary: 'bg-gray-700 hover:bg-gray-600',
    danger:    'bg-red-700 hover:bg-red-600',
  };

  return (
    <button
      className={`${base} ${variants[variant] ?? variants.primary} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? 'Veuillez patienter...' : children}
    </button>
  );
}
