import React, { useState } from 'react'
import { FileDown, Loader2 } from 'lucide-react'
import { usePlan } from '../lib/store'
import { api } from '../lib/api'
import { Button } from './ui'

/** Downloads a PDF report of the plan currently on screen. */
export function ReportButton({ size = 'sm' as 'sm' | 'md' }) {
  const { plan } = usePlan()
  const [busy, setBusy] = useState(false)
  return (
    <Button size={size} disabled={busy} onClick={async () => { setBusy(true); try { await api.downloadReport(plan) } finally { setBusy(false) } }}>
      {busy ? <Loader2 size={14} className="animate-spin" /> : <FileDown size={14} />}PDF report
    </Button>
  )
}
