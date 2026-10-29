from pathlib import Path

file_path = Path("frontend01/src/pages/AnalyticsCalendarPage.tsx")
content = file_path.read_text(encoding="utf-8")

# Add import of InfoTooltip
import_target = "import { useCanteen } from '../context/CanteenContext';"
import_replacement = """import { useCanteen } from '../context/CanteenContext';
import { InfoTooltip } from '../components/InfoTooltip';"""

if import_target in content:
    content = content.replace(import_target, import_replacement)

# Update layout container to split-workspace
grid_target = """      {/* Calendar Grid & Details Side Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '24px' }}>"""

grid_replacement = """      {/* Calendar Grid & Details Side Panel with Responsive Split-Workspace */}
      <div className="split-workspace" style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '24px' }}>"""

if grid_target in content:
    content = content.replace(grid_target, grid_replacement)

# Update Heatmap Metric selector label
metric_target = """          <label style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-muted)' }}>HEATMAP METRIC:</label>"""

metric_replacement = """          <label style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
            HEATMAP METRIC:
            <InfoTooltip
              title="Calendar Heatmap Metric"
              content="Visual color gradient based on daily operational telemetry. In Food Waste mode: Green is optimal (<4%), Amber is moderate (4-8%), and Red indicates severe overproduction (>8%)."
            />
          </label>"""

if metric_target in content:
    content = content.replace(metric_target, metric_replacement)

# Update Dishes Served Table to dense with sticky headers and ellipsis
table_target = """              {/* Menu Items Table */}
              <div>
                <h3 className="sub-heading" style={{ marginBottom: '8px', fontSize: '13px' }}>
                  Dishes Served Breakdown
                </h3>
                <div className="table-container">
                  <table className="enterprise-table">
                    <thead>
                      <tr>
                        <th>Dish Name</th>
                        <th>Meal</th>
                        <th>Prep / Sold</th>
                        <th>Surplus / Discard</th>
                        <th>Waste %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dateDetail.menu_items.map((m: any) => (
                        <tr key={m.food_id}>
                          <td style={{ fontWeight: 500 }}>{m.food_name}</td>"""

table_replacement = """              {/* Menu Items Table with Sticky Headers & Dense Formatting */}
              <div>
                <h3 className="sub-heading" style={{ marginBottom: '8px', fontSize: '13px' }}>
                  Dishes Served Breakdown
                </h3>
                <div className="table-container" style={{ maxHeight: '340px' }}>
                  <table className="enterprise-table dense-table" style={{ minWidth: '460px' }}>
                    <thead>
                      <tr>
                        <th style={{ width: '160px' }}>Dish Name</th>
                        <th style={{ width: '80px' }}>Meal</th>
                        <th style={{ width: '90px' }}>Prep / Sold</th>
                        <th style={{ width: '100px' }}>Surplus / Discard</th>
                        <th style={{ width: '70px' }}>Waste %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dateDetail.menu_items.map((m: any) => (
                        <tr key={m.food_id}>
                          <td
                            style={{ fontWeight: 500, maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                            title={m.food_name}
                          >
                            {m.food_name}
                          </td>"""

if table_target in content:
    content = content.replace(table_target, table_replacement)

file_path.write_text(content, encoding="utf-8")
print("AnalyticsCalendarPage.tsx patched successfully!")
