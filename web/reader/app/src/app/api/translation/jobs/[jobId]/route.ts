import { NextResponse } from 'next/server'

export async function GET(
  request: Request,
  { params }: { params: { jobId: string } }
) {
  const jobId = params.jobId

  const mockJob = {
    jobId,
    status: 'running',
    currentChunk: 3,
    completedChunks: 2,
    failedChunks: 0,
    totalChunks: 10,
    sourceIdentity: jobId.split('_')[1] || 'unknown',
    translationProfile: 'literary, balanced speed',
    deliverySettings: 'quality_delivery_v83=true, formats=[txt, epub]',
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    updatedAt: new Date().toISOString(),
    resumable: true,
  }

  return NextResponse.json(mockJob)
}