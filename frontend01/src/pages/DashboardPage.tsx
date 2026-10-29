import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  AlertCircle,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Apple,
  ChevronRight,
  DollarSign,
  Utensils,
  Percent,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useCanteen } from '../context/CanteenContext';
import { InfoTooltip } from '../components/InfoTooltip';
import { api } from '../services/api';

export const DashboardPage: React.FC = () => {
  const { selectedCanteen, currentDate, addToast } = useCanteen();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [salesMetric, setSalesMetric] = useState<'revenue' | 'portions'>('revenue');

  useEffect(() => {
    setLoading(true);
    api.getDashboard(selectedCanteen, currentDate)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load dashboard:', err);
        setLoading(false);
      });
  }, [selectedCanteen, currentDate]);

  if (loading || !data) {
    return (
      <div className="content-wrapper" style={{ padding: '60px 0', textAlign: 'center' }}>
        <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Loading real-time canteen operational telemetry...</div>
      </div>
    );
  }

  const { kpis, hourly_performance, breakdown, recommendations, nutrition_snapshot, regret_meter } = data;

  return (
    <div className="content-wrapper">
      {/* Header Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 className="page-title">Operational Overview</h1>
            <span className="badge badge-neutral" style={{ fontSize: '11px', padding: '3px 8px' }}>
              Scope: Today (Single Day: {currentDate})
            </span>
          </div>
          <p className="page-subtitle">
            Real-time daily preparation telemetry, demand fulfillment, and priority AI intervention flags • Single Day Horizon
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/analytics-calendar')}>
            View Historical Calendar
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/forecasting')}>
            Plan Next Shift
          </button>
        </div>
      </div>

      {/* Concise KPI Cards Row with Explicit Scopes & Tooltips */}
      <div className="grid-5" style={{ marginBottom: '24px' }}>
        <div className="kpi-card">
          <div className="kpi-title">
            <span style={{ display: 'flex', alignItems: 'center' }}>
              Portions Prepared
              <InfoTooltip
                title="Portions Prepared (Single Day)"
                content="Sum of physical meal portions batch-cooked across Breakfast, Lunch, Snacks, and Dinner shifts today."
                benchmark="Kitchen nominal capacity: 1,400 portions/day"
              />
            </span>
            <Utensils size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">{kpis.total_prepared.toLocaleString()}</div>
          <div className="kpi-context">
            <span className="badge badge-neutral">Capacity: 1,400</span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Today</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span style={{ display: 'flex', alignItems: 'center' }}>
              Portions Sold
              <InfoTooltip
                title="Full-Price Clearance"
                content="Meals sold at standard retail price before surplus recovery."
                formula="Fulfillment = (Sold / Prepared) = 93.9%"
              />
            </span>
            <TrendingUp size={14} color="var(--positive-600)" />
          </div>
          <div className="kpi-value">{kpis.total_sold.toLocaleString()}</div>
          <div className="kpi-context">
            <span style={{ color: 'var(--positive-700)', fontWeight: 600 }}>
              {Math.round((kpis.total_sold / kpis.total_prepared) * 100)}%
            </span>{' '}
            full-price clearance
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span style={{ display: 'flex', alignItems: 'center' }}>
              Today's Revenue
              <InfoTooltip
                title="Today's Logged Revenue"
                content="Gross cash receipts logged for today's service shifts."
                formula="Revenue = (Sold × Base Price) + (Surplus Recovered × Clearance Price)"
              />
            </span>
            <DollarSign size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">₹{kpis.today_revenue.toLocaleString()}</div>
          <div className="kpi-context">
            <span style={{ color: 'var(--positive-700)', fontWeight: 500 }}>+₹{(kpis.portions_recovered * 55).toLocaleString()}</span> via surplus rescue
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span style={{ display: 'flex', alignItems: 'center' }}>
              Food Waste %
              <InfoTooltip
                title="Daily Food Waste Rate"
                content="Percentage of batch-cooked food discarded to composting or waste bins."
                formula="Waste % = (Discarded Portions / Total Prepared) × 100"
                benchmark="Today: 3.3% • Down from 16.8% legacy unoptimized baseline"
              />
            </span>
            <Percent size={14} color={kpis.waste_percentage > 5 ? 'var(--warning-600)' : 'var(--positive-600)'} />
          </div>
          <div className="kpi-value" style={{ color: kpis.waste_percentage > 5 ? 'var(--warning-700)' : 'var(--positive-700)' }}>
            {kpis.waste_percentage}%
          </div>
          <div className="kpi-context">
            <span>{kpis.portions_discarded} discarded portions</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span style={{ display: 'flex', alignItems: 'center' }}>
              Today's Net Profit
              <InfoTooltip
                title="Operating Profit (Single Day Scope)"
                content="Net operating profit for today (Oct 29). For the 7-day optimized menu projection, see Weekly Optimizer (₹213,426 = ~₹30,489/day). For the 60-day historical trial aggregate, see Executive Reports (₹353,200)."
                formula="Profit = Revenue (₹100,777) - Food Cost (₹41,374) = ₹59,403"
              />
            </span>
            <TrendingUp size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">₹{kpis.today_profit.toLocaleString()}</div>
          <div className="kpi-context">
            <span>Cost: ₹{kpis.today_cost.toLocaleString()} • Single Day</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Charts & Regret Meter */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '24px' }}>
        {/* A. Today's Sales Performance */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="section-heading">Today's Sales Performance</h2>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Real-time intraday fulfillment pacing across service windows
              </div>
            </div>
            <div style={{ display: 'flex', gap: '4px', backgroundColor: 'var(--bg-subtle)', padding: '2px', borderRadius: '6px' }}>
              <button
                className={`btn btn-sm ${salesMetric === 'revenue' ? 'btn-secondary' : ''}`}
                style={{
                  border: 'none',
                  backgroundColor: salesMetric === 'revenue' ? '#ffffff' : 'transparent',
                  boxShadow: salesMetric === 'revenue' ? 'var(--shadow-sm)' : 'none',
                  fontSize: '11px',
                  padding: '4px 10px',
                }}
                onClick={() => setSalesMetric('revenue')}
              >
                Revenue (₹)
              </button>
              <button
                className={`btn btn-sm ${salesMetric === 'portions' ? 'btn-secondary' : ''}`}
                style={{
                  border: 'none',
                  backgroundColor: salesMetric === 'portions' ? '#ffffff' : 'transparent',
                  boxShadow: salesMetric === 'portions' ? 'var(--shadow-sm)' : 'none',
                  fontSize: '11px',
                  padding: '4px 10px',
                }}
                onClick={() => setSalesMetric('portions')}
              >
                Portions Sold
              </button>
            </div>
          </div>

          <div style={{ height: '260px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourly_performance} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="salesGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#14422e" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#14422e" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val: any) => [salesMetric === 'revenue' ? `₹${Number(val).toLocaleString()}` : `${val} portions`, salesMetric === 'revenue' ? 'Revenue' : 'Portions']}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #e5e7eb', fontSize: '12px' }}
                />
                <Area
                  type="monotone"
                  dataKey={salesMetric === 'revenue' ? 'revenue' : 'portions_sold'}
                  stroke="#14422e"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#salesGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* B. Preparation and Waste Breakdown */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="section-heading">Portion Disposition</h2>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Non-double-counted disposition breakdown
              </div>
            </div>
          </div>

          <div style={{ height: '170px', position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={breakdown}
                  dataKey="portions"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                >
                  {breakdown.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any, name: any) => [`${value} portions (${Math.round((value / kpis.total_prepared) * 100)}%)`, name]}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #e5e7eb', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Legend Items */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
            {breakdown.map((b: any) => (
              <div key={b.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '2px', backgroundColor: b.color }} />
                  <span style={{ color: 'var(--text-secondary)' }}>{b.name}</span>
                </div>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {b.portions} ({b.share_pct}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Grid: AI Recommendations, Nutrition & Regret Meter */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        {/* C. Prioritized AI Recommendations */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={16} color="var(--primary-600)" />
              <h2 className="section-heading">Operational AI Recommendations</h2>
            </div>
            <span className="badge badge-info">{recommendations.length} Active Flags</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {recommendations.map((rec: any) => (
              <div
                key={rec.id}
                style={{
                  border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-md)',
                  padding: '14px',
                  backgroundColor: '#fafbfa',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`badge ${rec.priority === 'Urgent' ? 'badge-risk' : rec.priority === 'High' ? 'badge-warning' : 'badge-neutral'}`}>
                      {rec.priority}
                    </span>
                    <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      {rec.type}
                    </span>
                  </div>
                </div>

                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  {rec.title}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  {rec.reason}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-light)' }}>
                  <span style={{ fontSize: '11px', color: 'var(--primary-700)', fontWeight: 500 }}>
                    💡 {rec.impact}
                  </span>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      addToast(`Navigating to ${rec.action_label}`, 'info');
                      navigate(rec.action_route);
                    }}
                    style={{ fontSize: '11px', padding: '4px 10px' }}
                  >
                    <span>{rec.action_label}</span>
                    <ArrowRight size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Nutrition Snapshot & Regret Meter */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* E. Operational Decision Regret Meter */}
          <div className="card" style={{ borderLeft: '4px solid var(--primary-600)' }}>
            <div className="card-header" style={{ marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldAlert size={16} color="var(--primary-600)" />
                <h2 className="section-heading">Operational Decision Regret Meter</h2>
                <InfoTooltip
                  title="Decision Regret Score (0-100)"
                  content="Quantifies avoidable friction losses from overproduction, missed demand stockouts, and surplus markdowns. Lower is better."
                  formula="Regret Score = Min(100, [Avoidable Loss / (Revenue × 0.20)] × 100)"
                  benchmark="Score < 20: Low Risk • Baseline was 46.5"
                />
              </div>
              <span className={`badge ${regret_meter.score < 20 ? 'badge-positive' : 'badge-warning'}`}>
                {regret_meter.severity}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px', margin: '4px 0' }}>
              <span style={{ fontSize: '32px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {regret_meter.score}
              </span>
              <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/ 100</span>
              <span style={{ marginLeft: 'auto', fontSize: '13px', fontWeight: 600, color: 'var(--risk-600)' }}>
                ₹{regret_meter.avoidable_loss.toLocaleString()} avoidable loss
              </span>
            </div>

            <div className="progress-track">
              <div
                className="progress-bar"
                style={{
                  width: `${Math.min(100, regret_meter.score)}%`,
                  backgroundColor: regret_meter.score < 20 ? 'var(--positive-600)' : 'var(--warning-600)',
                }}
              />
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4', marginTop: '8px' }}>
              Quantified financial impact of overproduction waste and stockout friction. Down from 38.5 baseline via CanteenIQ forecasting.
            </p>

            <div style={{ marginTop: '12px', textAlign: 'right' }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => navigate('/reports')}
                style={{ fontSize: '11px', padding: '3px 8px' }}
              >
                <span>Methodology & Historical Trends</span>
                <ChevronRight size={12} />
              </button>
            </div>
          </div>

          {/* D. Nutrition Snapshot */}
          <div className="card">
            <div className="card-header" style={{ marginBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Apple size={16} color="var(--positive-600)" />
                <h2 className="section-heading">Today's Nutrition Snapshot</h2>
              </div>
              <span className="badge badge-positive">{nutrition_snapshot.menu_compliance_score}% Balanced</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', textAlign: 'center', margin: '10px 0' }}>
              <div style={{ padding: '8px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Avg Calories</div>
                <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>{nutrition_snapshot.average_calories} kcal</div>
              </div>
              <div style={{ padding: '8px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Avg Protein</div>
                <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>{nutrition_snapshot.protein_avg_g}g</div>
              </div>
              <div style={{ padding: '8px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Avg Carbs</div>
                <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>{nutrition_snapshot.carbs_avg_g}g</div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Focus: {nutrition_snapshot.dominant_dietary}</span>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => navigate('/menu-optimizer')}
                style={{ fontSize: '11px', padding: '3px 8px' }}
              >
                <span>Full Menu Optimizer</span>
                <ChevronRight size={12} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
