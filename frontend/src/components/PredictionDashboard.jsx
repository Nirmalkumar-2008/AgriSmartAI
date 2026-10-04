import React, { useState, useEffect, useRef } from 'react';

const PredictionDashboard = ({ theme = 'light', onToggleTheme }) => {
  const [formData, setFormData] = useState({
    city: 'Bengaluru',
    N: 90,
    P: 42,
    K: 43,
    ph: 6.8,
    soil_moisture: 45,
    selected_crop: ''
  });

  const [weatherData, setWeatherData] = useState(null);
  const [weatherStatus, setWeatherStatus] = useState({ state: 'idle', message: '' });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [expandedInsights, setExpandedInsights] = useState({});
  const [activeExplainTab, setActiveExplainTab] = useState('crop');

  const debounceTimerRef = useRef(null);
  const isDark = theme === 'dark';

  const themeColors = {
    bg: isDark ? '#0F172A' : '#F8FAFC',
    cardBg: isDark ? '#1E293B' : '#FFFFFF',
    cardBorder: isDark ? '#334155' : '#E2E8F0',
    textPrimary: isDark ? '#F8FAFC' : '#111827',
    textSecondary: isDark ? '#94A3B8' : '#475569',
    accentPrimary: isDark ? '#22C55E' : '#16A34A',
    inputBg: isDark ? '#0F172A' : '#FFFFFF',
    inputBorder: isDark ? '#475569' : '#CBD5E1',
    metricBg: isDark ? '#0F172A' : '#F1F5F9'
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (name === 'city') {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

      if (value && value.trim().length > 2) {
        setWeatherStatus({ state: 'loading', message: '⏳ Loading weather...' });
        debounceTimerRef.current = setTimeout(() => {
          fetchWeatherForCity(value.trim());
        }, 1000);
      } else {
        setWeatherData(null);
        setWeatherStatus({ state: 'idle', message: '' });
      }
    }
  };

  const handleCityBlur = () => {
    if (formData.city && formData.city.trim().length > 2) {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      fetchWeatherForCity(formData.city.trim());
    }
  };

  const fetchWeatherForCity = async (cityName) => {
    if (!cityName) return;
    setWeatherStatus({ state: 'loading', message: '⏳ Loading weather...' });

    try {
      const response = await fetch(`/weather/${encodeURIComponent(cityName)}`);
      const data = await response.json();

      if (response.ok && data.temperature !== undefined) {
        setWeatherData(data);
        setWeatherStatus({ state: 'success', message: '✓ Live weather updated' });
      } else if (response.status === 404 || (data.detail && data.detail.includes('not found'))) {
        setWeatherData(null);
        setWeatherStatus({ state: 'error', message: '❌ City not found' });
      } else {
        setWeatherData(null);
        setWeatherStatus({ state: 'error', message: '❌ Unable to connect' });
      }
    } catch (err) {
      setWeatherData(null);
      setWeatherStatus({ state: 'error', message: '❌ Unable to connect' });
    }
  };

  useEffect(() => {
    fetchWeatherForCity('Bengaluru');
  }, []);

  const toggleInsight = (index) => {
    setExpandedInsights((prev) => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload = {
      city: formData.city.trim(),
      N: parseFloat(formData.N),
      P: parseFloat(formData.P),
      K: parseFloat(formData.K),
      ph: parseFloat(formData.ph),
      soil_moisture: parseFloat(formData.soil_moisture),
      selected_crop: formData.selected_crop.trim() !== '' ? formData.selected_crop.trim() : null
    };

    if (weatherData) {
      payload.temperature = weatherData.temperature;
      payload.humidity = weatherData.humidity;
      payload.rainfall = weatherData.rainfall;
    }

    try {
      const response = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || data.detail || (data.details ? data.details.join(', ') : 'Prediction request failed'));
      }

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getYieldBadge = (val) => {
    if (val >= 8.0) return { label: '🌟 Excellent Yield Potential', bg: '#DCFCE7', text: '#15803D', border: '#86EFAC' };
    if (val >= 5.0) return { label: '✅ Good Yield Potential', bg: '#DBEAFE', text: '#1D4ED8', border: '#93C5FD' };
    if (val >= 3.0) return { label: '⚠️ Average Yield Potential', bg: '#FEF9C3', text: '#A16207', border: '#FDE047' };
    return { label: '🛑 Poor Yield Potential', bg: '#FEE2E2', text: '#B91C1C', border: '#FCA5A5' };
  };

  const getSeverityStyle = (severity) => {
    switch (severity) {
      case 'warning':
        return { bg: isDark ? '#451A1A' : '#FEE2E2', border: '#EF4444', icon: '🚨', titleColor: isDark ? '#FCA5A5' : '#991B1B' };
      case 'caution':
        return { bg: isDark ? '#422006' : '#FEF3C7', border: '#F59E0B', icon: '⚠️', titleColor: isDark ? '#FDE68A' : '#92400E' };
      case 'success':
        return { bg: isDark ? '#064E3B' : '#DCFCE7', border: '#22C55E', icon: '✅', titleColor: isDark ? '#A7F3D0' : '#166534' };
      case 'info':
      default:
        return { bg: isDark ? '#1E3A8A' : '#DBEAFE', border: '#3B82F6', icon: 'ℹ️', titleColor: isDark ? '#BFDBFE' : '#1E40AF' };
    }
  };

  return (
    <div style={{ background: themeColors.bg, color: themeColors.textPrimary, transition: 'all 0.3s ease', minHeight: '100vh', padding: '2rem 1rem' }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        
        {/* PAGE HEADER */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <div>
            <h1 style={{ fontSize: '2.2rem', fontWeight: 800, margin: 0, color: themeColors.textPrimary }}>
              🌾 Crop Advisory Engine
            </h1>
            <p style={{ color: themeColors.textSecondary, fontSize: '0.95rem', marginTop: '0.3rem' }}>
              Precision Agriculture Decision Support System
            </p>
          </div>

          <button
            onClick={onToggleTheme}
            style={{
              background: themeColors.cardBg,
              border: `1px solid ${themeColors.cardBorder}`,
              color: themeColors.textPrimary,
              padding: '0.6rem 1.2rem',
              borderRadius: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <span>{isDark ? '☀ Light Mode' : '🌙 Dark Mode'}</span>
          </button>
        </div>

        {/* TWO-COLUMN LAYOUT */}
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 420px) 1fr', gap: '2rem' }}>
          
          {/* LEFT PANEL: FARMER INPUTS */}
          <div style={{ background: themeColors.cardBg, border: `1px solid ${themeColors.cardBorder}`, borderRadius: '20px', padding: '1.8rem', boxShadow: '0 4px 20px rgba(0,0,0,0.05)', height: 'fit-content' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: '0 0 1.2rem 0', color: themeColors.textPrimary, display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span>⚙️</span> Farmer Inputs
            </h2>

            {/* LOCATION & WEATHER */}
            <div style={{ marginBottom: '1.5rem', padding: '1rem', background: themeColors.metricBg, borderRadius: '14px', border: `1px solid ${themeColors.cardBorder}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                <label style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: themeColors.textSecondary }}>
                  📍 City / Region:
                </label>
                <button
                  type="button"
                  onClick={() => fetchWeatherForCity(formData.city)}
                  style={{ background: themeColors.accentPrimary, color: '#FFF', border: 'none', padding: '0.3rem 0.7rem', borderRadius: '8px', fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  Fetch Weather
                </button>
              </div>

              <input
                type="text"
                name="city"
                placeholder="e.g. Chennai, Bengaluru, Delhi"
                value={formData.city}
                onChange={handleChange}
                onBlur={handleCityBlur}
                required
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: `1px solid ${themeColors.inputBorder}`, background: themeColors.inputBg, color: themeColors.textPrimary, fontWeight: 600, fontSize: '0.9rem' }}
              />

              {weatherStatus.message && (
                <div style={{ marginTop: '0.4rem', fontSize: '0.8rem', fontWeight: 700, color: weatherStatus.state === 'success' ? '#22C55E' : '#EF4444' }}>
                  {weatherStatus.message}
                </div>
              )}

              {/* READ-ONLY WEATHER METRICS GRID */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.8rem' }}>
                <div style={{ background: themeColors.cardBg, padding: '0.5rem', borderRadius: '8px', border: `1px solid ${themeColors.cardBorder}` }}>
                  <span style={{ fontSize: '0.65rem', fontWeight: 700, color: themeColors.textSecondary, display: 'block' }}>TEMP</span>
                  <span style={{ fontWeight: 800, fontSize: '0.85rem' }}>{weatherData ? `${weatherData.temperature} °C` : '--'}</span>
                </div>
                <div style={{ background: themeColors.cardBg, padding: '0.5rem', borderRadius: '8px', border: `1px solid ${themeColors.cardBorder}` }}>
                  <span style={{ fontSize: '0.65rem', fontWeight: 700, color: themeColors.textSecondary, display: 'block' }}>HUMIDITY</span>
                  <span style={{ fontWeight: 800, fontSize: '0.85rem' }}>{weatherData ? `${weatherData.humidity} %` : '--'}</span>
                </div>
                <div style={{ background: themeColors.cardBg, padding: '0.5rem', borderRadius: '8px', border: `1px solid ${themeColors.cardBorder}` }}>
                  <span style={{ fontSize: '0.65rem', fontWeight: 700, color: themeColors.textSecondary, display: 'block' }}>RAINFALL</span>
                  <span style={{ fontWeight: 800, fontSize: '0.85rem' }}>{weatherData ? `${weatherData.rainfall} mm` : '--'}</span>
                </div>
                <div style={{ background: themeColors.cardBg, padding: '0.5rem', borderRadius: '8px', border: `1px solid ${themeColors.cardBorder}` }}>
                  <span style={{ fontSize: '0.65rem', fontWeight: 700, color: themeColors.textSecondary, display: 'block' }}>WIND</span>
                  <span style={{ fontWeight: 800, fontSize: '0.85rem' }}>{weatherData ? `${weatherData.wind_speed} m/s` : '--'}</span>
                </div>
              </div>
            </div>

            {/* FORM FOR SOIL PARAMETERS & CROP TARGET */}
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
              <div>
                <h3 style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', color: themeColors.textSecondary, marginBottom: '0.6rem' }}>
                  🌱 Soil Parameters
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
                  <div>
                    <label style={{ fontSize: '0.7rem', fontWeight: 700 }}>N (mg/kg):</label>
                    <input type="number" name="N" value={formData.N} onChange={handleChange} required style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: `1px solid ${themeColors.inputBorder}`, background: themeColors.inputBg, color: themeColors.textPrimary }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.7rem', fontWeight: 700 }}>P (mg/kg):</label>
                    <input type="number" name="P" value={formData.P} onChange={handleChange} required style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: `1px solid ${themeColors.inputBorder}`, background: themeColors.inputBg, color: themeColors.textPrimary }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.7rem', fontWeight: 700 }}>K (mg/kg):</label>
                    <input type="number" name="K" value={formData.K} onChange={handleChange} required style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: `1px solid ${themeColors.inputBorder}`, background: themeColors.inputBg, color: themeColors.textPrimary }} />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <div>
                    <label style={{ fontSize: '0.7rem', fontWeight: 700 }}>Soil pH:</label>
                    <input type="number" step="0.1" name="ph" value={formData.ph} onChange={handleChange} required style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: `1px solid ${themeColors.inputBorder}`, background: themeColors.inputBg, color: themeColors.textPrimary }} />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.7rem', fontWeight: 700, color: '#F59E0B' }}>Soil Moisture (%):</label>
                    <input type="number" name="soil_moisture" value={formData.soil_moisture} onChange={handleChange} required style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', border: '1px solid #F59E0B', background: isDark ? '#312E81' : '#FFFBEB', color: themeColors.textPrimary }} />
                  </div>
                </div>
              </div>

              <div>
                <h3 style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', color: themeColors.textSecondary, marginBottom: '0.6rem' }}>
                  🌾 Crop Selection (Optional)
                </h3>
                <input
                  type="text"
                  name="selected_crop"
                  placeholder="e.g. Rice, Maize, Wheat"
                  value={formData.selected_crop}
                  onChange={handleChange}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', border: `1px solid ${themeColors.inputBorder}`, background: themeColors.inputBg, color: themeColors.textPrimary }}
                />
                <p style={{ fontSize: '0.75rem', color: themeColors.textSecondary, marginTop: '0.4rem', lineHeight: '1.4' }}>
                  "If no crop is selected, the AI automatically recommends the best crop and predicts its yield."
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  background: 'linear-gradient(135deg, #16A34A 0%, #15803D 100%)',
                  color: '#FFFFFF',
                  padding: '1rem',
                  borderRadius: '14px',
                  fontWeight: 800,
                  fontSize: '1rem',
                  border: 'none',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(22, 163, 74, 0.3)',
                  transition: 'all 0.2s ease'
                }}
              >
                {loading ? 'Executing AI Recommendation Fusion...' : 'Run Prediction ⚡'}
              </button>
            </form>
          </div>

          {/* RIGHT PANEL: PREDICTION RESULTS CARDS */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.8rem' }}>
            {error && (
              <div style={{ padding: '1.2rem', background: '#FEE2E2', color: '#991B1B', borderRadius: '16px', border: '1px solid #EF4444', fontWeight: 700 }}>
                🚨 <strong>Error:</strong> {error}
              </div>
            )}

            {!result && !loading && (
              <div style={{ background: themeColors.cardBg, border: `1px solid ${themeColors.cardBorder}`, borderRadius: '20px', padding: '4rem 2rem', textAlign: 'center', color: themeColors.textSecondary }}>
                <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>🌾</div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: themeColors.textPrimary }}>No Crop Prediction Advisory Generated Yet</h3>
                <p style={{ fontSize: '0.9rem', maxWidth: '450px', margin: '0.5rem auto 0 auto' }}>Fetch weather and click "Run Prediction" to generate AI advisories.</p>
              </div>
            )}

            {loading && (
              <div style={{ background: themeColors.cardBg, border: `1px solid ${themeColors.cardBorder}`, borderRadius: '20px', padding: '4rem 2rem', textAlign: 'center' }}>
                <div style={{ width: '50px', height: '50px', border: '4px solid #16A34A', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 1.5rem auto' }}></div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: themeColors.textPrimary }}>Running Machine Learning Inference...</h3>
                <p style={{ fontSize: '0.85rem', color: themeColors.textSecondary }}>Computing SHAP values & evaluating micro-climate rules.</p>
              </div>
            )}

            {result && !loading && (
              <>
                {/* CARD 1: 🌱 CROP RECOMMENDATION */}
                <div style={{ background: themeColors.cardBg, border: `1px solid ${themeColors.cardBorder}`, borderRadius: '20px', padding: '1.8rem', boxShadow: '0 4px 20px rgba(0,0,0,0.05)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.2rem' }}>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: themeColors.textPrimary, display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <span>🌱</span> Crop Recommendation
                    </h2>
                    <span style={{ background: result.crop_source === 'recommended' ? '#DCFCE7' : '#DBEAFE', color: result.crop_source === 'recommended' ? '#166534' : '#1E40AF', padding: '0.4rem 0.8rem', borderRadius: '20px', fontWeight: 800, fontSize: '0.75rem' }}>
                      {result.crop_source === 'recommended' ? '🤖 Automatic Mode' : '👤 User Selected Mode'}
                    </span>
                  </div>

                  {/* HIGHLIGHT RECOMMENDED CROP */}
                  <div style={{ padding: '1rem 1.2rem', background: themeColors.metricBg, borderRadius: '14px', border: `1px solid ${themeColors.cardBorder}`, marginBottom: '1.2rem', display: 'flex', justifyBetween: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: themeColors.textSecondary, textTransform: 'uppercase' }}>Recommended Crop Target</span>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: themeColors.accentPrimary, marginTop: '0.2rem' }}>
                        {result.recommended_crop} ({result.recommended_crop_confidence}% confidence)
                      </div>
                    </div>

                    <div style={{ fontSize: '0.85rem', fontWeight: 700, padding: '0.5rem 1rem', background: themeColors.cardBg, borderRadius: '10px', border: `1px solid ${themeColors.cardBorder}` }}>
                      Evaluation Target: <strong style={{ color: themeColors.accentPrimary }}>{result.prediction_crop}</strong>
                    </div>
                  </div>

                  {/* TOP 3 RANKED LIST */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                    {result.top_3_recommendations && result.top_3_recommendations.map((rec) => {
                      const isRank1 = rec.rank === 1;
                      const medal = rec.rank === 1 ? '🥇' : rec.rank === 2 ? '🥈' : '🥉';
                      return (
                        <div key={rec.rank} style={{ padding: '1rem', background: isRank1 ? (isDark ? '#064E3B' : '#F0FDF4') : themeColors.metricBg, border: `1px solid ${isRank1 ? '#22C55E' : themeColors.cardBorder}`, borderRadius: '14px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>{medal} Rank {rec.rank}</span>
                            {isRank1 && <span style={{ background: '#22C55E', color: '#FFF', fontSize: '0.65rem', padding: '0.2rem 0.5rem', borderRadius: '8px', fontWeight: 800 }}>TOP PICK</span>}
                          </div>
                          <div style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: '0.4rem', color: themeColors.textPrimary }}>
                            {rec.crop} — {rec.confidence}%
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* CARDS GRID FOR YIELD, FERTILIZER, IRRIGATION */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
                  
                  {/* CARD 2: 📈 YIELD PREDICTION */}
                  <div style={{ background: themeColors.cardBg, border: `1px solid ${themeColors.cardBorder}`, borderRadius: '20px', padding: '1.5rem', boxShadow: '0 4px 20px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column', justifyBetween: 'space-between' }}>
                    <div>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0 0 1rem 0', color: themeColors.textPrimary, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span>📈</span> Yield Prediction
                      </h3>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: themeColors.textSecondary, textTransform: 'uppercase' }}>Expected Yield</span>
                      <div style={{ fontSize: '2rem', fontWeight: 900, color: themeColors.accentPrimary, margin: '0.3rem 0 1rem 0' }}>
                        {result.predicted_yield_tons_per_ha} <span style={{ fontSize: '1rem', fontWeight: 700 }}>tons/ha</span>
                      </div>
                    </div>

                    {(() => {
                      const b = getYieldBadge(result.predicted_yield_tons_per_ha);
                      return (
                        <div style={{ padding: '0.6rem 0.8rem', background: b.bg, color: b.text, border: `1px solid ${b.border}`, borderRadius: '12px', fontWeight: 800, fontSize: '0.85rem', textAlign: 'center' }}>
                          Performance: {b.label}
                        </div>
                      );
                    })()}
                  </div>

                  {/* CARD 3: 🧪 FERTILIZER RECOMMENDATION */}
                  <div style={{ background: themeColors.cardBg, border: `1px solid ${themeColors.cardBorder}`, borderRadius: '20px', padding: '1.5rem', boxShadow: '0 4px 20px rgba(0,0,0,0.05)' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0 0 1rem 0', color: themeColors.textPrimary, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span>🧪</span> Fertilizer Recommendation
                    </h3>

                    <div style={{ marginBottom: '0.8rem' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 700, color: themeColors.textSecondary, textTransform: 'uppercase' }}>Recommended Fertilizer</span>
                      <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#A855F7' }}>{result.fertilizer_recommendation}</div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', fontSize: '0.75rem', marginBottom: '0.8rem' }}>
                      <div style={{ background: themeColors.metricBg, padding: '0.4rem', borderRadius: '8px' }}>
                        <span style={{ color: themeColors.textSecondary, display: 'block' }}>Rate</span>
                        <strong>150 kg/ha</strong>
                      </div>
                      <div style={{ background: themeColors.metricBg, padding: '0.4rem', borderRadius: '8px' }}>
                        <span style={{ color: themeColors.textSecondary, display: 'block' }}>Timing</span>
                        <strong>Basal + Vegetative</strong>
                      </div>
                    </div>

                    <div style={{ fontSize: '0.75rem', color: themeColors.textSecondary }}>
                      <strong>Reason:</strong> Balanced NPK requirement for predicted crop.
                    </div>
                  </div>

                  {/* CARD 4: 💧 SMART IRRIGATION */}
                  <div style={{ background: themeColors.cardBg, border: `1px solid ${themeColors.cardBorder}`, borderRadius: '20px', padding: '1.5rem', boxShadow: '0 4px 20px rgba(0,0,0,0.05)' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0 0 1rem 0', color: themeColors.textPrimary, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span>💧</span> Smart Irrigation
                    </h3>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem' }}>
                      <div>
                        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: themeColors.textSecondary, textTransform: 'uppercase' }}>Irrigation Level</span>
                        <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#3B82F6' }}>{result.irrigation_recommendation.level}</div>
                      </div>
                      <div style={{ padding: '0.4rem 0.8rem', background: '#DBEAFE', color: '#1E40AF', borderRadius: '10px', fontWeight: 800, fontSize: '0.85rem' }}>
                        {result.irrigation_recommendation.water_depth_mm} mm
                      </div>
                    </div>

                    <div style={{ fontSize: '0.8rem', marginBottom: '0.6rem' }}>
                      <span style={{ color: themeColors.textSecondary }}>Best Time:</span> <strong>Morning (6:00 AM - 8:00 AM)</strong>
                    </div>

                    <div style={{ fontSize: '0.75rem', color: themeColors.textSecondary, background: isDark ? '#1E3A8A' : '#EFF6FF', padding: '0.5rem', borderRadius: '8px' }}>
                      <strong>Reason:</strong> Standard moisture balance.
                    </div>
                  </div>

                </div>

                {/* CARD 5: 🌦 WEATHER SUMMARY CARD */}
                <div style={{ background: themeColors.cardBg, border: `1px solid ${themeColors.cardBorder}`, borderRadius: '20px', padding: '1.5rem', boxShadow: '0 4px 20px rgba(0,0,0,0.05)' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0 0 1rem 0', color: themeColors.textPrimary, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>🌦</span> Weather Summary ({result.weather_summary.city})
                  </h3>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.8rem' }}>
                    <div style={{ background: themeColors.metricBg, padding: '0.6rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.65rem', fontWeight: 700, color: themeColors.textSecondary, display: 'block' }}>TEMP</span>
                      <strong style={{ fontSize: '0.95rem' }}>{result.weather_summary.temperature} °C</strong>
                    </div>
                    <div style={{ background: themeColors.metricBg, padding: '0.6rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.65rem', fontWeight: 700, color: themeColors.textSecondary, display: 'block' }}>HUMIDITY</span>
                      <strong style={{ fontSize: '0.95rem' }}>{result.weather_summary.humidity} %</strong>
                    </div>
                    <div style={{ background: themeColors.metricBg, padding: '0.6rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.65rem', fontWeight: 700, color: themeColors.textSecondary, display: 'block' }}>RAINFALL</span>
                      <strong style={{ fontSize: '0.95rem' }}>{result.weather_summary.rainfall} mm</strong>
                    </div>
                    <div style={{ background: themeColors.metricBg, padding: '0.6rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.65rem', fontWeight: 700, color: themeColors.textSecondary, display: 'block' }}>WIND SPEED</span>
                      <strong style={{ fontSize: '0.95rem' }}>{result.weather_summary.wind_speed} m/s</strong>
                    </div>
                    <div style={{ background: themeColors.metricBg, padding: '0.6rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.65rem', fontWeight: 700, color: themeColors.textSecondary, display: 'block' }}>PRESSURE</span>
                      <strong style={{ fontSize: '0.95rem' }}>{result.weather_summary.pressure} hPa</strong>
                    </div>
                    <div style={{ background: themeColors.metricBg, padding: '0.6rem', borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.65rem', fontWeight: 700, color: themeColors.textSecondary, display: 'block' }}>CONDITION</span>
                      <strong style={{ fontSize: '0.95rem' }}>{result.weather_summary.condition}</strong>
                    </div>
                  </div>
                </div>

                {/* CARD 6: 🧠 EXPLAINABLE AI (SHAP) */}
                <div style={{ background: themeColors.cardBg, border: `1px solid ${themeColors.cardBorder}`, borderRadius: '20px', padding: '1.8rem', boxShadow: '0 4px 20px rgba(0,0,0,0.05)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.2rem' }}>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: themeColors.textPrimary, display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <span>🧠</span> Explainable AI (SHAP Feature Importance)
                    </h2>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      {[
                        { id: 'crop', label: '🌱 Crop' },
                        { id: 'yield', label: '🌾 Yield' },
                        { id: 'fert', label: '🧪 Fertilizer' }
                      ].map((t) => (
                        <button
                          key={t.id}
                          onClick={() => setActiveExplainTab(t.id)}
                          style={{
                            padding: '0.4rem 0.8rem',
                            borderRadius: '8px',
                            border: 'none',
                            fontWeight: 700,
                            fontSize: '0.8rem',
                            cursor: 'pointer',
                            background: activeExplainTab === t.id ? themeColors.accentPrimary : themeColors.metricBg,
                            color: activeExplainTab === t.id ? '#FFF' : themeColors.textSecondary
                          }}
                        >
                          {t.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {(() => {
                    const moduleKey = activeExplainTab === 'crop' ? 'crop_recommendation' : activeExplainTab === 'yield' ? 'yield_prediction' : 'fertilizer_recommendation';
                    const explData = result.explainability ? result.explainability[moduleKey] : null;

                    if (!explData) return <p>No SHAP explanation available.</p>;

                    return (
                      <div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.7rem', marginBottom: '1.2rem' }}>
                          {explData.top_5_features && explData.top_5_features.map((feat, idx) => {
                            const roundedVal = feat.shap_value >= 0 ? `+${feat.shap_value.toFixed(3)}` : feat.shap_value.toFixed(3);
                            const barColor = feat.shap_value > 0 ? '#22C55E' : feat.shap_value < 0 ? '#EF4444' : '#64748B';

                            return (
                              <div key={idx} style={{ display: 'grid', gridTemplateColumns: '140px 1fr 90px', alignItems: 'center', gap: '1rem', fontSize: '0.85rem' }}>
                                <span style={{ fontWeight: 700, color: themeColors.textPrimary }} title={`Feature: ${feat.feature}`}>{feat.feature}</span>
                                <div style={{ background: themeColors.metricBg, height: '10px', borderRadius: '5px', overflow: 'hidden' }}>
                                  <div style={{ background: barColor, height: '100%', width: `${Math.min(100, Math.abs(feat.shap_value) * 100)}%`, transition: 'width 0.4s ease' }}></div>
                                </div>
                                <span style={{ fontWeight: 800, color: barColor, textAlign: 'right', fontFamily: 'monospace' }}>
                                  {roundedVal}
                                </span>
                              </div>
                            );
                          })}
                        </div>

                        {/* DARK CODE-STYLE EXPLANATION BOX */}
                        <div style={{ background: '#0F172A', color: '#86EFAC', padding: '1.2rem', borderRadius: '14px', fontFamily: 'monospace', fontSize: '0.85rem', lineHeight: '1.5', maxHeight: '180px', overflowY: 'auto', border: '1px solid #334155' }}>
                          {explData.plain_language_explanation}
                        </div>
                      </div>
                    );
                  })()}
                </div>

                {/* CARD 7: 🚨 AGRICULTURAL INSIGHTS */}
                <div style={{ background: themeColors.cardBg, border: `1px solid ${themeColors.cardBorder}`, borderRadius: '20px', padding: '1.8rem', boxShadow: '0 4px 20px rgba(0,0,0,0.05)' }}>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 1.2rem 0', color: themeColors.textPrimary, display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span>🚨</span> Agricultural Insights & Alerts ({result.agricultural_insights ? result.agricultural_insights.length : 0})
                  </h2>

                  {result.agricultural_insights && result.agricultural_insights.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {result.agricultural_insights.map((insight, idx) => {
                        const style = getSeverityStyle(insight.severity);
                        const isExpanded = expandedInsights[idx];

                        return (
                          <div
                            key={idx}
                            onClick={() => toggleInsight(idx)}
                            style={{
                              background: style.bg,
                              borderLeft: `6px solid ${style.border}`,
                              borderRadius: '14px',
                              padding: '1.2rem',
                              cursor: 'pointer',
                              transition: 'all 0.2s ease'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                <span style={{ fontSize: '1.3rem' }}>{style.icon}</span>
                                <h3 style={{ margin: 0, color: style.titleColor, fontSize: '1.1rem', fontWeight: 700 }}>{insight.title}</h3>
                              </div>
                              <span style={{ color: style.titleColor, fontWeight: 800, fontSize: '0.85rem' }}>
                                {isExpanded ? '▲ Hide Recommendation' : '▼ Show Recommendation'}
                              </span>
                            </div>

                            <p style={{ margin: '0.6rem 0 0 2rem', color: themeColors.textPrimary, fontSize: '0.9rem', lineHeight: '1.4' }}>
                              {insight.message}
                            </p>

                            {isExpanded && (
                              <div style={{ marginTop: '1rem', marginLeft: '2rem', padding: '1rem', background: themeColors.cardBg, borderRadius: '12px', border: `1px solid ${style.border}` }}>
                                <div style={{ color: style.titleColor, fontWeight: 800, fontSize: '0.9rem', marginBottom: '0.3rem' }}>
                                  💡 Actionable Agronomist Recommendation
                                </div>
                                <p style={{ margin: 0, color: themeColors.textPrimary, fontSize: '0.85rem', lineHeight: '1.5' }}>
                                  {insight.recommendation}
                                </p>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p style={{ color: themeColors.textSecondary }}>No critical alerts detected.</p>
                  )}
                </div>

              </>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};

export default PredictionDashboard;
