import React from 'react'
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts'
import {
  Activity,
  AlertCircle,
  Calendar,
  CheckCircle2,
  HelpCircle,
  Scale,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'
import type { AccuracyResponse } from '../types'

interface AccuracyViewProps {
  data: AccuracyResponse | null
  loading: boolean
  startDate: string
  endDate: string
  onStartDateChange: (val: string) => void
  onEndDateChange: (val: string) => void
  minDate: string
  maxDate: string
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{ value: number; name: string; color: string }>
  label?: string
}

const CustomDailyTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null

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
        minWidth: '200px',
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: '6px', color: 'var(--text-primary)' }}>
        Delivery Date: {label}
      </div>
      {payload.map((item) => (
        <div
          key={item.name}
          style={{ display: 'flex', justifyContent: 'space-between', margin: '4px 0' }}
        >
          <span style={{ color: item.color, fontWeight: 600 }}>{item.name}:</span>
          <span className="mono" style={{ fontWeight: 700 }}>
            {item.value > 0 && item.name === 'Daily Bias (MW)'
              ? `+${item.value.toLocaleString()}`
              : item.value.toLocaleString()}{' '}
            MW
          </span>
        </div>
      ))}
    </div>
  )
}

export const AccuracyView: React.FC<AccuracyViewProps> = ({
  data,
  loading,
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  minDate,
  maxDate,
}) => {
  if (loading) {
    return (
      <div className="panel" style={{ textAlign: 'center', padding: '60px 20px' }}>
        <div
          style={{
            display: 'inline-block',
            width: '36px',
            height: '36px',
            border: '3px solid rgba(6, 182, 212, 0.2)',
            borderTopColor: 'var(--accent-cyan)',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <p style={{ marginTop: '16px', color: 'var(--text-secondary)' }}>
          Computing accuracy metrics & daily trends...
        </p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  if (!data) {
    return null
  }

  const { metrics, daily, cutoff } = data
  const isOverforecast = metrics.bias > 0

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Date Range Selector Panel */}
      <div className="panel" style={{ padding: '16px 20px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>Analysis Window</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Evaluate cumulative accuracy across custom delivery intervals at{' '}
              <span className="mono">{cutoff}</span> cutoff
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <div className="input-group">
              <label
                htmlFor="accuracy-start-date"
                className="input-label"
                style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                <Calendar size={12} />
                <span>Start Date</span>
              </label>
              <input
                id="accuracy-start-date"
                type="date"
                className="input-control mono"
                value={startDate}
                min={minDate}
                max={endDate}
                onChange={(e) => onStartDateChange(e.target.value)}
              />
            </div>

            <div className="input-group">
              <label
                htmlFor="accuracy-end-date"
                className="input-label"
                style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                <Calendar size={12} />
                <span>End Date</span>
              </label>
              <input
                id="accuracy-end-date"
                type="date"
                className="input-control mono"
                value={endDate}
                min={startDate}
                max={maxDate}
                onChange={(e) => onEndDateChange(e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '16px',
        }}
      >
        {/* MAE Card */}
        <div className="kpi-card" style={{ '--card-accent': '#06b6d4' } as React.CSSProperties}>
          <div className="kpi-title">MAE (Mean Absolute Error)</div>
          <div className="kpi-value">
            {metrics.mae.toLocaleString()}{' '}
            <span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}>
              MW
            </span>
          </div>
          <div className="kpi-sub">
            <Scale size={14} color="#06b6d4" />
            <span>Average magnitude of deviation</span>
          </div>
        </div>

        {/* RMSE Card */}
        <div className="kpi-card" style={{ '--card-accent': '#8b5cf6' } as React.CSSProperties}>
          <div className="kpi-title">RMSE (Root Mean Square)</div>
          <div className="kpi-value">
            {metrics.rmse.toLocaleString()}{' '}
            <span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}>
              MW
            </span>
          </div>
          <div className="kpi-sub">
            <Activity size={14} color="#8b5cf6" />
            <span>Heavily penalizes extreme outliers</span>
          </div>
        </div>

        {/* Bias Card */}
        <div
          className="kpi-card"
          style={
            {
              '--card-accent': isOverforecast ? '#f59e0b' : '#38bdf8',
            } as React.CSSProperties
          }
        >
          <div className="kpi-title">Mean Bias (Forecast − Actual)</div>
          <div
            className="kpi-value"
            style={{ color: isOverforecast ? '#fbbf24' : '#38bdf8' }}
          >
            {metrics.bias > 0 ? `+${metrics.bias.toLocaleString()}` : metrics.bias.toLocaleString()}{' '}
            <span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}>
              MW
            </span>
          </div>
          <div className="kpi-sub">
            {isOverforecast ? (
              <TrendingUp size={14} color="#f59e0b" />
            ) : (
              <TrendingDown size={14} color="#38bdf8" />
            )}
            <span>
              {isOverforecast ? 'Over-forecasting tendency' : 'Under-forecasting tendency'}
            </span>
          </div>
        </div>

        {/* Coverage Card */}
        <div
          className="kpi-card"
          style={
            {
              '--card-accent': metrics.excluded_count > 0 ? '#f59e0b' : '#10b981',
            } as React.CSSProperties
          }
        >
          <div className="kpi-title">Settlement Coverage</div>
          <div className="kpi-value">
            {metrics.point_count.toLocaleString()}{' '}
            <span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}>
              pts
            </span>
          </div>
          <div className="kpi-sub">
            {metrics.excluded_count === 0 ? (
              <CheckCircle2 size={14} color="#10b981" />
            ) : (
              <AlertCircle size={14} color="#f59e0b" />
            )}
            <span>
              {metrics.excluded_count === 0
                ? '100% paired half-hours'
                : `${metrics.excluded_count} excluded periods`}
            </span>
          </div>
        </div>
      </div>

      {/* Plain Language Trading Desk Reading */}
      <div
        className="panel"
        style={{
          borderLeft: `4px solid ${isOverforecast ? 'var(--accent-amber)' : 'var(--accent-cyan)'}`,
          background: 'linear-gradient(90deg, rgba(19, 27, 46, 0.95), rgba(13, 18, 31, 0.85))',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
          <HelpCircle size={22} color={isOverforecast ? '#fbbf24' : '#38bdf8'} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '6px' }}>
              Trading Desk Plain-Language Reading
            </h4>
            <p style={{ fontSize: '0.9rem', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
              For purchase decisions evaluated across{' '}
              <strong style={{ color: 'var(--text-primary)' }}>{data.start_date}</strong> to{' '}
              <strong style={{ color: 'var(--text-primary)' }}>{data.end_date}</strong> at the{' '}
              <span className="mono" style={{ color: 'var(--text-primary)' }}>{data.cutoff}</span> UK decision cutoff,
              the latest available WINDFOR forecast exhibited an average absolute error (MAE) of{' '}
              <strong style={{ color: 'var(--text-primary)' }}>{metrics.mae.toLocaleString()} MW</strong>.
              {isOverforecast ? (
                <>
                  {' '}The overall positive bias of <strong style={{ color: '#fbbf24' }}>+{metrics.bias.toLocaleString()} MW</strong> indicates that the day-ahead forecast tended to over-predict national wind generation. Power buying desks factoring this profile should be cautious of short outturns and potential exposure to system buy prices in the balancing mechanism.
                </>
              ) : (
                <>
                  {' '}The overall negative bias of <strong style={{ color: '#38bdf8' }}>{metrics.bias.toLocaleString()} MW</strong> indicates that the day-ahead forecast tended to under-predict national wind generation. Buying desks can expect actual renewable output to have provided a buffer above day-ahead contracted levels.
                </>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Daily Error Breakdown Chart */}
      <div className="panel">
        <div style={{ marginBottom: '20px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>
            Daily Accuracy Trend (MAE & Mean Bias)
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Comparing day-to-day forecast error volatility across all 31 delivery days
          </p>
        </div>

        <div style={{ width: '100%', height: '380px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={daily.map((d) => ({
                ...d,
                shortDate: d.date.slice(5),
                'Daily MAE (MW)': d.mae,
                'Daily Bias (MW)': d.bias,
              }))}
              margin={{ top: 10, right: 20, left: 10, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.07)" vertical={false} />
              <XAxis
                dataKey="shortDate"
                stroke="var(--text-muted)"
                fontSize={11}
                tickLine={false}
                tick={{ fill: 'var(--text-secondary)' }}
              />
              <YAxis
                stroke="var(--text-muted)"
                fontSize={11}
                tickLine={false}
                tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
                tick={{ fill: 'var(--text-secondary)' }}
                unit=" MW"
              />
              <Tooltip content={<CustomDailyTooltip />} />
              <Legend
                verticalAlign="top"
                align="right"
                wrapperStyle={{ paddingBottom: '16px', fontSize: '0.85rem' }}
              />
              <Bar
                dataKey="Daily MAE (MW)"
                fill="#06b6d4"
                radius={[4, 4, 0, 0]}
                opacity={0.85}
              />
              <Line
                type="monotone"
                dataKey="Daily Bias (MW)"
                stroke="#fbbf24"
                strokeWidth={2.5}
                dot={{ r: 3, fill: '#fbbf24' }}
                activeDot={{ r: 6 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
