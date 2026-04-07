export function FieldError({ message }) {
  if (!message) return null;
  return <p className="text-red-700 text-xs mt-0.5">{message}</p>;
}
