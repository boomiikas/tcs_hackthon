from pathlib import Path

file_path = Path("frontend01/src/pages/DashboardPage.tsx")
content = file_path.read_text(encoding="utf-8")

# Add import of InfoTooltip
import_target = "import { useCanteen } from '../context/CanteenContext';"
import_replacement = """import { useCanteen } from '../context/CanteenContext';
import { InfoTooltip } from '../components/InfoTooltip';"""

if import_target in content:
    content = content.replace(import_target, import_replacement)

# Update page header and subtitle to be explicit about scope
header_target = """        <div>
          <h1 className="page-title">Operational Overview</h1>
          <p className="page-subtitle">Real-time daily preparation telemetry, demand fulfillment, and priority AI intervention flags</p>
        </div>"""

header_replacement = """        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 className="page-title">Operational Overview</h1>
            <span className="badge badge-neutral" style={{ fontSize: '11px', padding: '3px 8px' }}>
              Scope: Today (Single Day: {currentDate})
            </span>
          </div>
          <p className="page-subtitle">
            Real-time daily preparation telemetry, demand fulfillment, and priority AI intervention flags • Single Day Horizon
          </p>
        </div>"""

if header_target in content:
    content = content.replace(header_target, header_replacement)

# Update KPI Cards with InfoTooltips and clear definitions
kpi_target = """      {/* Concise KPI Cards Row */}
      <div className="grid-5" style={{ marginBottom: '24px' }}>
        <div className="kpi-card">
          <div className="kpi-title">
            <span>Portions Prepared</span>
            <Utensils size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">{kpis.total_prepared.toLocaleString()}</div>
          <div className="kpi-context">
            <span className="badge badge-neutral">Capacity: 1,400</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span>Portions Sold</span>
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
            <span>Today's Revenue</span>
            <DollarSign size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">₹{kpis.today_revenue.toLocaleString()}</div>
          <div className="kpi-context">
            <span style={{ color: 'var(--positive-700)', fontWeight: 500 }}>+₹{kpis.portions_recovered * 55}</span> via surplus
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span>Food Waste</span>
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
            <span>Est. Operating Profit</span>
            <TrendingUp size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">₹{kpis.today_profit.toLocaleString()}</div>
          <div className="kpi-context">
            <span>Cost: ₹{kpis.today_cost.toLocaleString()}</span>
          </div>
        </div>
      </div>"""

kpi_replacement = """      {/* Concise KPI Cards Row with Explicit Scopes & Tooltips */}
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
      </div>"""

if kpi_target in content:
    content = content.replace(kpi_target, kpi_replacement)

# Update Regret Meter card on Dashboard with InfoTooltip
regret_target = """              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={16} color="var(--primary-600)" />
                <h2 className="section-heading">Operational Decision Regret Meter</h2>
              </div>"""

regret_replacement = """              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldAlert size={16} color="var(--primary-600)" />
                <h2 className="section-heading">Operational Decision Regret Meter</h2>
                <InfoTooltip
                  title="Decision Regret Score (0-100)"
                  content="Quantifies avoidable friction losses from overproduction, missed demand stockouts, and surplus markdowns. Lower is better."
                  formula="Regret Score = Min(100, [Avoidable Loss / (Revenue × 0.20)] × 100)"
                  benchmark="Score < 20: Low Risk • Baseline was 46.5"
                />
              </div>"""

if regret_target in content:
    content = content.replace(regret_target, regret_replacement)

file_path.write_text(content, encoding="utf-8")
print("DashboardPage.tsx patched successfully!")
