import React, { useState } from 'react';
import { HelpCircle, Info } from 'lucide-react';

interface InfoTooltipProps {
  title?: string;
  content: string;
  formula?: string;
  benchmark?: string;
  size?: number;
}

export const InfoTooltip: React.FC<InfoTooltipProps> = ({
  title,
  content,
  formula,
  benchmark,
  size = 13,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <span
      className="metric-tooltip-container"
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
      onFocus={() => setIsOpen(true)}
      onBlur={() => setIsOpen(false)}
      tabIndex={0}
      role="button"
      aria-label={title || 'Metric explanation'}
      style={{ marginLeft: '4px', verticalAlign: 'middle', outline: 'none', display: 'inline-flex' }}
    >
      <Info size={size} color="var(--text-muted)" style={{ opacity: 0.8 }} />
      <div
        className="metric-tooltip-bubble"
        style={{
          opacity: isOpen ? 1 : 0,
          visibility: isOpen ? 'visible' : 'hidden',
        }}
      >
        {title && <div style={{ fontWeight: 600, marginBottom: '4px', color: '#ffffff' }}>{title}</div>}
        <div style={{ color: '#d1d5db', fontSize: '11px', lineHeight: '1.4' }}>{content}</div>
        {formula && (
          <div
            style={{
              marginTop: '6px',
              padding: '4px 6px',
              backgroundColor: '#272b29',
              borderRadius: '4px',
              fontFamily: 'monospace',
              fontSize: '10px',
              color: '#86efac',
            }}
          >
            {formula}
          </div>
        )}
        {benchmark && (
          <div style={{ marginTop: '5px', fontSize: '10px', color: '#9ca3af', borderTop: '1px solid #374151', paddingTop: '4px' }}>
            <strong>Benchmark:</strong> {benchmark}
          </div>
        )}
      </div>
    </span>
  );
};
