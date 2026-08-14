'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface JobDetail {
  jobId: string
  status: string
  currentChunk: number | null
  completedChunks: number
  failedChunks: number
  totalChunks: number
  sourceIdentity: string
  translationProfile: string
  deliverySettings: string
  createdAt: string
  updatedAt: string
  resumable: boolean
}

export default function JobDetailPage({ params }: { params: { jobId: string } }) {
  const [job, setJob] = useState<JobDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadJob()
    const interval = setInterval(loadJob, 3000)
    return () => clearInterval(interval)
  }, [params.jobId])

  const loadJob = async () => {
    try {
      const response = await fetch(`/api/translation/jobs/${params.jobId}`)
      if (!response.ok) {
        throw new Error(`Failed to load job: ${response.statusText}`)
      }
      const data = await response.json()
      setJob(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container">
        <div className="card">載入中...</div>
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="container">
        <div className="card">
          <p className="status-badge status-failed">載入失敗: {error || 'Job not found'}</p>
          <Link href="/jobs" className="btn btn-secondary">返回列表</Link>
        </div>
      </div>
    )
  }

  const progressPercent = job.totalChunks > 0 
    ? Math.round((job.completedChunks / job.totalChunks) * 100) 
    : 0

  return (
    <div className="container">
      <h1>NTPE Reader - 作業詳情</h1>

      <div className="card">
        <h2>作業資��</h2>
        <table>
          <tbody>
            <tr>
              <th>作業 ID</th>
              <td>{job.jobId}</td>
            </tr>
            <tr>
              <th>��態</th>
              <td>
                <span className={`status-badge status-${job.status}`}>
                  {job.status}
                </span>
              </td>
            </tr>
            <tr>
              <th>來源��別</th>
              <td>{job.sourceIdentity}</td>
            </tr>
            <tr>
              <th>翻��設定��</th>
              <td>{job.translationProfile}</td>
            </tr>
            <tr>
              <th>Delivery 設定</th>
              <td>{job.deliverySettings}</td>
            </tr>
            <tr>
              <th>可��復</th>
              <td>{job.resumable ? '是' : '否'}</td>
            </tr>
            <tr>
              <th>建立時間</th>
              <td>{new Date(job.createdAt).toLocaleString()}</td>
            </tr>
            <tr>
              <th>更新時間</th>
              <td>{new Date(job.updatedAt).toLocaleString()}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>進度</h2>
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ 
            backgroundColor: '#e0e0e0', 
            borderRadius: '4px', 
            height: '24px', 
            overflow: 'hidden' 
          }}>
            <div style={{
              backgroundColor: job.status === 'failed' ? '#cc0000' : '#0066cc',
              height: '100%',
              width: `${progressPercent}%`,
              transition: 'width 0.3s',
            }} />
          </div>
          <p style={{ marginTop: '0.5rem' }}>
            {job.completedChunks} / {job.totalChunks} 完成 
            {job.failedChunks > 0 && <span style={{ color: '#cc0000', marginLeft: '1rem' }}>({job.failedChunks} 失敗)</span>}
          </p>
        </div>

        {job.currentChunk !== null && (
          <p>目前處理區��: {job.currentChunk} / {job.totalChunks}</p>
        )}
      </div>

      <Link href="/jobs" className="btn btn-secondary">
        返回列表
      </Link>
    </div>
  )
}