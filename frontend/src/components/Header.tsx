import React from 'react'
import { Wind, Database, Clock, Activity } from 'lucide-react'
import type { MetaResponse } from '../types'

interface HeaderProps {
  meta: MetaResponse | null
}

export const Header: React.FC<HeaderProps> = ({ meta }) => {
  return (
    <header className="panel" style={{ padding: '20px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(139, 92, 246, 0.2))',
              border: '1px solid rgba(6, 182, 212, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-cyan)',
            }}
          >
            <Wind size={26} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                UK Wind Forecast Portal
              </h1>
              <span className="badge badge-cyan">Day-Ahead Buying Desk</span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Elexon BMRS FUELHH outturn vs. WINDFOR published forecast evaluation (January 2026)
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div className="badge badge-emerald">
            <Activity size={13} />
            <span>API Online</span>
          </div>

          <div className="badge badge-cyan" title="Snapshot covers 2 Jan - 1 Feb 2026">
            <Database size={13} />
            <span className="mono">
              {meta ? `${meta.total_actual_records} Actuals` : 'Loading...'}
            </span>
          </div>

          <div className="badge badge-amber" title="D-1 Cutoff interpreted in Europe/London">
            <Clock size={13} />
            <span>D-1 Cutoff (Europe/London)</span>
          </div>
        </div>
      </div>
    </header>
  )
}
