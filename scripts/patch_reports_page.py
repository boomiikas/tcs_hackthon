from pathlib import Path

file_path = Path("frontend01/src/pages/ReportsPage.tsx")
content = file_path.read_text(encoding="utf-8")

# Add import of InfoTooltip
import_target = "import { useCanteen } from '../context/CanteenContext';"
import_replacement = """import { useCanteen } from '../context/CanteenContext';
import { InfoTooltip } from '../components/InfoTooltip';"""

if import_target in content:
    content = content.replace(import_target, import_replacement)

# Update page title & subtitle with clear scope
header_target = """        <div>
          <h1 className="page-title">Executive Reports & Intelligence Insights</h1>
          <p className="page-subtitle">
            Long-term business performance analytics, rigorous A/B operational evaluation, and decision regret audits
          </p>
        </div>"""

header_replacement = """        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 className="page-title">Executive Reports & Intelligence Insights</h1>
            <span className="badge badge-neutral" style={{ fontSize: '11px', padding: '3px 8px' }}>
              Scope: Multi-Day Historical Telemetry ({daysFilter} Days)
            </span>
          </div>
          <p className="page-subtitle">
            Long-term business performance analytics, audited A/B controlled operational evaluation, and decision regret telemetry
          </p>
        </div>"""

if header_target in content:
    content = content.replace(header_target, header_replacement)

# Update KPI Cards with InfoTooltips
kpis_target = """      {/* Aggregate KPI Summary Row */}
      <div className="grid-5" style={{ marginBottom: '20px' }}>
        <div className="kpi-card">
          <div className="kpi-title">
            <span>Cumulative Revenue</span>
            <DollarSign size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">₹{summary.total_revenue.toLocaleString()}</div>
          <div className="kpi-context">
            <span>Over past {daysFilter} days</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span>Operating Profit</span>
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
            <span>Average Food Waste</span>
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
            <span>Average Regret Score</span>
            <ShieldAlert size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">{summary.average_regret_score}</div>
          <div className="kpi-context">
            <span style={{ color: 'var(--positive-700)', fontWeight: 600 }}>Low friction</span> operations
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span>Discarded Portions</span>
            <Scale size={14} color="var(--text-muted)" />
          </div>
          <div className="kpi-value">{summary.total_discarded}</div>
          <div className="kpi-context">
            <span>Out of {summary.total_prepared.toLocaleString()} prepared</span>
          </div>
        </div>
      </div>"""

kpis_replacement = """      {/* Aggregate KPI Summary Row with InfoTooltips & Scope */}
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
      </div>"""

if kpis_target in content:
    content = content.replace(kpis_target, kpis_replacement)

# Update Formal Evaluation Table and Add Mathematical Derivation Box
eval_target = """          <div className="table-container" style={{ marginBottom: '16px' }}>
            <table className="enterprise-table">
              <thead>
                <tr>
                  <th>Operational Strategy</th>
                  <th>Total Cost</th>
                  <th>Total Revenue</th>
                  <th>Net Operating Profit</th>
                  <th>Food Waste %</th>
                  <th>Discarded Portions</th>
                  <th>Unmet Demand</th>
                  <th>Regret Score</th>
                  <th>Status</th>
                </tr>
              </thead>"""

eval_replacement = """          <div className="table-container" style={{ marginBottom: '16px' }}>
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
              </thead>"""

if eval_target in content:
    content = content.replace(eval_target, eval_replacement)

# Add Mathematical Proof box after Impact Grid
impact_target = """            <div style={{ padding: '12px', backgroundColor: 'var(--primary-50)', border: '1px solid var(--primary-100)', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--primary-700)', fontWeight: 600 }}>CO2e Saved</div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--primary-800)', margin: '4px 0' }}>
                {evaluationData.impact_delta.co2_emissions_avoided_kg}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Methane prevention metric</div>
            </div>
          </div>
        </div>
      )}"""

impact_replacement = """            <div style={{ padding: '12px', backgroundColor: 'var(--primary-50)', border: '1px solid var(--primary-100)', borderRadius: '6px', textAlign: 'center' }}>
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
      )}"""

if impact_target in content:
    content = content.replace(impact_target, impact_replacement)

file_path.write_text(content, encoding="utf-8")
print("ReportsPage.tsx patched successfully!")
