import React from 'react';
import { AlertTriangle, CheckCircle2, X } from 'lucide-react';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmVariant?: 'primary' | 'danger' | 'success';
  variant?: 'primary' | 'danger' | 'success';
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm Action',
  cancelLabel = 'Cancel',
  confirmVariant,
  variant = 'primary',
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null;

  const activeVariant = confirmVariant || variant;

  const getButtonBg = () => {
    if (activeVariant === 'danger') return 'var(--risk-600)';
    if (activeVariant === 'success') return 'var(--positive-700)';
    return 'var(--primary-600)';
  };

  return (
    <div className="modal-overlay" onClick={onCancel} role="dialog" aria-modal="true">
      <div
        className="modal-content"
        style={{ maxWidth: '440px', padding: '20px' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {confirmVariant === 'danger' ? (
              <AlertTriangle size={18} color="var(--risk-600)" />
            ) : confirmVariant === 'success' ? (
              <CheckCircle2 size={18} color="var(--positive-700)" />
            ) : (
              <AlertTriangle size={18} color="var(--warning-600)" />
            )}
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>{title}</h3>
          </div>
          <button className="btn-icon" onClick={onCancel} aria-label="Close modal">
            <X size={16} />
          </button>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.45', marginBottom: '20px' }}>
          {message}
        </p>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button className="btn btn-secondary btn-sm" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button
            className="btn btn-sm"
            onClick={onConfirm}
            style={{ backgroundColor: getButtonBg(), color: '#ffffff' }}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
