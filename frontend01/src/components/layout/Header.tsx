import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  Bell,
  Calendar,
  Clock,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  X,
  ExternalLink,
} from 'lucide-react';
import { useCanteen } from '../../context/CanteenContext';

export const Header: React.FC = () => {
  const location = useLocation();
  const { currentDate, setCurrentDate, toasts, removeToast, unreadAlertCount, setUnreadAlertCount } = useCanteen();
  const [showNotifications, setShowNotifications] = useState(false);

  // Generate breadcrumb from pathname
  const pathMap: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/analytics-calendar': 'Analytics Calendar',
    '/forecasting': 'Demand Forecasting',
    '/menu-optimizer': 'Menu Optimizer',
    '/surplus-food': 'Surplus Food Management',
    '/inventory': 'Inventory & Procurement',
    '/reports': 'Reports & Insights',
    '/settings': 'Platform Settings',
    '/surplus-marketplace': 'Student Marketplace',
  };

  const pageTitle = pathMap[location.pathname] || 'Overview';

  const notifications = [
    {
      id: 'n1',
      title: 'Surplus Markdown Trigger',
      desc: '14 portions of Paneer Butter Masala are eligible for 40% discount.',
      time: '12m ago',
      type: 'warning',
      link: '/surplus-food',
    },
    {
      id: 'n2',
      title: 'Procurement Alert',
      desc: 'Fresh Paneer stock (14.5 kg) is below reorder threshold (20 kg).',
      time: '34m ago',
      type: 'danger',
      link: '/inventory',
    },
    {
      id: 'n3',
      title: 'Optimization Model Ready',
      desc: 'Draft menu for Week 45 generated with 94.5% nutrition compliance.',
      time: '1h ago',
      type: 'success',
      link: '/menu-optimizer',
    },
  ];

  return (
    <header className="app-topbar">
      {/* Left: Breadcrumbs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>CanteenIQ</span>
        <span style={{ color: 'var(--border-medium)' }}>/</span>
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{pageTitle}</span>
      </div>

      {/* Right Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Service Shift Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: 'var(--primary-50)',
            color: 'var(--primary-700)',
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)',
            fontSize: '12px',
            fontWeight: 500,
          }}
        >
          <Clock size={13} />
          <span>Lunch Service Active</span>
        </div>

        {/* Date Selector Indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            color: 'var(--text-secondary)',
            backgroundColor: 'var(--bg-subtle)',
            padding: '4px 10px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-light)',
          }}
        >
          <Calendar size={13} color="var(--text-muted)" />
          <span style={{ fontWeight: 500 }}>{currentDate}</span>
        </div>

        {/* Notification Bell */}
        <div style={{ position: 'relative' }}>
          <button
            className="btn-icon"
            onClick={() => {
              setShowNotifications(!showNotifications);
              if (!showNotifications) setUnreadAlertCount(0);
            }}
            style={{ position: 'relative' }}
            title="Operational Alerts"
          >
            <Bell size={18} />
            {unreadAlertCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: '2px',
                  right: '2px',
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--risk-600)',
                }}
              />
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div
              style={{
                position: 'absolute',
                top: '36px',
                right: '0',
                width: '320px',
                backgroundColor: '#ffffff',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
                padding: '12px',
                zIndex: 60,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>Operational Alerts</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Real-time</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {notifications.map((n) => (
                  <Link
                    key={n.id}
                    to={n.link}
                    onClick={() => setShowNotifications(false)}
                    style={{
                      display: 'block',
                      padding: '8px 10px',
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: 'var(--bg-subtle)',
                      textDecoration: 'none',
                      color: 'inherit',
                      fontSize: '12px',
                      transition: 'background 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{n.title}</span>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{n.time}</span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>{n.desc}</div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Floating Toast Alerts */}
      <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 100, display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {toasts.map((t) => (
          <div
            key={t.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              backgroundColor: t.type === 'error' ? 'var(--risk-50)' : t.type === 'warning' ? 'var(--warning-50)' : 'var(--positive-50)',
              border: `1px solid ${t.type === 'error' ? 'var(--risk-100)' : t.type === 'warning' ? 'var(--warning-100)' : 'var(--positive-100)'}`,
              color: t.type === 'error' ? 'var(--risk-700)' : t.type === 'warning' ? 'var(--warning-700)' : 'var(--positive-700)',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              boxShadow: 'var(--shadow-md)',
              fontSize: '13px',
              fontWeight: 500,
              minWidth: '280px',
            }}
          >
            {t.type === 'error' ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
            <span style={{ flex: 1 }}>{t.message}</span>
            <button
              onClick={() => removeToast(t.id)}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit' }}
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </header>
  );
};
