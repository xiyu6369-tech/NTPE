import { NextResponse } from 'next/server'

const mockJobs = [
  {
    jobId: 'job_a1b2c3d4_1234567890',
    status: 'running',
    currentChunk: 3,
    completedChunks: 2,
    failedChunks: 0,
    totalChunks: 10,
    sourceIdentity: 'a1b2c3d4',
    translationProfile: 'literary, balanced speed',
    deliverySettings: 'quality_delivery_v83=true, formats=[txt, epub]',
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    updatedAt: new Date().toISOString(),
    resumable: true,
  },
]

export async function GET() {
  return NextResponse.json({ jobs: mockJobs })
}