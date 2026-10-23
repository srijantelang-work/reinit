import type { AccuracyResponse, ForecastResponse, MetaResponse } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`
    try {
      const errJson = await res.json()
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail
      }
    } catch {
      // Ignore JSON parse errors for non-JSON response
    }
    throw new Error(errorDetail)
  }
  return res.json()
}

export async function fetchMeta(): Promise<MetaResponse> {
  const res = await fetch(`${BASE_URL}/api/meta`)
  return handleResponse<MetaResponse>(res)
}

export async function fetchForecast(deliveryDate: string, cutoff: string): Promise<ForecastResponse> {
  const params = new URLSearchParams({
    delivery_date: deliveryDate,
    cutoff,
  })
  const res = await fetch(`${BASE_URL}/api/forecast?${params.toString()}`)
  return handleResponse<ForecastResponse>(res)
}

export async function fetchAccuracy(
  start: string,
  end: string,
  cutoff: string,
): Promise<AccuracyResponse> {
  const params = new URLSearchParams({
    start,
    end,
    cutoff,
  })
  const res = await fetch(`${BASE_URL}/api/accuracy?${params.toString()}`)
  return handleResponse<AccuracyResponse>(res)
}
