import { useEffect, useState, useCallback } from 'react'
import { Header } from './components/Header'
import { ControlBar } from './components/ControlBar'
import { ForecastView } from './components/ForecastView'
import { AccuracyView } from './components/AccuracyView'
import { fetchAccuracy, fetchForecast, fetchMeta } from './api/client'
import type { AccuracyResponse, ForecastResponse, MetaResponse } from './types'
import { AlertCircle, RefreshCw } from 'lucide-react'

export function App() {
  const [meta, setMeta] = useState<MetaResponse | null>(null)
  const [activeTab, setActiveTab] = useState<'forecast' | 'accuracy'>('forecast')

  // Global controls
  const [deliveryDate, setDeliveryDate] = useState('2026-01-02')
  const [cutoff, setCutoff] = useState('09:00')

  // Accuracy view date range
  const [accuracyStart, setAccuracyStart] = useState('2026-01-02')
  const [accuracyEnd, setAccuracyEnd] = useState('2026-02-01')

  // Data states
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null)
  const [forecastLoading, setForecastLoading] = useState(false)

  const [accuracyData, setAccuracyData] = useState<AccuracyResponse | null>(null)
  const [accuracyLoading, setAccuracyLoading] = useState(false)

  const [error, setError] = useState<string | null>(null)

  // Fetch metadata on mount
  useEffect(() => {
    fetchMeta()
      .then((data) => {
        setMeta(data)
        if (data.default_date) setDeliveryDate(data.default_date)
        if (data.default_cutoff) setCutoff(data.default_cutoff)
        if (data.start_date) setAccuracyStart(data.start_date)
        if (data.end_date) setAccuracyEnd(data.end_date)
      })
      .catch((err) => {
        setError(`Failed to load system metadata: ${err.message}`)
      })
  }, [])

  // Fetch forecast series when date or cutoff changes
  const loadForecast = useCallback(() => {
    if (!deliveryDate || !cutoff) return
    setForecastLoading(true)
    setError(null)
    fetchForecast(deliveryDate, cutoff)
      .then((res) => {
        setForecastData(res)
      })
      .catch((err) => {
        setError(`Forecast query failed: ${err.message}`)
      })
      .finally(() => {
        setForecastLoading(false)
      })
  }, [deliveryDate, cutoff])

  useEffect(() => {
    loadForecast()
  }, [loadForecast])

  // Fetch accuracy metrics when range or cutoff changes
  const loadAccuracy = useCallback(() => {
    if (!accuracyStart || !accuracyEnd || !cutoff) return
    setAccuracyLoading(true)
    setError(null)
    fetchAccuracy(accuracyStart, accuracyEnd, cutoff)
      .then((res) => {
        setAccuracyData(res)
      })
      .catch((err) => {
        setError(`Accuracy query failed: ${err.message}`)
      })
      .finally(() => {
        setAccuracyLoading(false)
      })
  }, [accuracyStart, accuracyEnd, cutoff])

  useEffect(() => {
    if (activeTab === 'accuracy') {
      loadAccuracy()
    }
  }, [activeTab, loadAccuracy])

  return (
    <div className="app-container">
      <Header meta={meta} />

      <ControlBar
        meta={meta}
        deliveryDate={deliveryDate}
        onDeliveryDateChange={setDeliveryDate}
        cutoff={cutoff}
        onCutoffChange={setCutoff}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {error && (
        <div
          role="alert"
          className="panel fade-in"
          style={{
            borderColor: 'var(--accent-rose)',
            background: 'rgba(244, 63, 94, 0.1)',
            padding: '16px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertCircle size={20} color="var(--accent-rose)" />
            <span style={{ fontSize: '0.9rem', color: '#fca5a5' }}>{error}</span>
          </div>
          <button
            type="button"
            className="btn"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            onClick={() => {
              setError(null)
              if (activeTab === 'forecast') loadForecast()
              else loadAccuracy()
            }}
          >
            <RefreshCw size={13} />
            <span>Retry</span>
          </button>
        </div>
      )}

      <main>
        {activeTab === 'forecast' ? (
          <ForecastView data={forecastData} loading={forecastLoading} />
        ) : (
          <AccuracyView
            data={accuracyData}
            loading={accuracyLoading}
            startDate={accuracyStart}
            endDate={accuracyEnd}
            onStartDateChange={setAccuracyStart}
            onEndDateChange={setAccuracyEnd}
            minDate={meta?.start_date || '2026-01-02'}
            maxDate={meta?.end_date || '2026-02-01'}
          />
        )}
      </main>
    </div>
  )
}

export default App
