import React, { useState } from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts'
import { Zap, Info, Clock, AlertTriangle, Eye, EyeOff } from 'lucide-react'
import type { ForecastPoint, ForecastResponse } from '../types'

interface ForecastViewProps {
  data: ForecastResponse | null
  loading: boolean
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{ value: number; name: string; color: string; payload: ForecastPoint }>
  label?: string
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null

  const point = payload[0]?.payload
  if (!point) return null

  const fVal = point.forecast_mw
  const aVal = point.actual_mw
  const diff = fVal !== null && aVal !== null ? fVal - aVal : null

  return (
    <div
      style={{
        background: 'rgba(13, 18, 31, 0.95)',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        borderRadius: 'var(--radius-md)',
        padding: '12px 16px',
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.7)',
        backdropFilter: 'blur(8px)',
        fontSize: '0.85rem',
        minWidth: '220px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '4px' }}>
        <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>SP {point.settlement_period}</span>
        <span className="mono" style={{ color: 'var(--text-muted)' }}>{label} UTC</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#06b6d4', fontWeight: 600 }}>Forecast:</span>
          <span className="mono" style={{ fontWeight: 700 }}>
            {fVal !== null ? `${fVal.toLocaleString()} MW` : 'No forecast'}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#8b5cf6', fontWeight: 600 }}>Actual:</span>
          <span className="mono" style={{ fontWeight: 700 }}>
            {aVal !== null ? `${aVal.toLocaleString()} MW` : 'Pending'}
          </span>
        </div>

        {diff !== null && (
          <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px dashed rgba(255, 255, 255, 0.1)', paddingTop: '4px', marginTop: '2px' }}>
            <span style={{ color: diff >= 0 ? 'var(--accent-amber)' : '#38bdf8' }}>
              {diff >= 0 ? 'Over-forecast:' : 'Under-forecast:'}
            </span>
            <span className="mono" style={{ fontWeight: 700, color: diff >= 0 ? '#fbbf24' : '#38bdf8' }}>
              {diff > 0 ? `+${diff.toLocaleString()}` : diff.toLocaleString()} MW
            </span>
          </div>
        )}

        <div style={{ marginTop: '6px', fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Clock size={11} />
          <span>
            {point.forecast_publish_time
              ? `Pub: ${point.forecast_publish_time.replace('T', ' ').slice(0, 16)} UTC`
              : 'No publish before cutoff'}
          </span>
        </div>
      </div>
    </div>
  )
}

export const ForecastView: React.FC<ForecastViewProps> = ({ data, loading }) => {
  const [showTable, setShowTable] = useState(false)

  if (loading) {
    return (
      <div className="panel" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <div style={{ display: 'inline-block', width: '36px', height: '36px', border: '3px solid rgba(6, 182, 212, 0.2)', borderTopColor: 'var(--accent-cyan)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
        <p style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>Loading forecast & outturn series...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  if (!data || !data.points.length) {
    return (
      <div className="panel" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <AlertTriangle size={36} color="var(--accent-amber)" style={{ margin: '0 auto 12px' }} />
        <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>No Data for Selected Date</h3>
        <p style={{ color: 'var(--text-secondary)' }}>
          Please pick a delivery date in the January 2026 range (2 Jan to 1 Feb).
        </p>
      </div>
    )
  }

  // Calculate day summary metrics
  const validForecasts = data.points.filter((p) => p.forecast_mw !== null).map((p) => p.forecast_mw as number)
  const validActuals = data.points.filter((p) => p.actual_mw !== null).map((p) => p.actual_mw as number)

  const peakForecast = validForecasts.length ? Math.max(...validForecasts) : 0
  const peakActual = validActuals.length ? Math.max(...validActuals) : 0
  const unforecastedCount = data.points.filter((p) => p.forecast_mw === null).length

  // Chart data formatting
  const chartData = data.points.map((p) => {
    const timeLabel = p.start_time.slice(11, 16)
    return {
      ...p,
      timeLabel,
      'Forecast (MW)': p.forecast_mw,
      'Actual (MW)': p.actual_mw,
    }
  })

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Day Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="kpi-card" style={{ '--card-accent': '#06b6d4' } as React.CSSProperties}>
          <div className="kpi-title">Peak Day-Ahead Forecast</div>
          <div className="kpi-value">{peakForecast.toLocaleString()} <span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}>MW</span></div>
          <div className="kpi-sub">
            <Zap size={14} color="#06b6d4" />
            <span>Highest predicted output</span>
          </div>
        </div>

        <div className="kpi-card" style={{ '--card-accent': '#8b5cf6' } as React.CSSProperties}>
          <div className="kpi-title">Peak Actual Outturn</div>
          <div className="kpi-value">{peakActual.toLocaleString()} <span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}>MW</span></div>
          <div className="kpi-sub">
            <Zap size={14} color="#8b5cf6" />
            <span>Highest observed output</span>
          </div>
        </div>

        <div className="kpi-card" style={{ '--card-accent': unforecastedCount > 0 ? '#f59e0b' : '#10b981' } as React.CSSProperties}>
          <div className="kpi-title">Decision Cutoff (UTC)</div>
          <div className="kpi-value" style={{ fontSize: '1.4rem' }}>
            {data.cutoff_utc.replace('T', ' ').slice(0, 16)}
          </div>
          <div className="kpi-sub">
            <Clock size={14} color={unforecastedCount > 0 ? '#f59e0b' : '#10b981'} />
            <span>{unforecastedCount === 0 ? 'All 48 half-hours forecasted' : `${unforecastedCount} half-hours unforecasted`}</span>
          </div>
        </div>
      </div>

      {/* Main Chart Panel */}
      <div className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>
              Half-Hourly Generation: Forecast vs Actual
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Delivery Date: <strong style={{ color: 'var(--text-primary)' }}>{data.delivery_date}</strong> • Latest WINDFOR publish at or before <span className="mono">{data.cutoff}</span> (UK time on D-1)
            </p>
          </div>

          <button
            type="button"
            className="btn"
            onClick={() => setShowTable(!showTable)}
            style={{ fontSize: '0.8rem' }}
          >
            {showTable ? <EyeOff size={14} /> : <Eye size={14} />}
            <span>{showTable ? 'Hide Settlement Table' : 'View Settlement Periods'}</span>
          </button>
        </div>

        <div style={{ width: '100%', height: '420px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.07)" vertical={false} />
              <XAxis
                dataKey="timeLabel"
                stroke="var(--text-muted)"
                fontSize={11}
                tickLine={false}
                interval={3}
                tick={{ fill: 'var(--text-secondary)' }}
              />
              <YAxis
                stroke="var(--text-muted)"
                fontSize={11}
                tickLine={false}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                tick={{ fill: 'var(--text-secondary)' }}
                unit=" MW"
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="top"
                align="right"
                wrapperStyle={{ paddingBottom: '16px', fontSize: '0.85rem' }}
              />
              <Line
                type="monotone"
                dataKey="Forecast (MW)"
                stroke="#06b6d4"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 6, fill: '#06b6d4', stroke: '#fff', strokeWidth: 2 }}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="Actual (MW)"
                stroke="#8b5cf6"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 6, fill: '#8b5cf6', stroke: '#fff', strokeWidth: 2 }}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <Info size={14} />
          <span>Hover over any half-hour point on the chart to inspect the generation outturn and the exact publish timestamp that provided the forecast.</span>
        </div>
      </div>

      {/* Settlement Periods Breakdown Table */}
      {showTable && (
        <div className="panel fade-in" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '14px' }}>
            Settlement Period Audit (48 Half-Hours)
          </h3>
          <div style={{ maxHeight: '360px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '8px 12px' }}>Period</th>
                  <th style={{ padding: '8px 12px' }}>Start Time (UTC)</th>
                  <th style={{ padding: '8px 12px' }}>Forecast (MW)</th>
                  <th style={{ padding: '8px 12px' }}>Actual Outturn (MW)</th>
                  <th style={{ padding: '8px 12px' }}>Error (F − A)</th>
                  <th style={{ padding: '8px 12px' }}>Forecast Publish Time</th>
                </tr>
              </thead>
              <tbody>
                {data.points.map((p) => {
                  const err = p.forecast_mw !== null && p.actual_mw !== null ? p.forecast_mw - p.actual_mw : null
                  return (
                    <tr
                      key={p.settlement_period}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        backgroundColor: p.settlement_period % 2 === 0 ? 'rgba(255, 255, 255, 0.02)' : 'transparent',
                      }}
                    >
                      <td style={{ padding: '8px 12px', fontWeight: 600 }}>SP {p.settlement_period}</td>
                      <td className="mono" style={{ padding: '8px 12px', color: 'var(--text-secondary)' }}>
                        {p.start_time.slice(11, 16)}
                      </td>
                      <td className="mono" style={{ padding: '8px 12px', color: '#06b6d4', fontWeight: 600 }}>
                        {p.forecast_mw !== null ? `${p.forecast_mw.toLocaleString()} MW` : '—'}
                      </td>
                      <td className="mono" style={{ padding: '8px 12px', color: '#8b5cf6', fontWeight: 600 }}>
                        {p.actual_mw !== null ? `${p.actual_mw.toLocaleString()} MW` : '—'}
                      </td>
                      <td className="mono" style={{ padding: '8px 12px' }}>
                        {err !== null ? (
                          <span style={{ color: err >= 0 ? '#fbbf24' : '#38bdf8' }}>
                            {err > 0 ? `+${err.toLocaleString()}` : err.toLocaleString()} MW
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="mono" style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>
                        {p.forecast_publish_time ? p.forecast_publish_time.replace('T', ' ').slice(0, 16) : 'None'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
