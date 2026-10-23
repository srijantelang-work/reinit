export interface MetaResponse {
  start_date: string
  end_date: string
  default_cutoff: string
  default_date: string
  total_actual_records: number
  total_forecast_records: number
}

export interface ForecastPoint {
  settlement_period: number
  start_time: string
  forecast_mw: number | null
  forecast_publish_time: string | null
  actual_mw: number | null
}

export interface ForecastResponse {
  delivery_date: string
  cutoff: string
  cutoff_utc: string
  points: ForecastPoint[]
}

export interface AccuracyMetrics {
  mae: number
  rmse: number
  bias: number
  point_count: number
  excluded_count: number
}

export interface DailyAccuracy {
  date: string
  mae: number
  rmse: number
  bias: number
  point_count: number
  excluded_count: number
}

export interface AccuracyResponse {
  start_date: string
  end_date: string
  cutoff: string
  metrics: AccuracyMetrics
  daily: DailyAccuracy[]
}
