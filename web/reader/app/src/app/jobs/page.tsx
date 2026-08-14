'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Job {
  jobId: string
  status: string
  currentChunk: number | null
  completedChunks: number
  failedChunks: number
  totalChunks: number
  sourceIdentity: string
  createdAt: string
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadJobs()
    const interval = setInterval(loadJobs, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadJobs = async () => {
    try {
      const response = await fetch('/api/translation/jobs')
      if (response.ok) {
        const data = await response.json()
        setJobs(data.jobs || [])
      }
    } catch (error) {
      console.error('Failed to load jobs:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>NTPE Reader - 作業管理</h1>

      {loading ? (
        <div className="card">載入中...</div>
      ) : jobs.length === 0 ? (
        <div className="card">
          <p>目前��有翻��作業</p>
          <Link href="/" className="btn btn-primary">導入新書籍</Link>
        </div>
      ) : (
        <div className="card table-container">
          <table>
            <thead>
              <tr>
                <th>作業 ID</th>
                <th>��態</th>
                <th>來源</th>
                <th>進度</th>
                <th>建立時間</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.jobId}>
                  <td>{job.jobId}</td>
                  <td>
                    <span className={`status-badge status-${job.status}`}>
                      {job.status}
                    </span>
                  </td>
                  <td>{job.sourceIdentity}</td>
                  <td>
                    {job.currentChunk !== null ? (
                      <>{job.currentChunk} / {job.totalChunks}</>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td>{new Date(job.createdAt).toLocaleString()}</td>
                  <td>
                    <Link href={`/jobs/${job.jobId}`} className="btn btn-secondary">
                      詳情
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}