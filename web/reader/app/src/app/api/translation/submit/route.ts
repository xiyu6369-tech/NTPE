import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { sourceHash, fileSize, qualityProfile, speed, qualityDeliveryV83, qualityDeliveryFormatsV83 } = body

    const jobId = `job_${sourceHash}_${Date.now()}`

    return NextResponse.json({
      job_id: jobId,
      status: 'submitted',
      message: 'Job submitted successfully. Poll /api/translation/jobs/[jobId] for status.',
    })
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}