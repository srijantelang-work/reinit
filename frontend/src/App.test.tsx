import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import App from './App'
import * as apiClient from './api/client'

vi.mock('./api/client', () => ({
  fetchMeta: vi.fn(),
  fetchForecast: vi.fn(),
  fetchAccuracy: vi.fn(),
}))

const mockMeta = {
  start_date: '2026-01-02',
  end_date: '2026-02-01',
  default_cutoff: '09:00',
  default_date: '2026-01-02',
  total_actual_records: 1488,
  total_forecast_records: 17864,
}

const mockForecast = {
  delivery_date: '2026-01-02',
  cutoff: '09:00',
  cutoff_utc: '2026-01-01T09:00:00Z',
  points: [
    {
      settlement_period: 1,
      start_time: '2026-01-02T00:00:00Z',
      forecast_mw: 18000,
      forecast_publish_time: '2026-01-01T08:30:00Z',
      actual_mw: 15000,
    },
    {
      settlement_period: 2,
      start_time: '2026-01-02T00:30:00Z',
      forecast_mw: 18000,
      forecast_publish_time: '2026-01-01T08:30:00Z',
      actual_mw: 15200,
    },
  ],
}

const mockAccuracy = {
  start_date: '2026-01-02',
  end_date: '2026-02-01',
  cutoff: '09:00',
  metrics: {
    mae: 1250.5,
    rmse: 1560.8,
    bias: 320.4,
    point_count: 1488,
    excluded_count: 0,
  },
  daily: [
    {
      date: '2026-01-02',
      mae: 980.2,
      rmse: 1100.5,
      bias: 250.0,
      point_count: 48,
      excluded_count: 0,
    },
  ],
}

describe('Wind Forecast Portal App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.fetchMeta).mockResolvedValue(mockMeta)
    vi.mocked(apiClient.fetchForecast).mockResolvedValue(mockForecast)
    vi.mocked(apiClient.fetchAccuracy).mockResolvedValue(mockAccuracy)
  })

  it('renders application header and title', async () => {
    render(<App />)

    expect(screen.getByText('UK Wind Forecast Portal')).toBeInTheDocument()
    expect(screen.getByText('Day-Ahead Buying Desk')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('1488 Actuals')).toBeInTheDocument()
    })
  })

  it('renders controls and default values', async () => {
    render(<App />)

    const dateInput = screen.getByLabelText(/Delivery Day/i) as HTMLInputElement
    const cutoffInput = screen.getByLabelText(/D-1 Cutoff/i) as HTMLInputElement

    expect(dateInput).toBeInTheDocument()
    expect(cutoffInput).toBeInTheDocument()

    await waitFor(() => {
      expect(dateInput.value).toBe('2026-01-02')
      expect(cutoffInput.value).toBe('09:00')
    })
  })

  it('renders forecast view by default and displays chart summary', async () => {
    render(<App />)

    await waitFor(() => {
      expect(screen.getByText(/Half-Hourly Generation: Forecast vs Actual/i)).toBeInTheDocument()
      expect(screen.getByText('Peak Day-Ahead Forecast')).toBeInTheDocument()
      expect(screen.getByText('Peak Actual Outturn')).toBeInTheDocument()
    })
  })

  it('switches to accuracy view when clicking the Accuracy tab', async () => {
    const user = userEvent.setup()
    render(<App />)

    const accuracyTab = screen.getByRole('tab', { name: /Accuracy Metrics/i })
    await user.click(accuracyTab)

    await waitFor(() => {
      expect(screen.getByText(/MAE \(Mean Absolute Error\)/i)).toBeInTheDocument()
      expect(screen.getByText(/RMSE \(Root Mean Square\)/i)).toBeInTheDocument()
      expect(screen.getByText(/Trading Desk Plain-Language Reading/i)).toBeInTheDocument()
    })
  })

  it('updates forecast when delivery date changes', async () => {
    const user = userEvent.setup()
    render(<App />)

    await waitFor(() => {
      expect(apiClient.fetchForecast).toHaveBeenCalledWith('2026-01-02', '09:00')
    })

    const dateInput = screen.getByLabelText(/Delivery Day/i)
    await user.clear(dateInput)
    await user.type(dateInput, '2026-01-05')

    await waitFor(() => {
      expect(apiClient.fetchForecast).toHaveBeenCalledWith('2026-01-05', '09:00')
    })
  })

  it('updates forecast when cutoff preset is clicked', async () => {
    const user = userEvent.setup()
    render(<App />)

    await waitFor(() => {
      expect(apiClient.fetchForecast).toHaveBeenCalledWith('2026-01-02', '09:00')
    })

    const preset11 = screen.getByRole('button', { name: '11:00' })
    await user.click(preset11)

    await waitFor(() => {
      expect(apiClient.fetchForecast).toHaveBeenCalledWith('2026-01-02', '11:00')
    })
  })
})
