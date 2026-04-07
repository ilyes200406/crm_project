/**
 * CARD COMPONENT
 * 
 * Conteneur générique avec header/footer optionnels
 */

import React from 'react';

/**
 * Card Component
 * 
 * @param {Object} props
 * @param {string} props.title - Card title (optional)
 * @param {React.ReactNode} props.headerAction - Header action element (optional)
 * @param {React.ReactNode} props.children - Card content
 * @param {React.ReactNode} props.footer - Card footer (optional)
 * @param {string} props.className - Additional CSS classes (optional)
 * @param {boolean} props.noPadding - Remove padding (optional)
 */
export function Card({
  title,
  headerAction,
  children,
  footer,
  className = '',
  noPadding = false,
}) {
  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {/* Header */}
      {(title || headerAction) && (
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
            {headerAction && <div>{headerAction}</div>}
          </div>
        </div>
      )}

      {/* Content */}
      <div className={noPadding ? '' : 'p-6'}>{children}</div>

      {/* Footer */}
      {footer && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          {footer}
        </div>
      )}
    </div>
  );
}