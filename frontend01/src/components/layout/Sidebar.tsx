import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CalendarDays,
  TrendingUp,
  UtensilsCrossed,
  Sparkles,
  Boxes,
  BarChart3,
  Settings,
  ShoppingBag,
  Building2,
  ShieldCheck,
} from 'lucide-react';
import { useCanteen } from '../../context/CanteenContext';

export const Sidebar: React.FC = () => {
  const { selectedCanteen, setSelectedCanteen, canteens } = useCanteen();

  const currentCanteenObj = canteens.find((c) => c.id === selectedCanteen) || canteens[0];

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Analytics Calendar', path: '/analytics-calendar', icon: CalendarDays },
    { name: 'Demand Forecasting', path: '/forecasting', icon: TrendingUp },
    { name: 'Menu Optimizer', path: '/menu-optimizer', icon: UtensilsCrossed },
    { name: 'Surplus Food', path: '/surplus-food', icon: Sparkles },
    { name: 'Inventory & Procurement', path: '/inventory', icon: Boxes },
    { name: 'Reports & Insights', path: '/reports', icon: BarChart3 },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="app-sidebar">
      {/* Brand Header */}
      <div style={{ padding: '20px 18px', borderBottom: '1px solid var(--border-light)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              backgroundColor: 'var(--primary-600)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '16px',
            }}
          >
            CQ
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '16px', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
              Canteen<span style={{ color: 'var(--primary-600)' }}>IQ</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>
              Enterprise Intelligence
            </div>
          </div>
        </div>

        {/* Location Selector */}
        <div style={{ marginTop: '14px' }}>
          <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
            <Building2 size={12} /> Canteen Location
          </label>
          <select
            className="form-select"
            value={selectedCanteen}
            onChange={(e) => setSelectedCanteen(e.target.value)}
            style={{ fontSize: '12px', padding: '6px 8px' }}
          >
            {canteens.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Navigation Links */}
      <nav style={{ flex: 1, padding: '12px 10px', overflowY: 'auto' }}>
        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '4px 10px 8px 10px' }}>
          Operations Console
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '9px 12px',
                  borderRadius: 'var(--radius-md)',
                  textDecoration: 'none',
                  fontSize: '13px',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? 'var(--primary-700)' : 'var(--text-secondary)',
                  backgroundColor: isActive ? 'var(--primary-50)' : 'transparent',
                  borderLeft: isActive ? '3px solid var(--primary-600)' : '3px solid transparent',
                  transition: 'all 0.15s ease',
                })}
              >
                <Icon size={16} />
                <span className="sidebar-label">{item.name}</span>
              </NavLink>
            );
          })}
        </div>

        {/* Public Storefront Section */}
        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-light)' }}>
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '4px 10px 8px 10px' }}>
            External Storefront
          </div>
          <NavLink
            to="/surplus-marketplace"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '9px 12px',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
              fontSize: '13px',
              fontWeight: 500,
              color: isActive ? 'var(--info-700)' : 'var(--text-secondary)',
              backgroundColor: isActive ? 'var(--info-50)' : 'transparent',
            })}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShoppingBag size={16} />
              <span className="sidebar-label">Student Marketplace</span>
            </div>
            <span className="badge badge-info" style={{ fontSize: '10px', padding: '1px 5px' }}>Live</span>
          </NavLink>
        </div>
      </nav>

      {/* User Profile Footer */}
      <div
        style={{
          padding: '14px 16px',
          borderTop: '1px solid var(--border-light)',
          backgroundColor: '#fafbfa',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'var(--primary-100)',
            color: 'var(--primary-700)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 600,
            fontSize: '12px',
          }}
        >
          {currentCanteenObj.manager_name.split(' ').map((n) => n[0]).join('')}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {currentCanteenObj.manager_name}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--positive-600)' }}></span>
            Operations Lead
          </div>
        </div>
        <span title="Verified Admin Access">
          <ShieldCheck size={16} color="var(--primary-600)" />
        </span>
      </div>
    </aside>
  );
};
