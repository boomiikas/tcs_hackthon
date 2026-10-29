import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShoppingBag,
  Clock,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  ArrowLeft,
  QrCode,
  Tag,
  AlertCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { useCanteen } from '../context/CanteenContext';

export const SurplusMarketplacePage: React.FC = () => {
  const { selectedCanteen, addToast } = useCanteen();
  const navigate = useNavigate();

  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedMeal, setSelectedMeal] = useState<any>(null);
  const [portionsToReserve, setPortionsToReserve] = useState<number>(1);
  const [activeReservation, setActiveReservation] = useState<any>(null);
  const [studentId, setStudentId] = useState<string>('STU-2024-8841');

  const loadMarketplace = () => {
    setLoading(true);
    api.getSurplusListings(undefined, true) // active listings
      .then((res) => {
        setItems(res || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Marketplace error:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadMarketplace();
  }, []);

  const handleReserve = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMeal) return;

    api.reserveSurplus({
      listing_id: selectedMeal.id,
      student_id: studentId,
      portions: portionsToReserve,
    })
      .then((res) => {
        setActiveReservation(res);
        setSelectedMeal(null);
        addToast(`Reservation confirmed for ${portionsToReserve} portion(s)!`, 'success');
        loadMarketplace();
      })
      .catch((err) => {
        addToast(`Reservation failed: ${err.message}`, 'error');
      });
  };

  return (
    <div style={{ backgroundColor: '#f6f7f6', minHeight: '100vh', paddingBottom: '60px' }}>
      {/* Student Portal Header */}
      <header
        style={{
          backgroundColor: '#ffffff',
          borderBottom: '1px solid var(--border-light)',
          padding: '16px 24px',
          position: 'sticky',
          top: 0,
          zIndex: 30,
        }}
      >
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate('/dashboard')}>
              <ArrowLeft size={14} />
              <span>Back to Admin</span>
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--primary-600)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: '15px',
                }}
              >
                CQ
              </div>
              <div>
                <span style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)' }}>
                  Campus Green Plate • Surplus Marketplace
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>
                  Fresh chef-prepared campus meals at 40-60% discount
                </span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span className="badge badge-positive" style={{ padding: '4px 10px' }}>
              ● Live Kitchen Flash Sale
            </span>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <div style={{ maxWidth: '1200px', margin: '24px auto', padding: '0 20px' }}>
        <div
          style={{
            backgroundColor: 'var(--primary-600)',
            color: '#ffffff',
            borderRadius: 'var(--radius-lg)',
            padding: '28px 32px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          <div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'rgba(255,255,255,0.15)', padding: '4px 10px', borderRadius: 'var(--radius-full)', fontSize: '12px', fontWeight: 500, marginBottom: '10px' }}>
              <Sparkles size={13} />
              <span>Zero Food Waste Campus Initiative</span>
            </div>
            <h1 style={{ fontSize: '26px', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: '6px' }}>
              Fresh, High-Nutrition Meals. Discounted Prices.
            </h1>
            <p style={{ fontSize: '14px', color: 'rgba(255,255,255,0.85)', maxWidth: '640px' }}>
              All meals are prepared fresh today and safety-certified at ≥ 65°C. Reserve online and collect at the designated campus express counter before the deadline.
            </p>
          </div>
          <ShieldCheck size={72} color="rgba(255,255,255,0.25)" />
        </div>
      </div>

      {/* Marketplace Meals Grid */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 className="section-heading" style={{ fontSize: '18px' }}>Available Surplus Meals</h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Showing verified active batches across campus cafeterias
            </div>
          </div>
          <span className="badge badge-neutral">{items.length} items available</span>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
            Loading available surplus meals...
          </div>
        ) : items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', backgroundColor: '#ffffff', borderRadius: 'var(--radius-md)' }}>
            <ShoppingBag size={32} color="var(--text-muted)" style={{ margin: '0 auto 12px auto' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>All Surplus Meals Recovered!</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Check back at the end of the next meal shift (around 3:00 PM and 8:30 PM).
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
            {items.map((meal) => {
              const remaining = meal.quantity_available - meal.quantity_reserved;
              if (remaining <= 0) return null;

              return (
                <div
                  key={meal.id}
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-lg)',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    boxShadow: 'var(--shadow-sm)',
                    transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                  }}
                >
                  {/* Meal Photo Header */}
                  <div style={{ height: '160px', width: '100%', position: 'relative', overflow: 'hidden' }}>
                    <img
                      src={meal.image_url || 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80'}
                      alt={meal.food_name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                    <div
                      style={{
                        position: 'absolute',
                        top: '10px',
                        left: '10px',
                        backgroundColor: 'var(--warning-600)',
                        color: '#ffffff',
                        padding: '3px 8px',
                        borderRadius: 'var(--radius-full)',
                        fontSize: '11px',
                        fontWeight: 700,
                      }}
                    >
                      {meal.discount_percent}% OFF
                    </div>
                    <div
                      style={{
                        position: 'absolute',
                        top: '10px',
                        right: '10px',
                        backgroundColor: 'rgba(0,0,0,0.65)',
                        color: '#ffffff',
                        padding: '3px 8px',
                        borderRadius: 'var(--radius-full)',
                        fontSize: '11px',
                        fontWeight: 500,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <Clock size={11} />
                      <span>Until {meal.collection_deadline}</span>
                    </div>
                  </div>

                  {/* Meal Details */}
                  <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', flex: 1, gap: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <span
                          className={`badge ${
                            meal.dietary_type === 'Vegan'
                              ? 'badge-positive'
                              : meal.dietary_type === 'Vegetarian'
                              ? 'badge-info'
                              : 'badge-warning'
                          }`}
                          style={{ fontSize: '10px', marginBottom: '4px' }}
                        >
                          {meal.dietary_type}
                        </span>
                        <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                          {meal.food_name}
                        </h3>
                      </div>
                    </div>

                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {meal.portion_size} • Batch {meal.batch_code}
                    </div>

                    {/* Allergens & Safety Tag */}
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Tag size={12} color="var(--text-muted)" />
                      <span>Allergens: {meal.allergens}</span>
                    </div>

                    {/* Price & Action */}
                    <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ textDecoration: 'line-through', fontSize: '12px', color: 'var(--text-muted)' }}>
                          ₹{meal.original_price}
                        </div>
                        <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--primary-700)' }}>
                          ₹{meal.discounted_price}
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '11px', color: 'var(--positive-700)', fontWeight: 600, marginBottom: '4px' }}>
                          {remaining} left
                        </div>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => {
                            setSelectedMeal(meal);
                            setPortionsToReserve(1);
                          }}
                        >
                          Reserve Meal
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Reservation Modal */}
      {selectedMeal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShoppingBag size={18} color="var(--primary-600)" />
                <h2 className="section-heading">Reserve Surplus Meal</h2>
              </div>
              <button className="btn-icon" onClick={() => setSelectedMeal(null)}>
                ✕
              </button>
            </div>

            <form onSubmit={handleReserve} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ padding: '12px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {selectedMeal.food_name}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {selectedMeal.portion_size} • Collection by {selectedMeal.collection_deadline}
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
                  <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--primary-700)' }}>
                    ₹{selectedMeal.discounted_price}
                  </span>
                  <span style={{ textDecoration: 'line-through', fontSize: '12px', color: 'var(--text-muted)' }}>
                    ₹{selectedMeal.original_price}
                  </span>
                  <span className="badge badge-warning">{selectedMeal.discount_percent}% Discount</span>
                </div>
              </div>

              <div>
                <label className="form-label">Student / Campus ID</label>
                <input
                  type="text"
                  className="form-input"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="form-label">Number of Portions (Max 3 per student)</label>
                <input
                  type="number"
                  min="1"
                  max={Math.min(3, selectedMeal.quantity_available - selectedMeal.quantity_reserved)}
                  className="form-input"
                  value={portionsToReserve}
                  onChange={(e) => setPortionsToReserve(Number(e.target.value))}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', backgroundColor: 'var(--primary-50)', borderRadius: '6px', fontSize: '13px', fontWeight: 600 }}>
                <span>Total Due at Counter:</span>
                <span style={{ color: 'var(--primary-800)' }}>
                  ₹{(portionsToReserve * selectedMeal.discounted_price).toFixed(2)}
                </span>
              </div>

              <div style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                ⚠️ Please pick up your meal at Counter B before {selectedMeal.collection_deadline}. Uncollected reservations are cancelled at deadline to comply with food safety regulations.
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '10px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setSelectedMeal(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Confirm Reservation Pass
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Pickup Pass Confirmation Modal */}
      {activeReservation && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ textAlign: 'center' }}>
            <CheckCircle2 size={42} color="var(--positive-600)" style={{ margin: '0 auto 10px auto' }} />
            <h2 className="section-heading" style={{ fontSize: '18px' }}>Meal Reservation Confirmed!</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Present this pass at the CanteenIQ Express Pickup Counter.
            </p>

            <div
              style={{
                margin: '20px 0',
                padding: '16px',
                border: '2px dashed var(--primary-500)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--primary-50)',
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--primary-700)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Pickup Verification Code
              </div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--primary-800)', letterSpacing: '0.05em', margin: '6px 0' }}>
                {activeReservation.reservation_id}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--primary-700)' }}>
                {activeReservation.portions} Portion(s) • Total: ₹{activeReservation.total_amount}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--risk-700)', fontWeight: 600, marginTop: '8px' }}>
                Pickup Deadline: {activeReservation.collection_deadline}
              </div>
            </div>

            <button className="btn btn-primary" onClick={() => setActiveReservation(null)} style={{ width: '100%' }}>
              Got It / Return to Marketplace
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
