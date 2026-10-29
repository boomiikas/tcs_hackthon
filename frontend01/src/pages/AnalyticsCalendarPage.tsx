import React, { useState, useEffect } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Download,
  Calendar as CalendarIcon,
  X,
  TrendingUp,
  AlertTriangle,
  Award,
  Sparkles,
  ClipboardList,
} from 'lucide-react';
import { useCanteen } from '../context/CanteenContext';
import { api } from '../services/api';

export const AnalyticsCalendarPage: React.FC = () => {
  const { selectedCanteen, addToast } = useCanteen();

  const [year, setYear] = useState<number>(2026);
  const [month, setMonth] = useState<number>(10); // October
  const [selectedMetric, setSelectedMetric] = useState<'revenue' | 'waste_percentage' | 'portions_sold' | 'profit' | 'surplus_recovery_revenue'>('waste_percentage');
  const [calendarData, setCalendarData] = useState<any>(null);
  const [selectedDate, setSelectedDate] = useState<string>('2026-10-29');
  const [dateDetail, setDateDetail] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);

  // Month navigation
  const prevMonth = () => {
    if (month === 1) {
      setMonth(12);
      setYear(year - 1);
    } else {
      setMonth(month - 1);
    }
  };

  const nextMonth = () => {
    if (month === 12) {
      setMonth(1);
      setYear(year + 1);
    } else {
      setMonth(month + 1);
    }
  };

  const jumpToToday = () => {
    setYear(2026);
    setMonth(10);
    setSelectedDate('2026-10-29');
  };

  // Fetch monthly calendar overview
  useEffect(() => {
    setLoading(true);
    api.getCalendarOverview(selectedCanteen, year, month)
      .then((res) => {
        setCalendarData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load calendar:', err);
        setLoading(false);
      });
  }, [selectedCanteen, year, month]);

  // Fetch detailed report when selectedDate changes
  useEffect(() => {
    if (!selectedDate) return;
    setDetailLoading(true);
    api.getCalendarDateDetail(selectedDate, selectedCanteen)
      .then((res) => {
        setDateDetail(res);
        setDetailLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load date detail:', err);
        setDetailLoading(false);
      });
  }, [selectedDate, selectedCanteen]);

  // Build calendar matrix (Days of Month)
  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDayDOW = new Date(year, month - 1, 1).getDay(); // 0 = Sun
  const monthName = new Date(year, month - 1, 1).toLocaleString('default', { month: 'long' });

  // Map of date str -> day data
  const dateMap = new Map<string, any>();
  if (calendarData && calendarData.days) {
    calendarData.days.forEach((d: any) => dateMap.set(d.date, d));
  }

  // Heatmap intensity helper
  const getCellColor = (dayData: any) => {
    if (!dayData) return '#ffffff';
    if (selectedMetric === 'waste_percentage') {
      const w = dayData.waste_percentage;
      if (w <= 4) return '#dcfce7'; // positive green
      if (w <= 8) return '#fef3c7'; // mild amber
      if (w <= 14) return '#fed7aa'; // orange
      return '#fee2e2'; // risk red
    }
    if (selectedMetric === 'revenue') {
      const r = dayData.revenue;
      if (r > 90000) return '#bbf7d0';
      if (r > 70000) return '#dcfce7';
      return '#f0fdf4';
    }
    if (selectedMetric === 'profit') {
      const p = dayData.profit;
      if (p > 50000) return '#bbf7d0';
      if (p > 35000) return '#dcfce7';
      return '#f0fdf4';
    }
    return '#f3f4f6';
  };

  const exportDateReport = () => {
    if (!dateDetail || !dateDetail.has_data) return;
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      'Food Item,Meal Period,Prepared,Sold,Discounted,Discarded,Revenue,Cost,Waste Pct\n' +
      dateDetail.menu_items
        .map(
          (m: any) =>
            `"${m.food_name}","${m.meal_period}",${m.prepared},${m.sold},${m.discounted},${m.discarded},${m.revenue},${m.cost},${m.waste_percent}%`
        )
        .join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `CanteenIQ_${selectedDate}_Audit.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    addToast(`Exported operational audit report for ${selectedDate}`);
  };

  return (
    <div className="content-wrapper">
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
        <div>
          <h1 className="page-title">Analytics Calendar</h1>
          <p className="page-subtitle">Investigate historical operational outcomes, waste anomalies, and daily meal audits</p>
        </div>

        {/* Heatmap Metric Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Heatmap Metric:
          </span>
          <select
            className="form-select"
            value={selectedMetric}
            onChange={(e: any) => setSelectedMetric(e.target.value)}
            style={{ width: '180px', padding: '6px 10px', fontSize: '12px' }}
          >
            <option value="waste_percentage">Food Waste (%)</option>
            <option value="revenue">Total Revenue (₹)</option>
            <option value="profit">Operating Profit (₹)</option>
            <option value="portions_sold">Portions Sold</option>
            <option value="surplus_recovery_revenue">Surplus Recovered (₹)</option>
          </select>
          <button className="btn btn-secondary btn-sm" onClick={jumpToToday}>
            Today
          </button>
        </div>
      </div>

      {/* Main Layout: Calendar Grid on Left, Date Detail Side Panel on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '24px' }}>
        {/* Left: Monthly Calendar Grid */}
        <div className="card">
          {/* Month & Year Navigation Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h2 className="section-heading" style={{ fontSize: '18px' }}>
                {monthName} {year}
              </h2>
              <span className="badge badge-neutral" style={{ fontSize: '11px' }}>
                {calendarData ? `${calendarData.recorded_days_count} Recorded Days` : 'Loading...'}
              </span>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button className="btn btn-secondary btn-sm" onClick={prevMonth} title="Previous Month">
                <ChevronLeft size={16} />
              </button>
              <button className="btn btn-secondary btn-sm" onClick={nextMonth} title="Next Month">
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          {/* Days of Week Header */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '6px', textAlign: 'center', marginBottom: '8px' }}>
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((dow) => (
              <div key={dow} style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                {dow}
              </div>
            ))}
          </div>

          {/* Days Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '6px' }}>
            {/* Empty slots before first day */}
            {Array.from({ length: firstDayDOW }).map((_, i) => (
              <div key={`empty-${i}`} style={{ height: '70px', borderRadius: 'var(--radius-sm)', backgroundColor: 'transparent' }} />
            ))}

            {/* Days in Month */}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const dayNum = i + 1;
              const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`;
              const dayData = dateMap.get(dateStr);
              const isSelected = selectedDate === dateStr;
              const isToday = dateStr === '2026-10-29';

              return (
                <div
                  key={dateStr}
                  onClick={() => setSelectedDate(dateStr)}
                  style={{
                    height: '70px',
                    borderRadius: 'var(--radius-md)',
                    border: isSelected ? '2px solid var(--primary-600)' : '1px solid var(--border-light)',
                    backgroundColor: getCellColor(dayData),
                    padding: '6px 8px',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    transition: 'all 0.15s ease',
                    boxShadow: isSelected ? 'var(--shadow-md)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', fontWeight: isToday || isSelected ? 700 : 500, color: 'var(--text-primary)' }}>
                      {dayNum}
                    </span>
                    {isToday && (
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--primary-600)' }} />
                    )}
                  </div>

                  {dayData ? (
                    <div>
                      {selectedMetric === 'waste_percentage' && (
                        <div style={{ fontSize: '11px', fontWeight: 600, color: dayData.waste_percentage > 5 ? 'var(--warning-700)' : 'var(--positive-700)' }}>
                          {dayData.waste_percentage}% waste
                        </div>
                      )}
                      {selectedMetric === 'revenue' && (
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--primary-700)' }}>
                          ₹{(dayData.revenue / 1000).toFixed(0)}k rev
                        </div>
                      )}
                      {selectedMetric === 'profit' && (
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--positive-700)' }}>
                          ₹{(dayData.profit / 1000).toFixed(0)}k pft
                        </div>
                      )}
                      {selectedMetric === 'portions_sold' && (
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)' }}>
                          {dayData.portions_sold} sold
                        </div>
                      )}
                      {selectedMetric === 'surplus_recovery_revenue' && (
                        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--info-700)' }}>
                          +₹{dayData.surplus_recovery_revenue}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>No logs</div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Accessible Heatmap Legend */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--border-light)' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>
              Heatmap Scale ({selectedMetric.replace('_', ' ')}):
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#dcfce7', border: '1px solid #bbf7d0' }} />
                <span>Optimal</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#fef3c7', border: '1px solid #fde68a' }} />
                <span>Moderate</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#fee2e2', border: '1px solid #fecaca' }} />
                <span>Attention Required</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Selected Date Detailed Report Side Panel */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', maxHeight: '720px', overflowY: 'auto' }}>
          <div className="card-header" style={{ marginBottom: '12px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CalendarIcon size={16} color="var(--primary-600)" />
                <h2 className="section-heading">Daily Audit: {selectedDate}</h2>
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Comprehensive day log and meal performance
              </div>
            </div>
            {dateDetail && dateDetail.has_data && (
              <button className="btn btn-secondary btn-sm" onClick={exportDateReport} title="Export CSV Report">
                <Download size={14} />
                <span>Export</span>
              </button>
            )}
          </div>

          {detailLoading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading date performance metrics...
            </div>
          ) : !dateDetail || !dateDetail.has_data ? (
            <div style={{ padding: '40px 20px', textAlign: 'center', backgroundColor: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <AlertTriangle size={24} color="var(--warning-600)" style={{ margin: '0 auto 8px auto' }} />
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>No Records Logged</div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                Operational records have not been submitted for this date or canteen was closed.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Daily Summary Metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', textAlign: 'center' }}>
                <div style={{ padding: '8px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Prepared</div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>{dateDetail.summary.portions_prepared}</div>
                </div>
                <div style={{ padding: '8px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Sold</div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--positive-700)' }}>{dateDetail.summary.portions_sold}</div>
                </div>
                <div style={{ padding: '8px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Surplus Recov.</div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--info-700)' }}>{dateDetail.summary.portions_discounted}</div>
                </div>
                <div style={{ padding: '8px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Discarded</div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: dateDetail.summary.portions_discarded > 40 ? 'var(--risk-700)' : 'var(--text-primary)' }}>
                    {dateDetail.summary.portions_discarded} ({dateDetail.summary.waste_percentage}%)
                  </div>
                </div>
              </div>

              {/* Financial Snapshot */}
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', backgroundColor: 'var(--primary-50)', borderRadius: 'var(--radius-md)' }}>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--primary-700)' }}>Revenue Logged</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--primary-800)' }}>₹{dateDetail.summary.revenue.toLocaleString()}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--primary-700)' }}>Food Prep Cost</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--primary-800)' }}>₹{dateDetail.summary.cost.toLocaleString()}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--primary-700)' }}>Operating Profit</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--positive-700)' }}>₹{dateDetail.summary.profit.toLocaleString()}</div>
                </div>
              </div>

              {/* Best & Least Selling Items */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {dateDetail.best_seller && (
                  <div style={{ padding: '10px', border: '1px solid var(--border-light)', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--positive-700)', fontWeight: 600 }}>
                      <Award size={12} /> Top Performer
                    </div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                      {dateDetail.best_seller.food_name}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {dateDetail.best_seller.sold} sold (₹{dateDetail.best_seller.revenue})
                    </div>
                  </div>
                )}
                {dateDetail.least_seller && (
                  <div style={{ padding: '10px', border: '1px solid var(--border-light)', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--warning-700)', fontWeight: 600 }}>
                      <AlertTriangle size={12} /> Surplus Outlier
                    </div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                      {dateDetail.least_seller.food_name}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {dateDetail.least_seller.discarded} discarded ({dateDetail.least_seller.waste_percent}% waste)
                    </div>
                  </div>
                )}
              </div>

              {/* Menu Items Table */}
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
                          <td style={{ fontWeight: 500 }}>{m.food_name}</td>
                          <td>
                            <span className="badge badge-neutral" style={{ fontSize: '10px' }}>
                              {m.meal_period}
                            </span>
                          </td>
                          <td>
                            {m.prepared} / <strong>{m.sold}</strong>
                          </td>
                          <td>
                            <span style={{ color: 'var(--info-700)' }}>{m.discounted}</span> /{' '}
                            <span style={{ color: m.discarded > 5 ? 'var(--risk-600)' : 'var(--text-muted)' }}>
                              {m.discarded}
                            </span>
                          </td>
                          <td>
                            <span style={{ fontWeight: 600, color: m.waste_percent > 8 ? 'var(--risk-600)' : 'var(--positive-700)' }}>
                              {m.waste_percent}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Recorded Inventory Issues & AI Notes */}
              <div style={{ padding: '12px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
                  <Sparkles size={14} color="var(--primary-600)" />
                  <span>AI Shift Summary</span>
                </div>
                <ul style={{ paddingLeft: '18px', fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {dateDetail.ai_recommendations.map((note: string, idx: number) => (
                    <li key={idx}>{note}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
