'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface ReviewData {
  intakeResult: {
    encoding: string
    language: string
    corruptionStatus: string
    status: string
    submissionEligible: boolean
    warnings: string[]
  }
  sourceIdentity: {
    sourceHash: string
    fileSize: number
  }
}

export default function ReviewPage() {
  const [reviewData, setReviewData] = useState<ReviewData | null>(null)
  const [reviewStatus, setReviewStatus] = useState<'pending' | 'approved' | 'rejected'>('pending')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)

  useEffect(() => {
    const stored = sessionStorage.getItem('ntpe_review_data')
    if (stored) {
      setReviewData(JSON.parse(stored))
    } else {
      window.location.href = '/'
    }
  }, [])

  const handleApprove = () => {
    setReviewStatus('approved')
  }

  const handleReject = () => {
    setReviewStatus('rejected')
  }

  const handleSubmit = async () => {
    if (!reviewData) return

    setIsSubmitting(true)
    setError(null)

    try {
      const response = await fetch('/api/translation/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sourceHash: reviewData.sourceIdentity.sourceHash,
          fileSize: reviewData.sourceIdentity.fileSize,
          qualityProfile: 'literary',
          speed: 'balanced',
          qualityDeliveryV83: true,
          qualityDeliveryFormatsV83: ['txt', 'epub'],
        }),
      })

      if (!response.ok) {
        throw new Error(`Submission failed: ${response.statusText}`)
      }

      const data = await response.json()
      setJobId(data.job_id)
      sessionStorage.setItem('ntpe_job_id', data.job_id)
      window.location.href = `/jobs/${data.job_id}`
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setIsSubmitting(false)
    }
  }

  if (!reviewData) {
    return (
      <div className="container">
        <div className="card">
          <p>載入中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <h1>NTPE Reader - 審��與提交</h1>

      <div className="card">
        <h2>Intake 結果</h2>
        <table>
          <tbody>
            <tr>
              <th>編��</th>
              <td>{reviewData.intakeResult.encoding}</td>
            </tr>
            <tr>
              <th>語言</th>
              <td>{reviewData.intakeResult.language}</td>
            </tr>
            <tr>
              <th>������態</th>
              <td>{reviewData.intakeResult.corruptionStatus}</td>
            </tr>
            <tr>
              <th>Intake ��態</th>
              <td>
                <span className={`status-badge status-${reviewData.intakeResult.status}`}>
                  {reviewData.intakeResult.status}
                </span>
              </td>
            </tr>
            <tr>
              <th>來源����</th>
              <td>{reviewData.sourceIdentity.sourceHash}</td>
            </tr>
            <tr>
              <th>��案大小</th>
              <td>{formatBytes(reviewData.sourceIdentity.fileSize)}</td>
            </tr>
          </tbody>
        </table>

        {reviewData.intakeResult.warnings.length > 0 && (
          <div>
            <h3>警告</h3>
            <ul>
              {reviewData.intakeResult.warnings.map((w, i) => (
                <li key={i} className="status-badge status-ready_with_warnings">{w}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="card">
        <h2>人工審��</h2>
        <p>��確認上述資��無��後，選��審��結果：</p>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <button
            className={`btn ${reviewStatus === 'approved' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={handleApprove}
            disabled={reviewStatus !== 'pending'}
          >
            通過 (Approve)
          </button>
          <button
            className={`btn ${reviewStatus === 'rejected' ? 'btn-danger' : 'btn-secondary'}`}
            onClick={handleReject}
            disabled={reviewStatus !== 'pending'}
          >
            ���� (Reject)
          </button>
        </div>

        {reviewStatus === 'approved' && (
          <div style={{ marginTop: '1rem' }}>
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? '提交中...' : '提交翻��作業'}
            </button>
            {error && (
              <div className="status-badge status-failed" style={{ marginTop: '0.5rem' }}>
                �����: {error}
              </div>
            )}
          </div>
        )}

        {reviewStatus === 'rejected' && (
          <div style={{ marginTop: '1rem', color: '#cc0000' }}>
            ������提交。��返回修改或選��其他��案。
          </div>
        )}
      </div>

      <Link href="/" className="btn btn-secondary">
        返回導入
      </Link>
    </div>
  )
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}