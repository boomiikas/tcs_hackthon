import React, { useState, useEffect } from 'react';
import {
  Settings,
  ShieldCheck,
  Save,
  Bell,
  Thermometer,
  Layers,
  DollarSign,
  Utensils,
  CheckCircle2,
  Users,
} from 'lucide-react';
import { useCanteen } from '../context/CanteenContext';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const { addToast } = useCanteen();

  const [activeTab, setActiveTab] = useState<'operational' | 'safety' | 'roles' | 'notifications'>('operational');

  // Form states
  const [kitchenCapacity, setKitchenCapacity] = useState<number>(1400);
  const [defaultBufferStrategy, setDefaultBufferStrategy] = useState<string>('balanced');
  const [holdingTemp, setHoldingTemp] = useState<number>(65);
  const [coldTemp, setColdTemp] = useState<number>(4);
  const [maxHoldingHours, setMaxHoldingHours] = useState<number>(4.0);
  const [compostPartner, setCompostPartner] = useState<string>('Campus Green Circular Bio-Composting Facility');

  const [notifyLowStock, setNotifyLowStock] = useState<boolean>(true);
  const [notifyExpiryWarning, setNotifyExpiryWarning] = useState<boolean>(true);
  const [notifySurplusTrigger, setNotifySurplusTrigger] = useState<boolean>(true);

  const saveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    addToast('Platform configuration and safety parameters updated!', 'success');
  };

  return (
    <div className="content-wrapper">
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
        <div>
          <h1 className="page-title">Settings & System Administration</h1>
          <p className="page-subtitle">
            Operational defaults, safety temperature thresholds, role permissions, and alert triggers
          </p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={saveSettings}>
          <Save size={14} />
          <span>Save Changes</span>
        </button>
      </div>

      {/* Tabs Bar */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-light)', marginBottom: '20px' }}>
        {[
          { id: 'operational', label: 'Operational Defaults', icon: Layers },
          { id: 'safety', label: 'Food Safety Compliance', icon: Thermometer },
          { id: 'roles', label: 'Roles & Access Control', icon: Users },
          { id: 'notifications', label: 'Notification Alerts', icon: Bell },
        ].map((tab) => {
          const Icon = tab.icon;
          const isSelected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                background: 'transparent',
                border: 'none',
                borderBottom: isSelected ? '2px solid var(--primary-600)' : '2px solid transparent',
                fontWeight: isSelected ? 600 : 500,
                color: isSelected ? 'var(--primary-700)' : 'var(--text-secondary)',
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              <Icon size={15} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Operational Defaults */}
      {activeTab === 'operational' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="card">
            <h2 className="section-heading" style={{ marginBottom: '14px' }}>Kitchen Capacity & Buffer Defaults</h2>
            <form onSubmit={saveSettings} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label className="form-label">Canteen Daily Preparation Capacity (Portions)</label>
                <input
                  type="number"
                  className="form-input"
                  value={kitchenCapacity}
                  onChange={(e) => setKitchenCapacity(Number(e.target.value))}
                />
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Total maximum daily portions the line can prep without overtime penalty.
                </span>
              </div>

              <div>
                <label className="form-label">Default Buffer Optimization Policy</label>
                <select
                  className="form-select"
                  value={defaultBufferStrategy}
                  onChange={(e) => setDefaultBufferStrategy(e.target.value)}
                >
                  <option value="conservative">Conservative (Min Waste, Low Buffer)</option>
                  <option value="balanced">Balanced (Newsvendor Critical Fractile)</option>
                  <option value="aggressive">Aggressive (High Service Level, Zero Stockout)</option>
                </select>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Governs standard safety margin added to mean predicted demand.
                </span>
              </div>

              <div>
                <label className="form-label">Standard Operating Hours</label>
                <input type="text" className="form-input" defaultValue="07:30 AM – 10:00 PM" />
              </div>

              <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
                Update Operational Limits
              </button>
            </form>
          </div>

          <div className="card">
            <h2 className="section-heading" style={{ marginBottom: '14px' }}>Campus Location Details</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px' }}>
              <div style={{ padding: '12px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Central Student Commons (Main)</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Location: Campus Center, Block A • Manager: Priya Sharma
                </div>
              </div>

              <div style={{ padding: '12px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Engineering Quad Cafeteria</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Location: Tech Wing 3, Ground Floor • Manager: David Chen
                </div>
              </div>

              <div style={{ padding: '12px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Graduate Hall Bistro</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Location: Grad Residence Quad, Tower C • Manager: Amina Al-Mansoor
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Food Safety Compliance */}
      {activeTab === 'safety' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="card">
            <h2 className="section-heading" style={{ marginBottom: '14px' }}>Temperature & Holding Rules</h2>
            <form onSubmit={saveSettings} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label className="form-label">Minimum Hot-Holding Temperature (°C)</label>
                <input
                  type="number"
                  className="form-input"
                  value={holdingTemp}
                  onChange={(e) => setHoldingTemp(Number(e.target.value))}
                />
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Statutory minimum: 63°C. Recommended enterprise threshold: 65°C.
                </span>
              </div>

              <div>
                <label className="form-label">Maximum Cold-Display Temperature (°C)</label>
                <input
                  type="number"
                  className="form-input"
                  value={coldTemp}
                  onChange={(e) => setColdTemp(Number(e.target.value))}
                />
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Yogurts, chilled wraps, and salad greens. Statutory ceiling: 5°C.
                </span>
              </div>

              <div>
                <label className="form-label">Maximum Safe Shelf Life Window (Hours)</label>
                <input
                  type="number"
                  step="0.5"
                  className="form-input"
                  value={maxHoldingHours}
                  onChange={(e) => setMaxHoldingHours(Number(e.target.value))}
                />
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Items exceeding this window must be retired from sale and dispatched to composting.
                </span>
              </div>

              <div>
                <label className="form-label">Bio-Waste & Organic Composting Partner</label>
                <input
                  type="text"
                  className="form-input"
                  value={compostPartner}
                  onChange={(e) => setCompostPartner(e.target.value)}
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
                Save Safety Standards
              </button>
            </form>
          </div>

          <div className="card" style={{ backgroundColor: 'var(--primary-50)', border: '1px solid var(--primary-100)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary-800)', marginBottom: '8px' }}>
              <ShieldCheck size={20} />
              <h2 className="section-heading" style={{ color: 'inherit' }}>Food Safety First Mandate</h2>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--primary-800)', lineHeight: '1.5' }}>
              CanteenIQ enforces regulatory HACCP protocols. Surplus recovery discount mechanisms automatically shut off if:
            </p>
            <ul style={{ paddingLeft: '18px', fontSize: '12px', color: 'var(--primary-800)', marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <li>Steam table logs drop below 63°C for &gt; 15 minutes.</li>
              <li>Remaining collection window drops below 15 minutes to guarantee student safety.</li>
              <li>Batch origin records or allergen certifications are missing from inventory.</li>
            </ul>
          </div>
        </div>
      )}

      {/* Tab 3: Roles & Access Control */}
      {activeTab === 'roles' && (
        <div className="card">
          <h2 className="section-heading" style={{ marginBottom: '14px' }}>Role-Based Access Control (RBAC)</h2>
          <div className="table-container">
            <table className="enterprise-table">
              <thead>
                <tr>
                  <th>Role Title</th>
                  <th>Assigned Staff</th>
                  <th>Forecast Tuning</th>
                  <th>Menu Approval</th>
                  <th>Discount Override</th>
                  <th>Procurement POs</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: 600 }}>Super Admin (Enterprise Lead)</td>
                  <td>Executive Management</td>
                  <td>Full Access</td>
                  <td>Full Access</td>
                  <td>Full Access</td>
                  <td>Full Access</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Canteen Operations Lead</td>
                  <td>Priya Sharma, David Chen</td>
                  <td>Tune Buffers</td>
                  <td>Approve & Publish</td>
                  <td>Approve Custom %</td>
                  <td>Submit Orders</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Head Chef / Kitchen Lead</td>
                  <td>3 Campus Shift Leads</td>
                  <td>View Staged Plan</td>
                  <td>Suggest Recipes</td>
                  <td>Log Batch Times</td>
                  <td>Stock Count Only</td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Counter Cashier / Student Worker</td>
                  <td>12 Staff</td>
                  <td>Read Only</td>
                  <td>Read Only</td>
                  <td>Scan Pickup Pass</td>
                  <td>No Access</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Notifications */}
      {activeTab === 'notifications' && (
        <div className="card" style={{ maxWidth: '640px' }}>
          <h2 className="section-heading" style={{ marginBottom: '14px' }}>Notification Alert Preferences</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>Low Ingredient Stock Alerts</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Notify when inventory dips below safety reorder threshold</div>
              </div>
              <input
                type="checkbox"
                checked={notifyLowStock}
                onChange={(e) => setNotifyLowStock(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: 'var(--primary-600)' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--border-light)' }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>Ingredient Expiry Warnings</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Send urgent reminder 24 hours prior to batch expiry</div>
              </div>
              <input
                type="checkbox"
                checked={notifyExpiryWarning}
                onChange={(e) => setNotifyExpiryWarning(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: 'var(--primary-600)' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--border-light)' }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>Surplus Recovery Auto-Triggers</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Suggest automatic markdown clearance 1 hour before meal close</div>
              </div>
              <input
                type="checkbox"
                checked={notifySurplusTrigger}
                onChange={(e) => setNotifySurplusTrigger(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: 'var(--primary-600)' }}
              />
            </div>

            <button className="btn btn-primary" onClick={saveSettings} style={{ marginTop: '10px', alignSelf: 'flex-start' }}>
              Save Alert Preferences
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
