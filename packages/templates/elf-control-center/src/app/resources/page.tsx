'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { ResourceStatusDashboard } from '@/components/resources/ResourceStatusDashboard'

export default function ResourcesPage() {
  return (
    <PageTransition variant="fade">
      <div className="p-6">
        <ResourceStatusDashboard />
      </div>
    </PageTransition>
  )
}
