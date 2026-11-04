import React from 'react'
import { PageHeader } from '../components/ui'
import { DecisionPlayground } from '../components/DecisionPlayground'

export default function Decisions() {
  return (
    <div>
      <PageHeader title="Decision playground"
        subtitle="Stack the decisions you're weighing on top of your plan, drag them along the timeline, and see what each one does. Nothing changes your plan until you say so." />
      <DecisionPlayground />
    </div>
  )
}
