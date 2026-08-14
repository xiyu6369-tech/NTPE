'use client'

import { useState } from 'react'
import Link from 'next/link'

interface BookInfo {
  file: string
  encoding: string
  language: string
  corruptionStatus: string
  intakeStatus: string
  submissionEligible: boolean
}

export default function ImportPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [bookInfo, setBookInfo] = useState<BookInfo | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
      setBookInfo(null)
    }
  }

  const handleIntake = async () => {
    if (!selectedFile) {
      setError('��選����案')
      return
    }

    setIsProcessing(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch('/api/translation/intake', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Intake failed: ${response.statusText}`)
      }

      const data = await response.json()
      setBookInfo({
        file: selectedFile.name,
        encoding: data.encoding || 'unknown',
        language: data.language || 'unknown',
        corruptionStatus: data.corruptionStatus || 'unknown',
        intakeStatus: data.status || 'unknown',
        submissionEligible: data.submissionEligible || false,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="container">
      <h1>NTPE Reader - 書籍導入</h1>
      
      <div className="card">
        <h2>選��書籍��案</h2>
        <div className="form-group">
          <input
            type="file"
            accept=".txt,.epub"
            onChange={handleFileChange}
            disabled={isProcessing}
          />
        </div>
        
        {selectedFile && (
          <div className="form-group">
            <p>已選��: {selectedFile.name} ({formatBytes(selectedFile.size)})</p>
            <button 
              className="btn btn-primary" 
              onClick={handleIntake}
              disabled={isProcessing}
            >
              {isProcessing ? '處理中...' : '��行 Canonical Intake'}
            </button>
          </div>
        )}

        {error && (
          <div className="status-badge status-failed">
            �����: {error}
          </div>
        )}
      </div>

      {bookInfo && (
        <div className="card">
          <h2>Intake 結果</h2>
          <table>
            <tbody>
              <tr>
                <th>��案</th>
                <td>{bookInfo.file}</td>
              </tr>
              <tr>
                <th>編��</th>
                <td>{bookInfo.encoding}</td>
              </tr>
              <tr>
                <th>語言</th>
                <td>{bookInfo.language}</td>
              </tr>
              <tr>
                <th>������態</th>
                <td>{bookInfo.corruptionStatus}</td>
              </tr>
              <tr>
                <th>Intake ��態</th>
                <td>
                  <span className={`status-badge status-${bookInfo.intakeStatus}`}>
                    {bookInfo.intakeStatus}
                  </span>
                </td>
              </tr>
              <tr>
                <th>可提交</th>
                <td>{bookInfo.submissionEligible ? '是' : '否'}</td>
              </tr>
            </tbody>
          </table>

          {bookInfo.submissionEligible && (
            <Link href="/jobs/new" className="btn btn-primary">
              ��續到審��與提交
            </Link>
          )}
        </div>
      )}
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