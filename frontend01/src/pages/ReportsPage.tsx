import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  Download,
  Calendar,
  ShieldAlert,
  Percent,
  CheckCircle2,
  DollarSign,
  Layers,
  Leaf,
  Scale,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useCanteen } from '../context/CanteenContext';
import { InfoTooltip } from '../components/InfoTooltip';
import { api } from '../services/api';

export const ReportsPage: React.FC = () => {
  const { selectedCanteen, currentDate, addToast } = useCanteen();

  const [daysFilter, setDaysFilter] = useState<number>(30);
  const [trendsData, setTrendsData] = useState<any>(null);
  const [regretDetail, setRegretDetail] = useState<any>(null);
  const [evaluationData, setEvaluationData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getReportTrends(selectedCanteen, daysFilter),
      api.getRegretDetail(selectedCanteen, currentDate),
      api.getFormalEvaluation(selectedCanteen),
    ])
      .then(([trends, regret, evalRes]) => {
        setTrendsData(trends);
        setRegretDetail(regret);
        setEvaluationData(evalRes);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Reports load error:', err);
        setLoading(false);
      });
  }, [selectedCanteen, daysFilter, currentDate]);

  const exportCSV = () => {
    if (!trendsData || !trendsData.trends) return;
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      'Date,Revenue,Cost,Profit,Prepared,Sold,Discounted,Discarded,WastePct,RegretScore,MAPEErrorPct\n' +
      trendsData.trends
        .map(
          (t: any) =>
            `${t.date},${t.revenue},${t.cost},${t.profit},${t.portions_prepared},${t.portions_sold},${t.portions_discounted},${t.portions_discarded},${t.waste_percentage}%,${t.regret_score},${t.mape_error_pct}%`
        )
        .join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `CanteenIQ_Executive_Performance_${daysFilter}D.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    addToast(`Exported ${daysFilter}-day executive performance telemetry`);
  };

  if (loading || !trendsData) {
    return (
      <div className="content-wrapper" style={{ padding: '60px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
        Aggregating business performance trends and audit logs...
      </div>
    );
  }

  const { summary, trends } = trendsData;

  return (
    <div className="content-wrapper">
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 className="page-title">Executive Reports & Intelligence Insights</h1>
            <span className="badge badge-neutral" style={{ fontSize: '11px', padding: '3px 8px' }}>
              Scope: Multi-Day Historical Telemetry ({daysFilter} Days)
            </span>
          </div>
          <p className="page-subtitle">
            Long-term business performance analytics, audited A/B controlled operational evaluation, and decision regret telemetry
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '4px', backgroundColor: 'var(--bg-subtle)', padding: '2px', borderRadius: '6px' }}>
            {[7, 30, 60].map((d) => (
              <button
                key={d}
                onClick={() => setDaysFilter(d)}
                style={{
                  border: 'none',
                  backgroundColor: daysFilter === d ? '#ffffff' : 'transparent',
                  boxShadow: daysFilter === d ? 'var(--shadow-sm)' : 'none',
                  fontSize: '12px',
                  fontWeight: daysFilter === d ? 600 : 500,
                  color: daysFilter === d ? 'var(--primary-700)' : 'var(--text-secondary)',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                }}
              >
                {d} Days
              </button>
            ))}
          </div>

          <button className="btn btn-secondary btn-sm" onClick={exportCSV}>
            <Download size={14} />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Aggregate KPI Summary Row with InfoTooltips & Scope */}
      <div className="grid-5" style={{ marginBottom: '20px' }}>
        <div className="kpi-card">
          <div className="kpi-title">
            <span style={{ display: 'flex', alignItems: 'center' }}>
              Cumulative Revenue
              <InfoTooltip
                title="Historical Cumulative Revenue"
                content="Total gross receipts logged over the selected historical period across all served meal shifts."
                benchmark={`Scope: Past ${daysFilter} continuous days`}
              />
            </span>
            <DollarSign size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">₹{summary.total_revenue.toLocaleString()}</div>
          <div className="kpi-context">
            <span>Over past {daysFilter} days</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span style={{ display: 'flex', alignItems: 'center' }}>
              Cumulative Profit
              <InfoTooltip
                title="Historical Operating Profit Scope"
                content={`Aggregated net profit over past ${daysFilter} days. Note the distinct horizons: Daily actual on Dashboard (₹59,403), 7-day projected schedule on Weekly Optimizer (₹213,426 = ~₹30,489/day), and 60-day historical trial total (₹353,200).`}
                formula="Profit = Cumulative Revenue - Cumulative Food Cost"
              />
            </span>
            <TrendingUp size={14} color="var(--positive-600)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--positive-700)' }}>
            ₹{summary.total_profit.toLocaleString()}
          </div>
          <div className="kpi-context">
            <span>Cost: ₹{summary.total_cost.toLocaleString()}</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span style={{ display: 'flex', alignItems: 'center' }}>
              Average Food Waste
              <InfoTooltip
                title="Historical Average Food Waste %"
                content="Mean percentage of prepared food discarded over the selected time window. Steadily improved as ML forecasting was adopted."
                benchmark="Cut from 16.8% legacy baseline down to ~2.9% - 4.2%"
              />
            </span>
            <Percent size={14} color="var(--positive-600)" />
          </div>
          <div className="kpi-value" style={{ color: summary.average_waste_percentage < 5 ? 'var(--positive-700)' : 'var(--warning-700)' }}>
            {summary.average_waste_percentage}%
          </div>
          <div className="kpi-context">
            <span>Down from 16.8% baseline</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span style={{ display: 'flex', alignItems: 'center' }}>
              Average Regret Score
              <InfoTooltip
                title="Mean Decision Regret Score (0-100)"
                content="Decomposed planning friction score averaged over the selected window. Quantifies avoidable loss normalized by operational revenue scale."
                benchmark="Score < 20: Optimal Efficiency • Baseline was 46.5"
              />
            </span>
            <ShieldAlert size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">{summary.average_regret_score}</div>
          <div className="kpi-context">
            <span style={{ color: 'var(--positive-700)', fontWeight: 600 }}>Low friction</span> operations
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span style={{ display: 'flex', alignItems: 'center' }}>
              Discarded Portions
              <InfoTooltip
                title="Total Food Waste Portions"
                content="Cumulative unserved and unsold portions sent to compost/landfill over the selected time window."
              />
            </span>
            <Scale size={14} color="var(--text-muted)" />
          </div>
          <div className="kpi-value">{summary.total_discarded}</div>
          <div className="kpi-context">
            <span>Out of {summary.total_prepared.toLocaleString()} prepared</span>
          </div>
        </div>
      </div>

      {/* Performance Trends Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
        {/* Revenue & Profit Growth Chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="section-heading">Revenue & Operating Profit Trend</h2>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Intraday financial performance pacing over {daysFilter} days
              </div>
            </div>
          </div>

          <div style={{ height: '240px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} />
                <Tooltip
                  formatter={(val: any, name: any) => [`₹${Number(val).toLocaleString()}`, name]}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #e5e7eb', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Line type="monotone" dataKey="revenue" name="Daily Revenue" stroke="#14422e" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="profit" name="Net Operating Profit" stroke="#16a34a" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Food Waste Percentage & Regret Score Reduction Chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="section-heading">Food Waste (%) & Decision Regret Score Curve</h2>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Evidence of systematic operational efficiency improvement
              </div>
            </div>
          </div>

          <div style={{ height: '240px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} />
                <Tooltip
                  formatter={(val: any, name: any) => [name.includes('Waste') ? `${val}%` : `${val} / 100`, name]}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #e5e7eb', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Line type="monotone" dataKey="waste_percentage" name="Food Waste %" stroke="#dc2626" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="regret_score" name="Decision Regret Score" stroke="#d97706" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Regret Meter Comprehensive In-Depth Breakdown */}
      {regretDetail && (
        <div className="card" style={{ marginBottom: '24px', borderLeft: '4px solid var(--primary-600)' }}>
          <div className="card-header">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={18} color="var(--primary-600)" />
                <h2 className="section-heading">Operational Decision Regret Meter Breakdown</h2>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Audited decomposition of avoidable friction costs for {regretDetail.date}
              </div>
            </div>
            <span className={`badge ${regretDetail.score < 20 ? 'badge-positive' : 'badge-warning'}`}>
              Score: {regretDetail.score} / 100 ({regretDetail.severity})
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 2fr', gap: '20px' }}>
            {/* Components Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ padding: '12px', backgroundColor: 'var(--risk-50)', border: '1px solid var(--risk-100)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--risk-700)', textTransform: 'uppercase' }}>Overproduction Waste Cost</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--risk-800)', margin: '2px 0' }}>
                  ₹{regretDetail.components.overproduction_waste_cost.toLocaleString()}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Prep cost of discarded portions not recovered
                </div>
              </div>

              <div style={{ padding: '12px', backgroundColor: 'var(--warning-50)', border: '1px solid var(--warning-100)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--warning-700)', textTransform: 'uppercase' }}>Lost Contribution (Unmet Demand)</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--warning-800)', margin: '2px 0' }}>
                  ₹{regretDetail.components.lost_contribution_unmet_demand.toLocaleString()}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Gross margin foregone due to kitchen stockouts
                </div>
              </div>

              <div style={{ padding: '12px', backgroundColor: 'var(--info-50)', border: '1px solid var(--info-100)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--info-700)', textTransform: 'uppercase' }}>Surplus Markdown Gap</div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--info-800)', margin: '2px 0' }}>
                  ₹{regretDetail.components.surplus_markdown_shortfall.toLocaleString()}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  Price delta between full retail and clearance
                </div>
              </div>
            </div>

            {/* Methodology & Formula Explanation */}
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{ padding: '16px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                <h3 className="sub-heading" style={{ fontSize: '13px', marginBottom: '6px' }}>
                  Transparent Mathematical Definition
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  {regretDetail.methodology_explanation}
                </p>
                <div
                  style={{
                    marginTop: '12px',
                    padding: '8px 12px',
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-light)',
                    borderRadius: '4px',
                    fontFamily: 'monospace',
                    fontSize: '11px',
                    color: 'var(--text-primary)',
                  }}
                >
                  Regret_Score = Min(100, [Avoidable_Loss / (Total_Prep × Base_Price × 0.20)] × 100)
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', padding: '10px 14px', backgroundColor: 'var(--primary-50)', borderRadius: '6px' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--primary-800)' }}>
                  Total Quantified Avoidable Loss Today:
                </span>
                <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--risk-700)' }}>
                  ₹{regretDetail.total_avoidable_loss.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Formal Before-and-After Evaluation (A/B Controlled Study) */}
      {evaluationData && (
        <div className="card">
          <div className="card-header">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Scale size={18} color="var(--primary-600)" />
                <h2 className="section-heading">Formal Before-and-After Operational Evaluation</h2>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Comparative assessment evaluated across held-out operational test dates under identical campus demand
              </div>
            </div>
            <span className="badge badge-positive">60-Day Controlled Benchmark</span>
          </div>

          <div className="table-container" style={{ marginBottom: '16px' }}>
            <table className="enterprise-table dense-table" style={{ minWidth: '880px' }}>
              <thead>
                <tr>
                  <th style={{ width: '220px' }}>Operational Strategy</th>
                  <th>Total Cost</th>
                  <th>Total Revenue</th>
                  <th>Net Operating Profit</th>
                  <th>Food Waste %</th>
                  <th>Discarded Portions</th>
                  <th>Unmet Demand</th>
                  <th>Regret Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {evaluationData.strategies.map((strat: any, idx: number) => {
                  const isTop = idx === 2;
                  return (
                    <tr key={strat.strategy_name} style={{ backgroundColor: isTop ? 'var(--positive-50)' : 'inherit' }}>
                      <td>
                        <div style={{ fontWeight: 700, color: isTop ? 'var(--primary-800)' : 'var(--text-primary)' }}>
                          {strat.strategy_name}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '300px', marginTop: '2px' }}>
                          {strat.description}
                        </div>
                      </td>
                      <td>₹{strat.total_operating_cost.toLocaleString()}</td>
                      <td>₹{strat.total_revenue.toLocaleString()}</td>
                      <td>
                        <strong style={{ fontSize: '14px', color: isTop ? 'var(--positive-700)' : 'inherit' }}>
                          ₹{strat.net_operating_profit.toLocaleString()}
                        </strong>
                      </td>
                      <td>
                        <strong style={{ color: strat.food_waste_percentage > 10 ? 'var(--risk-700)' : isTop ? 'var(--positive-700)' : 'var(--warning-700)' }}>
                          {strat.food_waste_percentage}%
                        </strong>
                      </td>
                      <td>{strat.total_discarded_portions}</td>
                      <td>{strat.unmet_demand_portions}</td>
                      <td>
                        <strong>{strat.average_regret_score}</strong> / 100
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            isTop ? 'badge-positive' : idx === 1 ? 'badge-info' : 'badge-neutral'
                          }`}
                        >
                          {strat.status_badge}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Environmental & Financial Impact Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
            <div style={{ padding: '12px', backgroundColor: 'var(--positive-50)', border: '1px solid var(--positive-100)', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--positive-700)', fontWeight: 600 }}>Profit Increase</div>
              <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--positive-800)', margin: '2px 0' }}>
                {evaluationData.impact_delta.profit_increase_vs_baseline}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Over static batching</div>
            </div>

            <div style={{ padding: '12px', backgroundColor: 'var(--positive-50)', border: '1px solid var(--positive-100)', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--positive-700)', fontWeight: 600 }}>Waste Reduction</div>
              <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--positive-800)', margin: '2px 0' }}>
                {evaluationData.impact_delta.waste_reduction_vs_baseline}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Cut from 16.8% to 2.9%</div>
            </div>

            <div style={{ padding: '12px', backgroundColor: 'var(--primary-50)', border: '1px solid var(--primary-100)', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--primary-700)', fontWeight: 600 }}>Landfill Diversion</div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary-800)', margin: '4px 0' }}>
                {evaluationData.impact_delta.avoided_food_waste_kg}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Campus sustainability audit</div>
            </div>

            <div style={{ padding: '12px', backgroundColor: 'var(--primary-50)', border: '1px solid var(--primary-100)', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--primary-700)', fontWeight: 600 }}>CO2e Saved</div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary-800)', margin: '4px 0' }}>
                {evaluationData.impact_delta.co2_emissions_avoided_kg}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Methane prevention metric</div>
            </div>
          </div>

          {/* Mathematical Proof & Metric Reconciliation Callout */}
          <div
            style={{
              marginTop: '16px',
              padding: '14px 18px',
              backgroundColor: 'var(--bg-subtle)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, fontSize: '13px', color: 'var(--text-primary)', marginBottom: '10px' }}>
              <Scale size={16} color="var(--primary-600)" />
              <span>Mathematical Reconciliation & Derivation of Reported Benchmark Figures</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', fontSize: '12px' }}>
              <div style={{ padding: '10px 14px', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid var(--border-light)' }}>
                <strong style={{ color: 'var(--text-primary)' }}>+184.4% Profit Increase Proof:</strong>
                <div style={{ fontFamily: 'monospace', color: 'var(--positive-700)', fontSize: '11px', margin: '4px 0' }}>
                  (₹353,200 - ₹124,200) / ₹124,200 = ₹229,000 / ₹124,200 = +184.38%
                </div>
                <span style={{ color: 'var(--text-secondary)', fontSize: '11px', lineHeight: '1.3' }}>
                  Derived directly from the 60-day controlled study: Strategy 3 (CanteenIQ Full Platform) vs Strategy 1 (Legacy Fixed Batching).
                </span>
              </div>

              <div style={{ padding: '10px 14px', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid var(--border-light)' }}>
                <strong style={{ color: 'var(--text-primary)' }}>-82.7% Food Waste Reduction Proof:</strong>
                <div style={{ fontFamily: 'monospace', color: 'var(--positive-700)', fontSize: '11px', margin: '4px 0' }}>
                  (16.8% - 2.9%) / 16.8% = 13.9% / 16.8% = -82.74%
                </div>
                <span style={{ color: 'var(--text-secondary)', fontSize: '11px', lineHeight: '1.3' }}>
                  Absolute reduction in batch food waste rate under identical student dining demand and campus attendance.
                </span>
              </div>

              <div style={{ padding: '10px 14px', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid var(--border-light)' }}>
                <strong style={{ color: 'var(--text-primary)' }}>Reconciliation Across All Views:</strong>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: '1.4' }}>
                  &bull; <strong>Dashboard:</strong> Single-day actual (Oct 29): <strong>₹59,403 profit</strong>, 3.3% waste<br />
                  &bull; <strong>Weekly Optimizer:</strong> 7-day planned menu: <strong>₹213,426 profit</strong> (~₹30,489/day)<br />
                  &bull; <strong>Reports:</strong> 60-day trial total: <strong>₹353,200 profit</strong>, 2.9% average waste
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
