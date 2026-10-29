import React, { useState, useEffect } from 'react';
import {
  Boxes,
  Plus,
  AlertTriangle,
  ShoppingCart,
  CheckCircle2,
  TrendingDown,
  ArrowRight,
  PackagePlus,
  PackageMinus,
  RefreshCw,
  Search,
} from 'lucide-react';
import { useCanteen } from '../context/CanteenContext';
import { InfoTooltip } from '../components/InfoTooltip';
import { ConfirmModal } from '../components/ConfirmModal';
import { api } from '../services/api';

export const InventoryPage: React.FC = () => {
  const { selectedCanteen, addToast } = useCanteen();

  const [ingredients, setIngredients] = useState<any[]>([]);
  const [procurementRecs, setProcurementRecs] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [recsLoading, setRecsLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('All');
  const [selectedStockAdjustment, setSelectedStockAdjustment] = useState<any>(null);
  const [adjustmentAmount, setAdjustmentAmount] = useState<number>(5);
  const [adjustmentType, setAdjustmentType] = useState<'restock' | 'usage'>('usage');
  const [poConfirmModal, setPoConfirmModal] = useState<{ isOpen: boolean; title: string; message: string; action: () => void }>({
    isOpen: false,
    title: '',
    message: '',
    action: () => {},
  });

  const loadData = () => {
    setLoading(true);
    setRecsLoading(true);

    api.getInventory()
      .then((data) => {
        setIngredients(data || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Inventory error:', err);
        setLoading(false);
      });

    api.getProcurementRecommendations('MENU-2026-W44')
      .then((recs) => {
        setProcurementRecs(recs || []);
        setRecsLoading(false);
      })
      .catch((err) => {
        console.error('Procurement error:', err);
        setRecsLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, [selectedCanteen]);

  const handleAdjustStock = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStockAdjustment) return;

    const delta = adjustmentType === 'restock' ? adjustmentAmount : -adjustmentAmount;
    api.adjustStock({
      ingredient_id: selectedStockAdjustment.id,
      delta: delta,
      reason: adjustmentType === 'restock' ? 'Purchase Delivery Receipt' : 'Daily Kitchen Usage',
    })
      .then((res) => {
        addToast(`Updated stock for ${selectedStockAdjustment.name} (New Stock: ${res.current_stock} ${selectedStockAdjustment.unit})`, 'success');
        setSelectedStockAdjustment(null);
        loadData();
      })
      .catch((err) => {
        addToast(`Stock update failed: ${err.message}`, 'error');
      });
  };

  const handlePlaceOrder = (rec: any) => {
    setPoConfirmModal({
      isOpen: true,
      title: `Create Purchase Order: ${rec.ingredient_name}`,
      message: `Are you sure you want to place a purchase order for ${rec.suggested_order} ${rec.unit} of ${rec.ingredient_name} with ${rec.supplier} for an estimated cost of ₹${rec.estimated_procurement_cost.toLocaleString()}?`,
      action: () => {
        api.placeOrder({
          ingredient_id: rec.ingredient_id,
          quantity: rec.suggested_order,
          supplier: rec.supplier,
          unit_cost: rec.avg_cost,
        })
          .then(() => {
            addToast(`Purchase Order created: ${rec.suggested_order} ${rec.unit} of ${rec.ingredient_name} ordered from ${rec.supplier}`, 'success');
            loadData();
          })
          .catch((err) => {
            addToast(`Failed to place order: ${err.message}`, 'error');
          });
        setPoConfirmModal((prev) => ({ ...prev, isOpen: false }));
      },
    });
  };

  // Filtered ingredients
  const filtered = ingredients.filter((it) => {
    const matchesSearch = it.name.toLowerCase().includes(searchTerm.toLowerCase()) || it.supplier.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCat = categoryFilter === 'All' || it.category === categoryFilter;
    return matchesSearch && matchesCat;
  });

  const lowStockCount = ingredients.filter((it) => it.status === 'Low Stock' || it.status === 'Critical').length;
  const totalValuation = ingredients.reduce((acc, it) => acc + (it.current_stock * it.avg_cost), 0);

  return (
    <div className="content-wrapper">
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
        <div>
          <h1 className="page-title">Inventory & Ingredient Procurement</h1>
          <p className="page-subtitle">
            Ingredient stock levels, recipe-to-menu consumption projections, and automated procurement orders
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary btn-sm" onClick={loadData}>
            <RefreshCw size={14} />
            <span>Refresh Stock</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid-4" style={{ marginBottom: '20px' }}>
        <div className="kpi-card">
          <div className="kpi-title">
            <span>Tracked Ingredients</span>
            <Boxes size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">{ingredients.length}</div>
          <div className="kpi-context">
            <span>Mapped to 16 active recipes</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span>Attention Required</span>
            <AlertTriangle size={14} color={lowStockCount > 0 ? 'var(--warning-600)' : 'var(--positive-600)'} />
          </div>
          <div className="kpi-value" style={{ color: lowStockCount > 0 ? 'var(--warning-700)' : 'var(--positive-700)' }}>
            {lowStockCount}
          </div>
          <div className="kpi-context">
            <span>Below safety reorder threshold</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span>Total Inventory Value</span>
            <Boxes size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">₹{Math.round(totalValuation).toLocaleString()}</div>
          <div className="kpi-context">
            <span>At weighted average purchase cost</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span>Procurement Pending</span>
            <ShoppingCart size={14} color="var(--info-600)" />
          </div>
          <div className="kpi-value">
            {procurementRecs.filter((r) => r.suggested_order > 0).length}
          </div>
          <div className="kpi-context">
            <span>Orders recommended for menu</span>
          </div>
        </div>
      </div>

      {/* Menu-Driven Procurement Recommendations Panel */}
      <div className="card" style={{ marginBottom: '24px', borderLeft: '4px solid var(--primary-600)' }}>
        <div className="card-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShoppingCart size={16} color="var(--primary-600)" />
              <h2 className="section-heading">Menu-Driven Procurement Recommendations</h2>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Computed by multiplying approved weekly menu portions by standardized recipe formulas minus existing on-hand stock
            </div>
          </div>
          <span className="badge badge-info">Linked to Menu 2026-W44</span>
        </div>

        {recsLoading ? (
          <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Calculating ingredient requirements from approved schedule...
          </div>
        ) : (
          <div className="table-container" style={{ maxHeight: '380px' }}>
            <table className="enterprise-table dense-table" style={{ minWidth: '920px' }}>
              <thead>
                <tr>
                  <th style={{ width: '80px' }}>Urgency</th>
                  <th style={{ width: '160px' }}>Ingredient</th>
                  <th style={{ width: '110px' }}>Current Stock</th>
                  <th style={{ width: '120px' }}>Menu Need</th>
                  <th style={{ width: '110px' }}>Suggested PO</th>
                  <th style={{ width: '90px' }}>Est. Cost</th>
                  <th style={{ width: '150px' }}>Supplier & Lead Time</th>
                  <th>Explanation & Rationale</th>
                  <th style={{ width: '90px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {procurementRecs.filter((r) => r.suggested_order > 0).map((rec) => (
                  <tr key={rec.ingredient_id}>
                    <td>
                      <span
                        className={`badge ${
                          rec.urgency === 'Urgent'
                            ? 'badge-risk'
                            : rec.urgency === 'High'
                            ? 'badge-warning'
                            : 'badge-neutral'
                        }`}
                        style={{ fontSize: '10px', fontWeight: 600 }}
                      >
                        {rec.urgency}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>{rec.ingredient_name}</td>
                    <td>
                      <span style={{ fontWeight: 600, color: rec.current_stock < rec.reorder_threshold ? 'var(--risk-700)' : 'inherit' }}>
                        {rec.current_stock} {rec.unit}
                      </span>
                    </td>
                    <td>
                      {rec.required_for_menu} {rec.unit}
                    </td>
                    <td>
                      <strong style={{ color: 'var(--primary-700)', fontSize: '13px' }}>
                        {rec.suggested_order} {rec.unit}
                      </strong>
                    </td>
                    <td>
                      <strong>₹{rec.estimated_procurement_cost.toLocaleString()}</strong>
                    </td>
                    <td>
                      <div style={{ fontSize: '12px', fontWeight: 500 }}>{rec.supplier}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{rec.lead_time_days} day lead time</div>
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--text-secondary)', maxWidth: '280px', lineHeight: '1.3' }}>
                      {rec.reason}
                    </td>
                    <td>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handlePlaceOrder(rec)}
                        style={{ fontSize: '11px', padding: '4px 10px' }}
                      >
                        <ShoppingCart size={12} />
                        <span>Place PO</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Main Ingredient Stock Inventory Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="section-heading">Master Ingredients Inventory</h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Current stock on-hand, reorder thresholds, and shelf-life tracking
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <select
              className="form-select"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              style={{ width: '140px', padding: '4px 8px', fontSize: '12px' }}
            >
              <option value="All">All Categories</option>
              <option value="Grain">Grain & Pulses</option>
              <option value="Dairy">Dairy</option>
              <option value="Protein">Protein & Poultry</option>
              <option value="Vegetable">Vegetable Produce</option>
              <option value="Bakery">Bakery & Batters</option>
            </select>

            <div style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder="Search ingredients..."
                className="form-input"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ width: '180px', padding: '4px 10px 4px 28px', fontSize: '12px' }}
              />
              <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '8px', top: '9px' }} />
            </div>
          </div>
        </div>

        <div className="table-container" style={{ maxHeight: '440px' }}>
          <table className="enterprise-table dense-table" style={{ minWidth: '880px' }}>
            <thead>
              <tr>
                <th style={{ width: '180px' }}>Ingredient Name</th>
                <th style={{ width: '90px' }}>Category</th>
                <th style={{ width: '100px' }}>Stock</th>
                <th style={{ width: '60px' }}>Unit</th>
                <th style={{ width: '90px' }}>Avg Cost</th>
                <th style={{ width: '110px' }}>Threshold</th>
                <th style={{ width: '150px' }}>Supplier</th>
                <th style={{ width: '100px' }}>Expiry</th>
                <th style={{ width: '80px' }}>Status</th>
                <th style={{ width: '110px' }}>Quick Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id}>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.name}</td>
                  <td>
                    <span className="badge badge-neutral" style={{ fontSize: '10px' }}>
                      {item.category}
                    </span>
                  </td>
                  <td>
                    <strong style={{ fontSize: '13px', color: item.current_stock <= item.reorder_threshold ? 'var(--risk-700)' : 'var(--text-primary)' }}>
                      {item.current_stock}
                    </strong>
                  </td>
                  <td style={{ color: 'var(--text-muted)' }}>{item.unit}</td>
                  <td>₹{item.avg_cost}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {item.reorder_threshold} {item.unit}
                  </td>
                  <td style={{ fontSize: '12px' }}>{item.supplier}</td>
                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{item.expiry_date}</td>
                  <td>
                    <span
                      className={`badge ${
                        item.status === 'Critical'
                          ? 'badge-risk'
                          : item.status === 'Low Stock'
                          ? 'badge-warning'
                          : 'badge-positive'
                      }`}
                      style={{ fontSize: '10px' }}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => {
                          setSelectedStockAdjustment(item);
                          setAdjustmentType('usage');
                          setAdjustmentAmount(5);
                        }}
                        title="Log Usage"
                        style={{ fontSize: '10px', padding: '3px 6px' }}
                      >
                        <PackageMinus size={12} />
                        <span>Usage</span>
                      </button>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => {
                          setSelectedStockAdjustment(item);
                          setAdjustmentType('restock');
                          setAdjustmentAmount(15);
                        }}
                        title="Log Delivery"
                        style={{ fontSize: '10px', padding: '3px 6px' }}
                      >
                        <PackagePlus size={12} />
                        <span>Restock</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stock Adjustment Modal */}
      {selectedStockAdjustment && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Boxes size={18} color="var(--primary-600)" />
                <h2 className="section-heading">Adjust Stock: {selectedStockAdjustment.name}</h2>
              </div>
              <button className="btn-icon" onClick={() => setSelectedStockAdjustment(null)}>✕</button>
            </div>

            <form onSubmit={handleAdjustStock} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ padding: '12px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Current Stock On-Hand:</div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {selectedStockAdjustment.current_stock} {selectedStockAdjustment.unit}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Reorder Threshold: {selectedStockAdjustment.reorder_threshold} {selectedStockAdjustment.unit}
                </div>
              </div>

              <div>
                <label className="form-label">Adjustment Type</label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="button"
                    className={`btn ${adjustmentType === 'usage' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setAdjustmentType('usage')}
                    style={{ flex: 1 }}
                  >
                    <PackageMinus size={14} />
                    <span>Log Daily Kitchen Usage (-)</span>
                  </button>
                  <button
                    type="button"
                    className={`btn ${adjustmentType === 'restock' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setAdjustmentType('restock')}
                    style={{ flex: 1 }}
                  >
                    <PackagePlus size={14} />
                    <span>Receive Supplier Delivery (+)</span>
                  </button>
                </div>
              </div>

              <div>
                <label className="form-label">
                  Quantity ({selectedStockAdjustment.unit})
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  className="form-input"
                  value={adjustmentAmount}
                  onChange={(e) => setAdjustmentAmount(Number(e.target.value))}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '10px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setSelectedStockAdjustment(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Confirm Stock Update
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
          {/* PO Confirmation Modal */}
      <ConfirmModal
        isOpen={poConfirmModal.isOpen}
        title={poConfirmModal.title}
        message={poConfirmModal.message}
        variant="primary"
        confirmLabel="Place PO"
        onConfirm={poConfirmModal.action}
        onCancel={() => setPoConfirmModal((prev) => ({ ...prev, isOpen: false }))}
      />
    </div>
  );
};
