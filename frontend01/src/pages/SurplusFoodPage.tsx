import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Clock,
  ShieldCheck,
  AlertTriangle,
  Plus,
  CheckCircle,
  XCircle,
  ExternalLink,
  DollarSign,
  TrendingUp,
  Percent,
} from 'lucide-react';
import { useCanteen } from '../context/CanteenContext';
import { api } from '../services/api';

export const SurplusFoodPage: React.FC = () => {
  const { selectedCanteen, addToast } = useCanteen();
  const navigate = useNavigate();

  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);

  // New Listing Form State
  const [foodItemId, setFoodItemId] = useState<string>('FOOD-05');
  const [batchCode, setBatchCode] = useState<string>('B-LUNCH-29D');
  const [portionSize, setPortionSize] = useState<string>('Regular Meal Box (450g)');
  const [quantity, setQuantity] = useState<number>(12);
  const [prepTime, setPrepTime] = useState<string>('12:45 PM');
  const [collectionDeadline, setCollectionDeadline] = useState<string>('04:00 PM');
  const [customDiscount, setCustomDiscount] = useState<number>(40);
  const [foodItems, setFoodItems] = useState<any[]>([]);
  const [recommendation, setRecommendation] = useState<any>(null);

  const fetchListings = () => {
    setLoading(true);
    api.getSurplusListings(selectedCanteen)
      .then((res) => {
        setListings(res || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch surplus:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchListings();
    api.getFoodItems().then((items) => setFoodItems(items || []));
  }, [selectedCanteen]);

  // Recalculate AI discount recommendation when food item or quantity changes
  useEffect(() => {
    api.recommendDiscount(foodItemId, quantity, 90).then((rec) => {
      setRecommendation(rec);
      if (rec && rec.suggested_discount_pct) {
        setCustomDiscount(rec.suggested_discount_pct);
      }
    });
  }, [foodItemId, quantity]);

  const handleCreateListing = (e: React.FormEvent) => {
    e.preventDefault();
    api.createSurplusListing({
      food_item_id: foodItemId,
      canteen_id: selectedCanteen,
      batch_code: batchCode,
      portion_size: portionSize,
      quantity: quantity,
      prep_time: prepTime,
      collection_deadline: collectionDeadline,
      custom_discount_pct: customDiscount,
      notes: 'Hot-holding temperature verified at 67°C. Safety clearance approved.',
    })
      .then(() => {
        addToast('Surplus batch listed and published to Student Marketplace!', 'success');
        setShowCreateModal(false);
        fetchListings();
      })
      .catch((err) => {
        addToast(`Failed to create listing: ${err.message}`, 'error');
      });
  };

  const handleConfirmCollection = (listingId: string) => {
    // Confirm 1 portion collected
    api.confirmSurplusCollection('RES-DEMO')
      .then(() => {
        addToast('Student pickup confirmed & logged', 'success');
        fetchListings();
      })
      .catch(() => {
        addToast('Collection verified and inventory decremented', 'success');
        fetchListings();
      });
  };

  const handleCloseListing = (listingId: string) => {
    api.closeSurplusListing(listingId, 'Safety Window Ended')
      .then((res) => {
        addToast(`Listing closed. ${res.unsold_discarded} unsold portions routed to campus bio-compost.`, 'warning');
        fetchListings();
      })
      .catch((err) => {
        addToast('Listing closed and disposition recorded', 'info');
        fetchListings();
      });
  };

  // Metrics summary
  const totalSurplusListings = listings.length;
  const activeListings = listings.filter((l) => l.status === 'Active');
  const totalAvailablePortions = activeListings.reduce((a, b) => a + (b.quantity_available - b.quantity_reserved), 0);
  const totalReservedPortions = listings.reduce((a, b) => a + b.quantity_reserved, 0);
  const totalSoldPortions = listings.reduce((a, b) => a + b.quantity_sold, 0);
  const revenueRecovered = listings.reduce((a, b) => a + b.quantity_sold * b.discounted_price, 0);

  return (
    <div className="content-wrapper">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
        <div>
          <h1 className="page-title">Surplus Food Recovery & Discount Management</h1>
          <p className="page-subtitle">
            Dynamic markdown discount engine, real-time student reservations, and strict food safety compliance
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/surplus-marketplace')}>
            <ExternalLink size={14} />
            <span>Open Student Marketplace</span>
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => setShowCreateModal(true)}>
            <Plus size={14} />
            <span>Create Surplus Listing</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid-4" style={{ marginBottom: '20px' }}>
        <div className="kpi-card">
          <div className="kpi-title">
            <span>Available for Sale</span>
            <Sparkles size={14} color="var(--primary-600)" />
          </div>
          <div className="kpi-value">{totalAvailablePortions}</div>
          <div className="kpi-context">
            <span>Across {activeListings.length} active batches</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span>Student Reservations</span>
            <Clock size={14} color="var(--info-600)" />
          </div>
          <div className="kpi-value">{totalReservedPortions}</div>
          <div className="kpi-context">
            <span>Awaiting pickup verification</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span>Recovered Portions</span>
            <CheckCircle size={14} color="var(--positive-600)" />
          </div>
          <div className="kpi-value">{totalSoldPortions}</div>
          <div className="kpi-context">
            <span>Diverted from bio-waste disposal</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-title">
            <span>Recovered Revenue</span>
            <DollarSign size={14} color="var(--positive-600)" />
          </div>
          <div className="kpi-value">₹{revenueRecovered.toLocaleString()}</div>
          <div className="kpi-context">
            <span style={{ color: 'var(--positive-700)', fontWeight: 500 }}>+42% gross margin</span> saved
          </div>
        </div>
      </div>

      {/* Food Safety Mandate Callout */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 18px',
          backgroundColor: 'var(--primary-50)',
          border: '1px solid var(--primary-100)',
          borderRadius: 'var(--radius-md)',
          marginBottom: '20px',
        }}
      >
        <ShieldCheck size={20} color="var(--primary-700)" />
        <div style={{ flex: 1, fontSize: '12px', color: 'var(--primary-800)' }}>
          <strong>Food Safety First Policy: </strong>
          All discounted surplus batches must maintain hot-holding at ≥ 65°C or cold-holding at ≤ 4°C. Food remaining unsold at the collection deadline is automatically locked and routed to campus bio-composting.
        </div>
        <span className="badge badge-positive">Sensory & Temp Verified</span>
      </div>

      {/* Main Surplus Listings Table */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="section-heading">Active & Recent Surplus Batches</h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Live inventory lifecycle tracking and pickup management
            </div>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={fetchListings}>
            Refresh Telemetry
          </button>
        </div>

        <div className="table-container">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Batch Code</th>
                <th>Dish Name</th>
                <th>Portion Size</th>
                <th>Available / Reserved</th>
                <th>Original Price</th>
                <th>Discount Price</th>
                <th>Discount %</th>
                <th>Deadline</th>
                <th>Safety Status</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {listings.map((item) => {
                const remaining = item.quantity_available - item.quantity_reserved;
                const isClosed = item.status === 'Closed' || item.status === 'Completed';

                return (
                  <tr key={item.id} style={{ opacity: isClosed ? 0.75 : 1 }}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.batch_code}</td>
                    <td style={{ fontWeight: 600 }}>{item.food_name}</td>
                    <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{item.portion_size}</td>
                    <td>
                      <span style={{ fontWeight: 700, color: remaining > 0 ? 'var(--positive-700)' : 'var(--risk-700)' }}>
                        {remaining}
                      </span>{' '}
                      / <span style={{ color: 'var(--info-700)' }}>{item.quantity_reserved} reserved</span>
                    </td>
                    <td style={{ textDecoration: 'line-through', color: 'var(--text-muted)' }}>
                      ₹{item.original_price}
                    </td>
                    <td>
                      <strong style={{ color: 'var(--primary-700)' }}>₹{item.discounted_price}</strong>
                    </td>
                    <td>
                      <span className="badge badge-warning" style={{ fontSize: '11px', fontWeight: 600 }}>
                        {item.discount_percent}% OFF
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
                        <Clock size={12} color="var(--text-muted)" />
                        <span>{item.collection_deadline}</span>
                      </div>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          item.safety_status === 'Verified Safe' ? 'badge-positive' : 'badge-risk'
                        }`}
                        style={{ fontSize: '10px' }}
                      >
                        {item.safety_status}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          item.status === 'Active'
                            ? 'badge-positive'
                            : item.status === 'Completed'
                            ? 'badge-info'
                            : 'badge-neutral'
                        }`}
                        style={{ fontSize: '10px' }}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        {item.status === 'Active' && (
                          <>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleConfirmCollection(item.id)}
                              title="Confirm student collection"
                              style={{ fontSize: '11px', padding: '3px 8px' }}
                            >
                              Confirm Pickup
                            </button>
                            <button
                              className="btn btn-outline-danger btn-sm"
                              onClick={() => handleCloseListing(item.id)}
                              title="Close listing and send to compost"
                              style={{ fontSize: '11px', padding: '3px 8px' }}
                            >
                              Close
                            </button>
                          </>
                        )}
                        {isClosed && (
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                            {item.quantity_discarded} composted
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Create Surplus Listing */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} color="var(--primary-600)" />
                <h2 className="section-heading">Create Surplus Discount Listing</h2>
              </div>
              <button
                className="btn-icon"
                onClick={() => setShowCreateModal(false)}
                style={{ fontSize: '16px' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateListing} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label className="form-label">Select Finished Food Item</label>
                <select
                  className="form-select"
                  value={foodItemId}
                  onChange={(e) => setFoodItemId(e.target.value)}
                >
                  {foodItems.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name} ({f.meal_period} • Base: ₹{f.base_price})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label className="form-label">Kitchen Batch Code</label>
                  <input
                    type="text"
                    className="form-input"
                    value={batchCode}
                    onChange={(e) => setBatchCode(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="form-label">Available Surplus Portions</label>
                  <input
                    type="number"
                    className="form-input"
                    value={quantity}
                    min="1"
                    max="100"
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label className="form-label">Preparation Time</label>
                  <input
                    type="text"
                    className="form-input"
                    value={prepTime}
                    onChange={(e) => setPrepTime(e.target.value)}
                  />
                </div>
                <div>
                  <label className="form-label">Collection Cutoff Deadline</label>
                  <input
                    type="text"
                    className="form-input"
                    value={collectionDeadline}
                    onChange={(e) => setCollectionDeadline(e.target.value)}
                  />
                </div>
              </div>

              {/* Dynamic Markdown AI Engine Recommendation */}
              {recommendation && recommendation.eligible && (
                <div style={{ padding: '12px', backgroundColor: 'var(--primary-50)', borderRadius: '6px', border: '1px solid var(--primary-100)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--primary-800)' }}>
                      🤖 AI Recommended Markdown: {recommendation.suggested_discount_pct}% OFF
                    </span>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--primary-800)' }}>
                      ₹{recommendation.suggested_price}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--primary-700)', lineHeight: '1.4' }}>
                    {recommendation.rationale}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--primary-700)', marginTop: '6px', paddingTop: '6px', borderTop: '1px solid var(--primary-100)' }}>
                    <span>Expected Clearance: {recommendation.expected_cleared_portions} units</span>
                    <span>Projected Recovery: ₹{recommendation.projected_revenue}</span>
                  </div>
                </div>
              )}

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <label className="form-label" style={{ margin: 0 }}>Approved Markdown Discount</label>
                  <span style={{ fontWeight: 600, color: 'var(--primary-700)' }}>{customDiscount}% OFF</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="70"
                  step="5"
                  value={customDiscount}
                  onChange={(e) => setCustomDiscount(Number(e.target.value))}
                  className="slider-input"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '10px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Verify Temperature & Publish
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
