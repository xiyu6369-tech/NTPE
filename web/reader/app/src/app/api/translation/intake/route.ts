import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File | null

    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      )
    }

    const text = await file.text()
    const encoding = detectEncoding(text)
    const language = detectLanguage(text)
    const corruptionStatus = checkCorruption(text)
    const intakeResult = determineIntakeStatus(corruptionStatus, language)

    return NextResponse.json({
      encoding,
      language,
      corruptionStatus,
      status: intakeResult.status,
      submissionEligible: intakeResult.submissionEligible,
      warnings: intakeResult.warnings,
    })
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}

function detectEncoding(text: string): string {
  return 'utf-8'
}

function detectLanguage(text: string): string {
  const koreanChars = (text.match(/[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7A3]/g) || []).length
  const japaneseChars = (text.match(/[\u3040-\u309F\u30A0-\u30FF]/g) || []).length
  const chineseChars = (text.match(/[\u4E00-\u9FFF]/g) || []).length

  const total = koreanChars + japaneseChars + chineseChars
  if (total === 0) return 'unknown'

  if (koreanChars > japaneseChars && koreanChars > chineseChars) return 'ko'
  if (japaneseChars > koreanChars && japaneseChars > chineseChars) return 'ja'
  if (chineseChars > koreanChars && chineseChars > japaneseChars) return 'zh'
  return 'mixed'
}

function checkCorruption(text: string): string {
  const nullChars = (text.match(/\x00/g) || []).length
  const replacementChars = (text.match(/\uFFFD/g) || []).length
  const controlChars = (text.match(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g) || []).length

  if (nullChars > 0 || replacementChars > 0 || controlChars > text.length * 0.01) {
    return 'corrupted'
  }
  return 'clean'
}

function determineIntakeStatus(corruptionStatus: string, language: string): { status: string; submissionEligible: boolean; warnings: string[] } {
  const warnings: string[] = []

  if (corruptionStatus === 'corrupted') {
    return { status: 'blocked', submissionEligible: false, warnings: ['File corruption detected'] }
  }

  if (language === 'unknown' || language === 'mixed') {
    warnings.push(`Language detection uncertain: ${language}`)
    return { status: 'manual_review_required', submissionEligible: false, warnings }
  }

  if (language !== 'ko') {
    warnings.push(`Expected Korean source, detected: ${language}`)
    return { status: 'manual_review_required', submissionEligible: false, warnings }
  }

  return { status: 'ready', submissionEligible: true, warnings }
}