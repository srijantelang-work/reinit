import React from 'react'
import { Calendar, Clock, BarChart3, TrendingUp } from 'lucide-react'
import type { MetaResponse } from '../types'

interface ControlBarProps {
  meta: MetaResponse | null
  deliveryDate: string
  onDeliveryDateChange: (val: string) => void
  cutoff: string
  onCutoffChange: (val: string) => void
  activeTab: 'forecast' | 'accuracy'
  onTabChange: (tab: 'forecast' | 'accuracy') => void
}

const CUTOFF_PRESETS = [
  { label: '07:00 (Early)', value: '07:00' },
  { label: '09:00 (Default)', value: '09:00' },
  { label: '11:00 (Gate Closure)', value: '11:00' },
  { label: '17:00 (Evening)', value: '17:00' },
]

export const ControlBar: React.FC<ControlBarProps> = ({
  meta,
  deliveryDate,
  onDeliveryDateChange,
  cutoff,
  onCutoffChange,
  activeTab,
  onTabChange,
}) => {
  const minDate = meta?.start_date || '2026-01-02'
  const maxDate = meta?.end_date || '2026-02-01'

  return (
    <div className="panel" style={{ padding: '16px 24px' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px',
        }}
      >
        {/* Navigation Tabs */}
        <div
          role="tablist"
          style={{
            display: 'flex',
            background: 'var(--bg-secondary)',
            padding: '4px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <button
            id="tab-forecast-view"
            role="tab"
            aria-selected={activeTab === 'forecast'}
            className={`btn btn-tab ${activeTab === 'forecast' ? 'active' : ''}`}
            onClick={() => onTabChange('forecast')}
          >
            <TrendingUp size={16} />
            <span>Forecast Profile</span>
          </button>
          <button
            id="tab-accuracy-view"
            role="tab"
            aria-selected={activeTab === 'accuracy'}
            className={`btn btn-tab ${activeTab === 'accuracy' ? 'active' : ''}`}
            onClick={() => onTabChange('accuracy')}
          >
            <BarChart3 size={16} />
            <span>Accuracy Metrics</span>
          </button>
        </div>

        {/* Filters / Inputs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
          {/* Delivery Date Picker */}
          <div className="input-group">
            <label htmlFor="delivery-date-input" className="input-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Calendar size={12} />
              <span>Delivery Day (D)</span>
            </label>
            <input
              id="delivery-date-input"
              type="date"
              className="input-control mono"
              value={deliveryDate}
              min={minDate}
              max={maxDate}
              onChange={(e) => onDeliveryDateChange(e.target.value)}
            />
          </div>

          {/* Cutoff Time Input */}
          <div className="input-group">
            <label htmlFor="cutoff-time-input" className="input-label" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={12} />
              <span>D-1 Cutoff (UK Time)</span>
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                id="cutoff-time-input"
                type="time"
                step="300"
                className="input-control mono"
                style={{ width: '115px' }}
                value={cutoff}
                onChange={(e) => onCutoffChange(e.target.value)}
              />
              <div style={{ display: 'flex', gap: '4px' }}>
                {CUTOFF_PRESETS.map((p) => (
                  <button
                    key={p.value}
                    id={`preset-${p.value.replace(':', '')}`}
                    type="button"
                    className="btn"
                    style={{
                      padding: '6px 10px',
                      fontSize: '0.75rem',
                      background: cutoff === p.value ? 'var(--accent-cyan)' : 'var(--bg-secondary)',
                      color: cutoff === p.value ? '#000' : 'var(--text-secondary)',
                      borderColor: cutoff === p.value ? 'transparent' : 'var(--border-subtle)',
                    }}
                    onClick={() => onCutoffChange(p.value)}
                    title={`Set cutoff to ${p.label}`}
                  >
                    {p.value}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
