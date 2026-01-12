/* eslint-disable unicode-bom */
import React from 'react'
import './App.css'
import logo from './assets/logo.png'
import { NotificationContainer } from './NotificationSystem'

// Use environment variable if available, otherwise use IP address
const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://43.204.100.245:8000'

function App() {
  const [activeView, setActiveView] = React.useState('call-audit') // Changed default to call-audit
  
  // Dashboard state - COMMENTED OUT
  // const [dashboardStats, setDashboardStats] = React.useState({ total_calls: 0, average_score: 0, pass_percentage: 0 })
  // const [performanceData, setPerformanceData] = React.useState([])
  // const [executives, setExecutives] = React.useState([])
  // const [callRecordings, setCallRecordings] = React.useState([])
  // const [pieChartData, setPieChartData] = React.useState([])
  // const [barChartData, setBarChartData] = React.useState([])
  // const [loading, setLoading] = React.useState(true)
  // const [error, setError] = React.useState('')
  // const [searchQuery, setSearchQuery] = React.useState('')
  
  // Executive Board filters - COMMENTED OUT
  // const [selectedAgent, setSelectedAgent] = React.useState('Lakshmi')
  // const [selectedTeam, setSelectedTeam] = React.useState('')
  // const [agentsList, setAgentsList] = React.useState([])
  // const [teamsList, setTeamsList] = React.useState([])
  // const [allCallRecordings, setAllCallRecordings] = React.useState([])
  // const [selectedCallResult, setSelectedCallResult] = React.useState(null)
  // const [isExecutiveRubricOpen, setIsExecutiveRubricOpen] = React.useState(false)
  // const [loadingCallDetails, setLoadingCallDetails] = React.useState(false)
  // const [showSuggestions, setShowSuggestions] = React.useState(false)
  // const [highlightedIndex, setHighlightedIndex] = React.useState(-1)
  
  // Notification system state
  const [notifications, setNotifications] = React.useState([])
  // eslint-disable-next-line no-unused-vars
  const [error, setError] = React.useState('') // setError is used, error variable is not
  
  // Call Audit state
  const [audioFile, setAudioFile] = React.useState(null)
  const [textFile, setTextFile] = React.useState(null)
  const [transcript, setTranscript] = React.useState('')
  const [speakerSegments, setSpeakerSegments] = React.useState([])
  const [transcriptionMetadata, setTranscriptionMetadata] = React.useState(null)
  const [result, setResult] = React.useState(null)
  const [isTranscribing, setIsTranscribing] = React.useState(false)
  const [isReviewing, setIsReviewing] = React.useState(false)
  const [isFinalizing, setIsFinalizing] = React.useState(false)
  const [stage, setStage] = React.useState('idle')
  const [uploadPct, setUploadPct] = React.useState(0)
  // eslint-disable-next-line no-unused-vars
  const [dealId, setDealId] = React.useState('') // Reserved for future use
  // eslint-disable-next-line no-unused-vars
  const [clientName, setClientName] = React.useState('') // Reserved for future use
  const [salesRep, setSalesRep] = React.useState('')
  // eslint-disable-next-line no-unused-vars
  const [callDate, setCallDate] = React.useState('') // Reserved for future use
  // eslint-disable-next-line no-unused-vars
  const [dealReview, setDealReview] = React.useState(null) // Reserved for future use
  const [finalReport, setFinalReport] = React.useState(null)
  const [isRubricOpen, setIsRubricOpen] = React.useState(false)
  const [isDragActive, setIsDragActive] = React.useState(false)
  const [activeTab, setActiveTab] = React.useState('scores') // 'scores' or 'summaries'
  const [activeExecutiveTab, setActiveExecutiveTab] = React.useState('scores') // For Executive Board popup
  const [executiveExpandedIds, setExecutiveExpandedIds] = React.useState({})
  const [auditExpandedIds, setAuditExpandedIds] = React.useState({})
  // eslint-disable-next-line no-unused-vars
  const [scoringVersion, setScoringVersion] = React.useState('v2') // Reserved for future use
  
  const audioInputRef = React.useRef(null)
  const textInputRef = React.useRef(null)

  // Notification system functions
  const showNotification = React.useCallback((type, title, message, duration = 5000) => {
    const id = Date.now() + Math.random()
    const notification = { id, type, title, message, timestamp: new Date() }
    setNotifications(prev => [...prev, notification])
    
    if (duration > 0) {
      setTimeout(() => {
        setNotifications(prev => prev.filter(n => n.id !== id))
      }, duration)
    }
    
    return id
  }, [])

  const removeNotification = React.useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  // Simple renderer to turn **bold** markers into <strong> for readability
  const renderWithBold = (value) => {
    if (value == null) return null
    const text = String(value)
    if (!text.includes('**')) return text
    const parts = text.split(/(\*\*[^*]+\*\*)/g)
    return parts.map((part, idx) => {
      const match = part.match(/^\*\*([^*]+)\*\*$/)
      if (match) {
        return <strong key={idx}>{match[1]}</strong>
      }
      return <span key={idx}>{part}</span>
    })
  }

  // Helper function to format time in seconds to MM:SS format
  const formatTime = (seconds) => {
    if (typeof seconds !== 'number' || isNaN(seconds)) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Helper function to format duration from various formats to readable format
  const formatDuration = (duration, transcriptionDuration = null) => {
    // Prefer transcriptionMetadata duration if available (most accurate)
    if (transcriptionDuration !== null && typeof transcriptionDuration === 'number') {
      const totalSeconds = transcriptionDuration
      const mins = Math.floor(totalSeconds / 60)
      const secs = Math.floor(totalSeconds % 60)
      if (mins > 0) {
        return `${mins}min${secs > 0 ? ` ${secs}s` : ''}`
      }
      return `${secs}s`
    }
    
    // Handle duration from other sources
    if (!duration || duration === 'Unknown') return 'Unknown'
    
    // If it's already a number (seconds)
    if (typeof duration === 'number') {
      const totalSeconds = duration
      const mins = Math.floor(totalSeconds / 60)
      const secs = Math.floor(totalSeconds % 60)
      if (mins > 0) {
        return `${mins}min${secs > 0 ? ` ${secs}s` : ''}`
      }
      return `${secs}s`
    }
    
    // If it's a string, try to parse it
    if (typeof duration === 'string') {
      // Check if it's already in a good format (like "30min", "5min 30s", etc.)
      if (duration.match(/^\d+min/)) {
        return duration
      }
      
      // Try to parse as seconds string
      const secondsMatch = duration.match(/^(\d+(?:\.\d+)?)\s*s(?:econds?)?$/i)
      if (secondsMatch) {
        const totalSeconds = parseFloat(secondsMatch[1])
        const mins = Math.floor(totalSeconds / 60)
        const secs = Math.floor(totalSeconds % 60)
        if (mins > 0) {
          return `${mins}min${secs > 0 ? ` ${secs}s` : ''}`
        }
        return `${secs}s`
      }
      
      // Check if it's in MM:SS format
      const timeMatch = duration.match(/^(\d+):(\d+)$/)
      if (timeMatch) {
        const mins = parseInt(timeMatch[1], 10)
        const secs = parseInt(timeMatch[2], 10)
        return `${mins}min${secs > 0 ? ` ${secs}s` : ''}`
      }
      
      // Return as-is if it seems already formatted
      return duration
    }
    
    return 'Unknown'
  }

  // Fetch dashboard data - COMMENTED OUT
  /* const fetchDashboardData = React.useCallback(async () => {
    try {
      setLoading(true)
      setError('')

      const [statsRes, perfRes, execRes, recordingsRes, pieRes, barRes] = await Promise.all([
        fetch(`${API_BASE}/dashboard/stats`),
        fetch(`${API_BASE}/dashboard/performance`),
        fetch(`${API_BASE}/dashboard/executives`),
        fetch(`${API_BASE}/dashboard/call-recordings`),
        fetch(`${API_BASE}/dashboard/charts/pie`).catch(() => ({ ok: false })),
        fetch(`${API_BASE}/dashboard/charts/bar`).catch(() => ({ ok: false }))
      ])

      if (!statsRes.ok || !perfRes.ok || !execRes.ok || !recordingsRes.ok) {
        throw new Error('Failed to fetch dashboard data')
      }

      const [stats, perf, exec, recordings, pie, bar] = await Promise.all([
        statsRes.json(),
        perfRes.json(),
        execRes.json(),
        recordingsRes.json(),
        pieRes.ok ? pieRes.json() : [],
        barRes.ok ? barRes.json() : []
      ])

      setDashboardStats(stats)
      const normalizedPerf = Array.isArray(perf) ? perf.map(d => ({
        month: d.month || d.Month || 'Unknown',
        score: typeof d.score === 'number' ? d.score : (d.avg_score || d.Score || 0)
      })) : []
      setPerformanceData(normalizedPerf)
      setExecutives(exec)
      setCallRecordings(recordings)
      setPieChartData(pie)
      setBarChartData(bar)
    } catch (e) {
      setError(e?.message || 'Failed to load dashboard data')
      console.error('Dashboard fetch error:', e)
    } finally {
      setLoading(false)
    }
  }, []) */

  // Fetch Executive Board data - COMMENTED OUT
  /* const fetchExecutiveBoardData = React.useCallback(async () => {
    try {
      // Build agent filter for API calls - pass empty string or 'All' when "All" is selected
      const agentParam = selectedAgent && selectedAgent !== 'All' ? selectedAgent : ''
      const agentQuery = agentParam ? `?agent=${encodeURIComponent(agentParam)}` : ''
      const chartAgentParam = selectedAgent === 'All' ? '' : (agentParam || '')
      
      const [allCallsRes, agentsRes, teamsRes, pieRes, barRes] = await Promise.all([
        fetch(`${API_BASE}/dashboard/call-recordings/all${agentQuery}`),
        fetch(`${API_BASE}/dashboard/filters/agents`),
        fetch(`${API_BASE}/dashboard/filters/teams`),
        fetch(`${API_BASE}/dashboard/charts/pie/filtered${chartAgentParam ? `?agent=${encodeURIComponent(chartAgentParam)}` : ''}${selectedTeam ? `${chartAgentParam ? '&' : '?'}team=${encodeURIComponent(selectedTeam)}` : ''}`),
        fetch(`${API_BASE}/dashboard/charts/bar/filtered${chartAgentParam ? `?agent=${encodeURIComponent(chartAgentParam)}` : ''}${selectedTeam ? `${chartAgentParam ? '&' : '?'}team=${encodeURIComponent(selectedTeam)}` : ''}`)
      ])

      if (allCallsRes.ok) {
        const allCalls = await allCallsRes.json()
        setAllCallRecordings(allCalls)
      }

      if (agentsRes.ok) {
        const agents = await agentsRes.json()
        setAgentsList(agents)
      }

      if (teamsRes.ok) {
        const teams = await teamsRes.json()
        setTeamsList(teams)
      }

      if (pieRes.ok) {
        const pie = await pieRes.json()
        setPieChartData(pie)
      }

      if (barRes.ok) {
        const bar = await barRes.json()
        setBarChartData(bar)
      }
    } catch (e) {
      console.error('Executive Board fetch error:', e)
    }
  }, [selectedAgent, selectedTeam]) */

  // Dashboard useEffect - COMMENTED OUT
  /* React.useEffect(() => {
    if (activeView !== 'call-audit' && activeView !== 'executive-board') {
      fetchDashboardData()
      const interval = setInterval(fetchDashboardData, 30000)
      return () => clearInterval(interval)
    }
  }, [fetchDashboardData, activeView]) */

  // Fetch deal details for clicked call - COMMENTED OUT
  /* const fetchCallDetails = React.useCallback(async (dealId, callData) => {
    try {
      setLoadingCallDetails(true)
      // Try new call-records endpoint first, fallback to old endpoint
      let response = await fetch(`${API_BASE}/call-records/${dealId}`)
      if (!response.ok) {
        // Fallback to old endpoint
        response = await fetch(`${API_BASE}/deals/${dealId}`)
        if (!response.ok) {
          throw new Error('Failed to fetch call details')
        }
      }
      const dealData = await response.json()
      
      // Format the data to match the result structure used in Call Audit
      const criteria_scores = dealData.criteria_scores || []
      // Extract fatal error info from metadata if available
      const metadata = dealData.metadata || {}
      const fatalErrorReason = metadata.fatal_error_reason || (metadata.fatal_parameter_failed && metadata.failed_fatal_parameters ? 
        `Score set to 0 due to FATAL parameter failure(s): ${metadata.failed_fatal_parameters.join(', ')}` : null)
      const formattedResult = {
        rubric_title: 'Empire Pre-Sales Call — Quality Rubric',
        total_points: dealData.rubric_max_score || 100,
        total_score: dealData.rubric_score || 0,
        criteria: criteria_scores.map((c, i) => ({
          id: c.id || String(i),
          name: c.name || '',
          description: c.description || '',
          max_points: c.max_points || 0,
          points_awarded: c.points_awarded || 0,
          rationale: c.rationale || ''
        })),
        metadata: { transcript: dealData.transcript || '', deal_id: dealData.deal_id, ...metadata },
        passed: (dealData.rubric_percentage || 0) >= 60,
        fatal_error_reason: fatalErrorReason,
        failed_fatal_parameters: metadata.failed_fatal_parameters || []
      }
      
      setSelectedCallResult({
        result: formattedResult,
        callData: callData,
        dealData: dealData
      })
      setActiveExecutiveTab('scores') // Reset to scores tab when opening
      setIsExecutiveRubricOpen(true)
    } catch (e) {
      setError(e?.message || 'Failed to load call details')
      console.error('Call details fetch error:', e)
    } finally {
      setLoadingCallDetails(false)
    }
  }, []) */

  // Executive Board useEffect - COMMENTED OUT
  /* React.useEffect(() => {
    if (activeView === 'executive-board') {
      // Clear any old chart data first
      setPieChartData([])
      setBarChartData([])
      // Then fetch Executive Board data
      fetchExecutiveBoardData()
      const interval = setInterval(fetchExecutiveBoardData, 30000)
      return () => clearInterval(interval)
    }
  }, [fetchExecutiveBoardData, activeView]) */

  // Chart calculations - COMMENTED OUT
  /* const chartData = React.useMemo(() => {
    if (!performanceData || performanceData.length === 0) {
      return { points: [], maxValue: 100, hasData: false }
    }
    
    const scores = performanceData.map(d => d.score || 0).filter(s => s >= 0)
    if (scores.length === 0) {
      return { points: [], maxValue: 100, hasData: false }
    }
    
    const maxScore = Math.max(...scores)
    const minScore = Math.min(...scores)
    const range = maxScore - minScore || 100
    const maxValue = Math.max(100, Math.ceil((maxScore + range * 0.2) / 25) * 25)
    
    const points = performanceData.map((d, i) => {
      const score = d.score || 0
      const xPercent = performanceData.length > 1 ? (i / (performanceData.length - 1)) : 0.5
      return {
        x: xPercent,
        y: score / maxValue,
        label: d.month || `Month ${i + 1}`,
        value: score
      }
    })
    
    return { points, maxValue, hasData: true }
  }, [performanceData]) */

  // Call Audit functions
  const resetForNewInput = React.useCallback(() => {
    setTranscript('')
    setSpeakerSegments([])
    setTranscriptionMetadata(null)
    setResult(null)
    setIsRubricOpen(false)
    setDealReview(null)
    setFinalReport(null)
    setError('')
    setStage('idle')
    setUploadPct(0)
  }, [])

  const loadTextFile = React.useCallback((file) => {
    if (!file) {
      setTextFile(null)
      setAudioFile(null)
      resetForNewInput()
      return
    }
    setTextFile(file)
    setAudioFile(null)
    resetForNewInput()
    showNotification('info', 'File Upload', `Processing text file: ${file.name}`, 3000)
    const reader = new FileReader()
    reader.onload = () => {
      const content = String(reader.result || '')
      setTranscript(content)
      showNotification('success', 'File Uploaded Successfully', `Text file "${file.name}" loaded successfully. ${content.length} characters read.`, 4000)
    }
    reader.onerror = () => {
      const errorMsg = `Unable to read ${file.name}`
      setError(errorMsg)
      showNotification('error', 'File Upload Error', errorMsg, 6000)
    }
    reader.readAsText(file)
  }, [resetForNewInput, showNotification])

  const loadAudioFile = React.useCallback((file) => {
    if (!file) {
      setAudioFile(null)
      setTextFile(null)
      resetForNewInput()
      return
    }
    setAudioFile(file)
    setTextFile(null)
    resetForNewInput()
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2)
    showNotification('info', 'Audio File Selected', `Audio file "${file.name}" (${fileSizeMB} MB) ready for transcription.`, 3000)
  }, [resetForNewInput, showNotification])

  const onAudioSelected = (e) => {
    const f = e.target.files && e.target.files[0]
    // Only update if a file was actually selected (not canceled)
    if (f) {
      loadAudioFile(f)
    }
    // Reset the input value so the same file can be selected again if needed
    e.target.value = ''
  }

  const onTextSelected = (e) => {
    const f = e.target.files && e.target.files[0]
    // Only update if a file was actually selected (not canceled)
    if (f) {
      loadTextFile(f)
    }
    // Reset the input value so the same file can be selected again if needed
    e.target.value = ''
  }

  const handleDragOver = (event) => {
    event.preventDefault()
    event.stopPropagation()
    setIsDragActive(true)
  }

  const handleDragLeave = (event) => {
    event.preventDefault()
    event.stopPropagation()
    setIsDragActive(false)
  }

  const handleFileDrop = (event) => {
    event.preventDefault()
    event.stopPropagation()
    setIsDragActive(false)
    const files = event.dataTransfer?.files
    if (!files || !files.length) return
    const file = files[0]
    const name = file.name || 'file'
    if ((file.type && file.type.startsWith('audio/')) || /\.(wav|mp3|m4a|aac|ogg)$/i.test(name)) {
      loadAudioFile(file)
    } else if (file.type === 'text/plain' || name.toLowerCase().endsWith('.txt')) {
      loadTextFile(file)
    } else {
      const errorMsg = `Unsupported file type: ${name}`
      setError(errorMsg)
      showNotification('error', 'Unsupported File Type', `File "${name}" is not supported. Please upload an audio file (.wav, .mp3, .m4a, .aac, .ogg) or text file (.txt).`, 6000)
    }
  }

  const transcribeAudio = async () => {
    if (!audioFile) {
      showNotification('warning', 'No Audio File', 'Please select an audio file before starting transcription.', 4000)
      return
    }
    setIsTranscribing(true)
    setError('')
    setStage('uploading')
    setUploadPct(0)
    showNotification('info', 'Transcription Started', `Starting transcription process for "${audioFile.name}". Please wait...`, 0)
    try {
      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open('POST', `${API_BASE}/transcribe-audio`)
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            setUploadPct(Math.round((e.loaded / e.total) * 100))
          }
        }
        xhr.onloadstart = () => setStage('uploading')
        xhr.upload.onload = () => setStage('processing')
        xhr.onerror = () => reject(new Error('Network error'))
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const json = JSON.parse(xhr.responseText)
              // New API returns 'transcription' field with speaker_segments and timing info
              const t = (json && json.transcription) || ''
              if (t) {
                setTranscript(t)
                // Store speaker segments and timing data for display and analysis
                if (json.speaker_segments && json.speaker_segments.length > 0) {
                  setSpeakerSegments(json.speaker_segments)
                  setTranscriptionMetadata({
                    duration: json.duration,
                    language_code: json.language_code,
                    speaker_count: json.speaker_count || json.speaker_segments.length,
                    metadata: json.metadata
                  })
                  console.log('Speaker segments received:', json.speaker_segments.length, 'segments')
                  console.log('Speakers detected:', json.speaker_count || 'unknown')
                  console.log('Duration:', json.duration, 'seconds')
                  console.log('Language:', json.language_code)
                  
                  // Format transcript with speaker labels for display
                  const formattedTranscript = json.speaker_segments.map(seg => {
                    const timeStr = `[${formatTime(seg.start_time)} - ${formatTime(seg.end_time)}]`
                    return `${seg.speaker} ${timeStr}\n${seg.text}`
                  }).join('\n\n')
                  
                  console.log(`Formatted transcript length: ${formattedTranscript.length} characters`)
                  console.log(`Number of segments formatted: ${json.speaker_segments.length}`)
                  console.log(`Last segment:`, json.speaker_segments[json.speaker_segments.length - 1])
                  
                  setTranscript(formattedTranscript)
                  showNotification('success', 'Transcription Completed', `Successfully transcribed audio. Detected ${json.speaker_count || json.speaker_segments.length} speaker(s), ${json.speaker_segments.length} segments, duration: ${formatTime(json.duration)}.`, 6000)
                } else {
                  setSpeakerSegments([])
                  setTranscriptionMetadata(null)
                  showNotification('warning', 'Transcription Completed', 'Transcription completed but no speaker segments were detected.', 5000)
                }
              } else {
                reject(new Error('No transcription received from API'))
              }
              setResult(null)
              setIsRubricOpen(false)
              setFinalReport(null)
              setStage('done')
              resolve()
            } catch (err) {
              reject(err)
            }
          } else {
            reject(new Error(`${xhr.status} ${xhr.responseText}`))
          }
        }
        const form = new FormData()
        form.append('file', audioFile)
        xhr.send(form)
      })
    } catch (e) {
      const errorMsg = e?.message || 'Audio transcription failed'
      setError(errorMsg)
      showNotification('error', 'Transcription Failed', `Failed to transcribe audio: ${errorMsg}. Please check your file and try again.`, 8000)
    } finally {
      setIsTranscribing(false)
    }
  }

  const scoreTranscript = async () => {
    setIsReviewing(true)
    setError('')
    try {
      if (!transcript || !transcript.trim()) {
        setError('Transcript is empty. Transcribe or upload text first.')
        return
      }

      // Build payload expected by the new /score-transcript endpoint
      const payload = {
        transcription: transcript,
        // speaker_segments is optional for scoring, but include if available
        speaker_segments: speakerSegments && speakerSegments.length > 0 ? speakerSegments : [],
        version: "v2"  // Add version selection
      }

      const resp = await fetch(`${API_BASE}/score-transcript`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!resp.ok) throw new Error(`${resp.status} ${await resp.text()}`)

      const json = await resp.json()

      // Map API response from score_transcript() to UI-friendly structure
      setDealReview(null)
      setIsRubricOpen(false)
      setResult({
        rubric_title: json.rubric_title || 'Empire Pre-Sales Call — Quality Rubric',
        total_points: json.total_points || 100,
        total_score: json.total_score || 0,
        criteria: (json.criteria_scores || []).map((c, i) => ({
          id: c.id || String(i),
          name: c.name || '',
          description: c.rationale || '',
          max_points: c.max_points || 0,
          points_awarded: c.points_awarded || 0,
          rationale: c.rationale || '',
          response: c.response || undefined
        })),
        metadata: json.metadata || {},
        passed: (json.percentage || 0) >= 60,
        yes_no_na_responses: json.yes_no_na_responses || {},
        fatal_error_reason: json.fatal_error_reason || null,
        failed_fatal_parameters: json.failed_fatal_parameters || [],
        failed_fatal_details: json.failed_fatal_details || []
      })
    } catch (e) {
      setError(e?.message || 'Scoring failed')
    } finally {
      setIsReviewing(false)
    }
  }

  const generateFinalReport = async () => {
    setError('')
    setFinalReport(null)
    if (!transcript || !transcript.trim()) {
      setError('Transcript is empty. Transcribe or upload text first.')
      return
    }
    setIsFinalizing(true)
    try {
      if (!result || result.total_score === undefined) {
        setError('Please score the transcript first using "Score Transcript" before generating report.')
        return
      }

      // Build payload for /generate-report endpoint
      const transcriptPayload = {
        transcription: transcript,
        speaker_segments: speakerSegments && speakerSegments.length > 0 ? speakerSegments : []
      }

      const scorePayload = {
        rubric_title: result.rubric_title,
        total_points: result.total_points,
        total_score: result.total_score,
        percentage: result.total_points ? Math.round((result.total_score / result.total_points) * 10000) / 100 : 0,
        criteria_scores: (result.criteria || []).map((c) => ({
          id: c.id,
          name: c.name,
          max_points: c.max_points,
          points_awarded: c.points_awarded,
          score: c.points_awarded,
          response: c.response,
          rationale: c.rationale
        })),
        yes_no_na_responses: result.yes_no_na_responses || {},
        metadata: result.metadata || {}
      }

      const resp = await fetch(`${API_BASE}/generate-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript_data: transcriptPayload,
          score_data: scorePayload
        })
      })

      if (!resp.ok) throw new Error(`${resp.status} ${await resp.text()}`)
      const json = await resp.json()

      // Store only summaries object (overall, agent, client)
      const summaries = json.summaries || json
      setFinalReport(summaries)
    } catch (e) {
      const errorMsg = e?.message || 'Final report generation failed'
      setError(errorMsg)
    } finally {
      setIsFinalizing(false)
    }
  }

  const percent = React.useMemo(() => {
    if (!result || !result.total_points) return 0
    return Math.round((result.total_score / result.total_points) * 100)
  }, [result])

  // Get color based on overall score percentage (0–100)
  const getScoreColor = React.useCallback((scorePercent) => {
    if (scorePercent > 75) return '#22c55e' // green for > 75
    if (scorePercent >= 50) return '#f59e0b' // yellow/orange for 50–75
    return '#ef4444' // red for < 50
  }, [])

  const scoreColor = result ? getScoreColor(percent) : '#666'

  const criteria = result?.criteria || []
  const canTranscribe = !!audioFile && !isTranscribing
  // Scoring now only depends on having a transcript; deal metadata is optional
  const canScore = (!!transcript && !isReviewing) || (!!textFile && !isReviewing)
  const canFinalize = !!transcript && !isFinalizing && !!result && result.total_score !== undefined
  const isBusy = isTranscribing || isReviewing || isFinalizing

  return (
    <div className="erp-root">
      <div className="erp-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo-container">
            <img src={logo} alt="Company Logo" className="sidebar-logo" />
          </div>
          <div className="sidebar-subtitle">ReaaEstate Pre-Sales Call Audit System</div>
        </div>
        <nav className="sidebar-nav">
          {/* Dashboard button - COMMENTED OUT */}
          {/* <button
            className={`nav-item ${activeView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveView('dashboard')}
          >
            Dashboard
          </button> */}
          {/* Executive Board button - COMMENTED OUT */}
          {/* <button
            className={`nav-item ${activeView === 'executive-board' ? 'active' : ''}`}
            onClick={() => setActiveView('executive-board')}
          >
            Executive Board
          </button> */}
          <button
            className={`nav-item ${activeView === 'call-audit' ? 'active' : ''}`}
            onClick={() => setActiveView('call-audit')}
          >
            Call Audit
          </button>
        </nav>
      </div>

      <div className="erp-main">
        {/* Notification Container */}
        <NotificationContainer notifications={notifications} onClose={removeNotification} />

        {/* Dashboard loading - COMMENTED OUT */}
        {/* {loading && activeView !== 'call-audit' && (
          <div className="loading-overlay">
            <div className="loading-card">
              <div className="spinner" />
              <div>Loading dashboard...</div>
            </div>
          </div>
        )} */}

        {/* Temporarily commented out error banner - keeping screen empty on fetch errors */}
        {/* {error && (
          <div className="error-banner">
            {error}
          </div>
        )} */}

        {/* Dashboard View - COMMENTED OUT */}
        {/* {activeView === 'dashboard' && (
          <div className="dashboard-content">
            <div className="metrics-row">
              <div className="metric-card">
                <div className="metric-label">Total Calls</div>
                <div className="metric-value">{dashboardStats.total_calls}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Average Score</div>
                <div className="metric-value">{dashboardStats.average_score}</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Pass Percentage</div>
                <div className="metric-value">{dashboardStats.pass_percentage}</div>
              </div>
            </div>

            <div className="middle-row">
              <div className="chart-card">
                <div className="card-title">Performance Chart</div>
                <div className="chart-container">
                  {chartData.hasData && chartData.points.length > 0 ? (
                    <div className="chart-wrapper">
                      <svg className="chart-svg" viewBox="0 0 450 250" preserveAspectRatio="xMidYMid meet">
                        <text x="20" y="125" textAnchor="middle" fontSize="12" fill="#333" fontWeight="600" transform="rotate(-90, 20, 125)">Score</text>
                        <text x="225" y="245" textAnchor="middle" fontSize="12" fill="#333" fontWeight="600">Month</text>
                        {[0, 25, 50, 75, 100].map((val) => {
                          const y = 220 - (val / 100) * 200
                          return (
                            <g key={val}>
                              <line x1="50" y1={y} x2="400" y2={y} stroke="#CCCCCC" strokeWidth="1" />
                              <text x="45" y={y + 4} textAnchor="end" fontSize="11" fill="#666" fontWeight="500">{val}</text>
                            </g>
                          )
                        })}
                        <line x1="50" y1="20" x2="50" y2="220" stroke="#999" strokeWidth="2" />
                        <line x1="50" y1="220" x2="400" y2="220" stroke="#999" strokeWidth="2" />
                        {chartData.points.map((p, i) => {
                          const x = 50 + p.x * 350
                          return (
                            <g key={i}>
                              <line x1={x} y1="220" x2={x} y2="225" stroke="#999" strokeWidth="1" />
                              <text x={x} y="238" textAnchor="middle" fontSize="11" fill="#666" fontWeight="500">{p.label}</text>
                            </g>
                          )
                        })}
                        {chartData.points.length > 1 && (
                          <polyline
                            points={chartData.points.map((p) => {
                              const x = 50 + p.x * 350
                              const y = 220 - (p.y * 200)
                              return `${x},${y}`
                            }).join(' ')}
                            fill="none"
                            stroke="#ff6b9d"
                            strokeWidth="3"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        )}
                        {chartData.points.map((p, i) => {
                          const x = 50 + p.x * 350
                          const y = 220 - (p.y * 200)
                          return (
                            <g key={i}>
                              <circle cx={x} cy={y} r="5" fill="#ff6b9d" stroke="#fff" strokeWidth="2" />
                              <title>{`${p.label}: ${p.value.toFixed(1)}`}</title>
                            </g>
                          )
                        })}
                      </svg>
                    </div>
                  ) : (
                    <div className="chart-empty">No performance data available</div>
                  )}
                </div>
              </div>

              <div className="scoreboard-card">
                <div className="card-title">Executive Scoreboard</div>
                <div className="scoreboard-table">
                  <div className="table-header">
                    <div className="table-col">Name</div>
                    <div className="table-col">Rank</div>
                    <div className="table-col">Score</div>
                  </div>
                  {executives.map((exec, idx) => (
                    <div key={idx} className="table-row">
                      <div className="table-col">{exec.name}</div>
                      <div className="table-col">{exec.rank}{exec.rank === 1 ? 'st' : exec.rank === 2 ? 'nd' : exec.rank === 3 ? 'rd' : 'th'} Rank</div>
                      <div className="table-col">{exec.score}</div>
                    </div>
                  ))}
                  {executives.length === 0 && (
                    <div className="table-row empty">
                      <div className="table-col">No executive data available</div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="recordings-card">
              <div className="card-title">Latest Call Recordings</div>
              <div className="recordings-table">
                <div className="recordings-header">
                  <div className="recordings-col">Executive Name</div>
                  <div className="recordings-col">Call Record</div>
                  <div className="recordings-col">Date</div>
                  <div className="recordings-col">Duration</div>
                </div>
                {callRecordings.map((recording, idx) => (
                  <div 
                    key={idx} 
                    className="recordings-row clickable-row"
                    onClick={() => {
                        const dealId = recording.call_record
                        if (dealId) {
                          fetchCallDetails(dealId, recording)
                        }
                    }}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="recordings-col">{recording.executive_name}</div>
                    <div className="recordings-col">{recording.call_record}</div>
                    <div className="recordings-col">{recording.date}</div>
                    <div className="recordings-col">
                      <span className="duration-badge">{recording.duration}</span>
                    </div>
                  </div>
                ))}
                {callRecordings.length === 0 && (
                  <div className="recordings-row empty">
                    <div className="recordings-col">No call recordings available</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )} */}
        {/* End of Dashboard View - COMMENTED OUT */}

        {/* Loading indicator for call details - COMMENTED OUT */}
        {/* {loadingCallDetails && (
          <div className="loading-overlay">
            <div className="loading-card">
              <div className="spinner" />
              <div>Loading call details...</div>
            </div>
          </div>
        )} */}

        {/* Executive Board Rubric Popup - COMMENTED OUT */}
        {false && (() => {
          const _isExecutiveRubricOpen = false
          const _selectedCallResult = null
          const setIsExecutiveRubricOpen = () => {}
          return _isExecutiveRubricOpen && _selectedCallResult && _selectedCallResult.result && (() => {
          const selectedCallResult = _selectedCallResult
          const result = selectedCallResult?.result
          const callData = selectedCallResult?.callData
          const dealData = selectedCallResult?.dealData
          
          // Extract report data from dealData
          let reportData = null
          if (dealData?.report_data) {
            try {
              reportData = typeof dealData.report_data === 'string' ? JSON.parse(dealData.report_data) : dealData.report_data
            } catch (e) {
              console.error('Failed to parse report_data:', e)
            }
          } else if (dealData?.final_report) {
            reportData = typeof dealData.final_report === 'string' ? JSON.parse(dealData.final_report) : dealData.final_report
          }
          
          // Categorize criteria based on Empire rubric structure
          const categorizedCriteria = {
            'Greetings': [],
            'Project Knowledge': [],
            'Process Knowledge': [],
            'Soft Skills': [],
            'Closing': []
          }
          
          // Exact mapping based on rubric criteria names
          const categoryMap = {
            'Greetings': ['Greeting & Introduced Self', 'Brand Intro', 'Purpose of Call', 'Reaching Decision Maker/RPC'],
            'Project Knowledge': ['Effective Probing', 'Project Knowledge', 'Objection Handling', 'Follow Up'],
            'Process Knowledge': ['Call Control', 'Disposition'],
            'Soft Skills': ['Enthusiasm', 'Active Listening', 'Confidence', 'Professional', 'Language and Grammar', 'Clarity of Speech', 'Tone and Voice Modulation'],
            'Closing': ['Thanking Customer', 'Closing Script']
          }
          
          const criteria = result.criteria || []
          criteria.forEach(c => {
            const name = c.name || ''
            for (const [category, names] of Object.entries(categoryMap)) {
              if (names.some(n => name.includes(n) || n.includes(name))) {
                categorizedCriteria[category].push(c)
                break
              }
            }
          })

          // Determine color for each criterion based on percentage of max score
          // 0-50%: red, 50-75%: yellow, 75-100%: green
          const getScoreColor = (criterion) => {
            if (!criterion || typeof criterion.points_awarded !== 'number' || typeof criterion.max_points !== 'number') return '#ef4444'
            if (criterion.max_points === 0) return '#ef4444'
            const percentage = (criterion.points_awarded / criterion.max_points) * 100
            if (percentage >= 75) return '#22c55e' // green for 75-100%
            if (percentage >= 50) return '#fbbf24' // yellow for 50-75%
            return '#ef4444' // red for 0-50%
          }

          const fileName = callData?.call_record || dealData?.deal_id || 'Unknown'
          // Try to get duration from dealData (from scoring/transcription) first, then callData
          // dealData might have duration in seconds from transcription, callData might have it as string
          const duration = formatDuration(dealData?.duration || callData?.duration)
          const callDateDisplay = callData?.date || dealData?.call_date || 'Unknown'
          const salesRepName = callData?.sales_rep || callData?.executive_name || dealData?.sales_rep || 'Unknown'

          return (
            <div className="modal-backdrop" onClick={() => setIsExecutiveRubricOpen(false)}>
              <div className="modal-card rubric-modal-new" onClick={(e) => e.stopPropagation()}>
                <div className="modal-head">
                  <div className="modal-title">Call Review Report</div>
                  <button className="modal-close" onClick={() => setIsExecutiveRubricOpen(false)}>x</button>
                </div>
                
                {/* Tab Navigation */}
                <div className="modal-tabs" style={{ display: 'flex', gap: '8px', padding: '0 24px', borderBottom: '1px solid #e5e7eb', marginBottom: '16px' }}>
                  <button
                    className={`modal-tab ${activeExecutiveTab === 'scores' ? 'active' : ''}`}
                    onClick={() => setActiveExecutiveTab('scores')}
                    style={{
                      padding: '12px 24px',
                      border: 'none',
                      background: 'transparent',
                      cursor: 'pointer',
                      borderBottom: activeExecutiveTab === 'scores' ? '2px solid #ff6b9d' : '2px solid transparent',
                      color: activeExecutiveTab === 'scores' ? '#ff6b9d' : '#666',
                      fontWeight: activeExecutiveTab === 'scores' ? 600 : 400,
                      fontSize: '14px'
                    }}
                  >
                    Scores
                  </button>
                  <button
                    className={`modal-tab ${activeExecutiveTab === 'summaries' ? 'active' : ''}`}
                    onClick={() => setActiveExecutiveTab('summaries')}
                    disabled={!reportData}
                    style={{
                      padding: '12px 24px',
                      border: 'none',
                      background: 'transparent',
                      cursor: reportData ? 'pointer' : 'not-allowed',
                      borderBottom: activeExecutiveTab === 'summaries' ? '2px solid #ff6b9d' : '2px solid transparent',
                      color: reportData ? (activeExecutiveTab === 'summaries' ? '#ff6b9d' : '#666') : '#ccc',
                      fontWeight: activeExecutiveTab === 'summaries' ? 600 : 400,
                      fontSize: '14px',
                      opacity: reportData ? 1 : 0.5
                    }}
                  >
                    Summaries
                  </button>
                </div>
                
                <div className="rubric-modal-content">
                  {/* Left Panel */}
                  <div className="rubric-left-panel">
                    <div className="executive-info">
                      <div className="executive-name">{salesRepName}</div>
                      <div className="executive-team">Team 1</div>
                    </div>
                    
                    <div className="call-details-box">
                      <div className="call-details-header">Call Details</div>
                      <div className="call-detail-item">
                        <span className="call-detail-label">File Name:</span>
                        <span className="call-detail-value">{fileName}</span>
                      </div>
                      <div className="call-detail-item">
                        <span className="call-detail-label">Duration:</span>
                        <span className="call-detail-value">{duration}</span>
                      </div>
                      <div className="call-detail-item">
                        <span className="call-detail-label">Date:</span>
                        <span className="call-detail-value">{callDateDisplay}</span>
                      </div>
                    </div>

                    <div className="total-score-box">
                      <div className="total-score-label">TOTAL SCORE</div>
                      <div 
                        className="total-score-value" 
                        style={{ 
                          color: result.total_points > 0 ? (() => {
                            const percentage = (result.total_score / result.total_points) * 100
                            if (percentage >= 75) return '#22c55e' // green for 75-100%
                            if (percentage >= 50) return '#fbbf24' // yellow for 50-75%
                            return '#ef4444' // red for 0-50%
                          })() : '#ef4444'
                        }}
                      >
                        {result.total_score} / {result.total_points}
                      </div>
                      {result.fatal_error_reason && result.total_score === 0 && (
                        <div style={{
                          marginTop: '12px',
                          padding: '10px',
                          background: '#fef2f2',
                          border: '2px solid #ef4444',
                          borderRadius: '6px',
                          color: '#991b1b',
                          fontSize: '11px',
                          lineHeight: '1.4',
                          fontWeight: 600
                        }}>
                          <div style={{ marginBottom: '4px', fontWeight: 700 }}>⚠️ FATAL ERROR</div>
                          <div style={{ fontWeight: 500 }}>{result.fatal_error_reason}</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right Panel */}
                  <div className="rubric-right-panel">
                    {activeExecutiveTab === 'scores' ? (
                      Object.entries(categorizedCriteria).map(([category, categoryCriteria]) => (
                        categoryCriteria.length > 0 && (
                          <div 
                            key={category} 
                            className="rubric-category-group"
                          >
                            <div className="rubric-category-header">
                              {category}
                            </div>
                            <div className="rubric-criteria-container">
                              {categoryCriteria.map((c) => {
                                const scoreColorValue = getScoreColor(c)
                                const isExpanded = executiveExpandedIds[c.id]
                                return (
                                  <div 
                                    key={c.id} 
                                    className={`rubric-criterion-item ${isExpanded ? 'expanded' : ''}`}
                                  >
                                    <div className="rubric-criterion-main">
                                      <button
                                        type="button"
                                        className="criterion-toggle-btn"
                                        onClick={() => setExecutiveExpandedIds(prev => {
                                          const newState = { ...prev }
                                          if (newState[c.id]) {
                                            delete newState[c.id]
                                          } else {
                                            newState[c.id] = true
                                          }
                                          return newState
                                        })}
                                      >
                                        <span className={`arrow-icon ${isExpanded ? 'expanded' : ''}`}>
                                          {isExpanded ? '▾' : '▸'}
                                        </span>
                                        <span className="rubric-criterion-name">{c.name}</span>
                                      </button>
                                      <span 
                                        className="rubric-criterion-score" 
                                        style={{ color: scoreColorValue, fontWeight: 700 }}
                                      >
                                        {c.points_awarded} / {c.max_points}
                                      </span>
                                    </div>
                                    {isExpanded && c.rationale && (
                                      <div className="rubric-criterion-rationale">
                                        {renderWithBold(c.rationale)}
                                      </div>
                                    )}
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        )
                      ))
                    ) : (
                      reportData ? (() => {
                        const summaries = reportData.summaries || reportData
                        const overallSummary = summaries.overall_summary
                        const clientSummary = summaries.client_summary
                        const agentSummary = summaries.agent_summary
                        const hasAgentBulletStructure = agentSummary && Array.isArray(agentSummary.well_performed)
                        return (
                        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                          {overallSummary && (
                            <div>
                              <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: '#333' }}>Overall Summary</h3>
                              <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#555', whiteSpace: 'pre-wrap' }}>
                                {renderWithBold(overallSummary)}
                              </div>
                            </div>
                          )}
                          {clientSummary && (
                            <div>
                              <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: '#333' }}>Client Summary</h3>
                              <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#555', whiteSpace: 'pre-wrap' }}>
                                {renderWithBold(clientSummary)}
                              </div>
                            </div>
                          )}
                          {agentSummary && (
                            <div>
                              <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: '#333' }}>Agent Summary</h3>
                              {hasAgentBulletStructure ? (
                                <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#555' }}>
                                  <div style={{ marginBottom: '8px' }}>
                                    <strong>Well Performed:</strong>
                                    <ul>
                                      {agentSummary.well_performed.map((item, idx) => (
                                        <li key={`exec-wp-${idx}`}>{renderWithBold(item)}</li>
                                      ))}
                                    </ul>
                                  </div>
                                  <div>
                                    <strong>Areas of Improvement:</strong>
                                    <ul>
                                      {(agentSummary.areas_of_improvement || []).map((item, idx) => (
                                        <li key={`exec-ai-${idx}`}>{renderWithBold(item)}</li>
                                      ))}
                                    </ul>
                                  </div>
                                </div>
                              ) : (
                                <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#555', whiteSpace: 'pre-wrap' }}>
                                  {renderWithBold(agentSummary)}
                                </div>
                              )}
                            </div>
                          )}
                          {!overallSummary && !clientSummary && !agentSummary && (
                            <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
                              No summaries available for this call.
                            </div>
                          )}
                        </div>
                        )
                      })() : (
                        <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
                          No summaries available for this call.
                        </div>
                      )
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })()
        })()}
        {/* End of Executive Board Rubric Popup - COMMENTED OUT */}

        {/* Executive Board View - COMMENTED OUT */}
        {false && (() => {
          const _activeView = 'call-audit'
          const searchQuery = ''
          const setSearchQuery = () => {}
          const setShowSuggestions = () => {}
          const setHighlightedIndex = () => {}
          const highlightedIndex = -1
          const showSuggestions = false
          const agentsList = []
          const allCallRecordings = []
          const selectedAgent = ''
          const setSelectedAgent = () => {}
          const teamsList = []
          const selectedTeam = ''
          const setSelectedTeam = () => {}
          const fetchCallDetails = () => {}
          const pieChartData = []
          const barChartData = []
          return _activeView === 'executive-board' && (
          <div className="executive-board-content">
            <div className="top-bar">
              <div className="search-container">
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search by Name..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value)
                    setShowSuggestions(e.target.value.length > 0)
                    setHighlightedIndex(-1)
                  }}
                  onFocus={() => {
                    if (searchQuery.length > 0) {
                      setShowSuggestions(true)
                    }
                  }}
                  onBlur={() => {
                    // Delay hiding suggestions to allow click events
                    setTimeout(() => {
                      setShowSuggestions(false)
                      setHighlightedIndex(-1)
                    }, 200)
                  }}
                  onKeyDown={(e) => {
                    // Get suggestions for keyboard navigation
                    const allNames = new Set()
                    agentsList.forEach(name => {
                      if (name && typeof name === 'string') {
                        allNames.add(name)
                      }
                    })
                    allCallRecordings.forEach(rec => {
                      if (rec.executive_name) allNames.add(rec.executive_name)
                      if (rec.sales_rep) allNames.add(rec.sales_rep)
                    })
                    
                    const suggestions = Array.from(allNames)
                      .filter(name => name.toLowerCase().startsWith(searchQuery.toLowerCase()))
                      .sort()
                      .slice(0, 10)
                    
                    if (suggestions.length === 0) return
                    
                    if (e.key === 'ArrowDown') {
                      e.preventDefault()
                      setShowSuggestions(true)
                      setHighlightedIndex(prev => 
                        prev < suggestions.length - 1 ? prev + 1 : prev
                      )
                    } else if (e.key === 'ArrowUp') {
                      e.preventDefault()
                      setShowSuggestions(true)
                      setHighlightedIndex(prev => prev > 0 ? prev - 1 : -1)
                    } else if (e.key === 'Enter') {
                      e.preventDefault()
                      if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
                        const selectedName = suggestions[highlightedIndex]
                        setSelectedAgent(selectedName)
                        setSearchQuery('')
                        setShowSuggestions(false)
                        setHighlightedIndex(-1)
                      }
                    } else if (e.key === 'Escape') {
                      setShowSuggestions(false)
                      setHighlightedIndex(-1)
                    }
                  }}
                />
                {showSuggestions && searchQuery.length > 0 && (() => {
                  // Get unique names from agentsList and allCallRecordings
                  const allNames = new Set()
                  agentsList.forEach(name => {
                    if (name && typeof name === 'string') {
                      allNames.add(name)
                    }
                  })
                  allCallRecordings.forEach(rec => {
                    if (rec.executive_name) allNames.add(rec.executive_name)
                    if (rec.sales_rep) allNames.add(rec.sales_rep)
                  })
                  
                  // Filter names that start with search query (case-insensitive)
                  const suggestions = Array.from(allNames)
                    .filter(name => name.toLowerCase().startsWith(searchQuery.toLowerCase()))
                    .sort()
                    .slice(0, 10) // Limit to 10 suggestions
                  
                  if (suggestions.length === 0) return null
                  
                  return (
                    <div className="search-suggestions">
                      {suggestions.map((name, idx) => (
                        <div
                          key={idx}
                          onClick={() => {
                            setSelectedAgent(name)
                            setSearchQuery('')
                            setShowSuggestions(false)
                            setHighlightedIndex(-1)
                          }}
                          className={`suggestion-item ${highlightedIndex === idx ? 'highlighted' : ''}`}
                          onMouseEnter={() => setHighlightedIndex(idx)}
                        >
                          {name}
                        </div>
                      ))}
                    </div>
                  )
                })()}
              </div>
              <select
                className="filter-select"
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
              >
                <option value="All">All Agents</option>
                {agentsList.length > 0 ? (
                  agentsList.map((agent, idx) => (
                    <option key={idx} value={agent}>{agent}</option>
                  ))
                ) : (
                  <>
                <option value="Lakshmi">Lakshmi</option>
                <option value="John">John</option>
                    <option value="Priya">Priya</option>
                    <option value="Arun">Arun</option>
                    <option value="Sundar">Sundar</option>
                  </>
                )}
              </select>
              {teamsList.length > 0 && (
                <select
                  className="filter-select"
                  value={selectedTeam}
                  onChange={(e) => setSelectedTeam(e.target.value)}
                >
                  <option value="">All Teams</option>
                  {teamsList.map((team, idx) => (
                    <option key={idx} value={team}>{team}</option>
                  ))}
                </select>
              )}
            </div>

            <div className="executive-scoreboard-card">
              <div className="card-title">Call History</div>
              <div className="executive-records-table scrollable-section">
                <div className="executive-records-header">
                  <div className="executive-records-col">Call Record</div>
                  <div className="executive-records-col">Date</div>
                  <div className="executive-records-col">Duration</div>
                </div>
                {allCallRecordings
                  .filter(r => {
                    // Apply agent filter
                    const matchesAgent = !selectedAgent || selectedAgent === 'All' || 
                      (r.executive_name && r.executive_name.toLowerCase().includes(selectedAgent.toLowerCase())) ||
                      (r.sales_rep && r.sales_rep.toLowerCase().includes(selectedAgent.toLowerCase()))
                    // Apply team filter
                    const matchesTeam = !selectedTeam || 
                      (r.team && r.team.toLowerCase().includes(selectedTeam.toLowerCase()))
                    // Apply search filter if provided (only by name, must start with query)
                    const matchesSearch = !searchQuery || 
                      (r.executive_name && r.executive_name.toLowerCase().startsWith(searchQuery.toLowerCase())) || 
                      (r.sales_rep && r.sales_rep.toLowerCase().startsWith(searchQuery.toLowerCase()))
                    return matchesAgent && matchesTeam && matchesSearch
                  })
                  .map((recording, idx) => (
                    <div 
                      key={idx} 
                      className="executive-records-row clickable-row"
                      onClick={() => fetchCallDetails(recording.deal_id || recording.call_record, recording)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="executive-records-col">{recording.call_record}</div>
                      <div className="executive-records-col">{recording.date}</div>
                      <div className="executive-records-col">
                        <span className="duration-badge">{recording.duration}</span>
                      </div>
                    </div>
                  ))}
                {allCallRecordings.length === 0 && (
                  <div className="executive-records-row empty">
                    <div className="executive-records-col">No call records available</div>
                  </div>
                )}
              </div>
            </div>

            <div className="charts-section">
              <div className="chart-card scrollable-section">
                <div className="chart-title">Main Parameters Average (Points)</div>
                <div className="chart-container">
                  {pieChartData && pieChartData.length > 0 ? (
                    <div style={{ display: 'flex', gap: '20px', alignItems: 'center', flexWrap: 'wrap' }}>
                      <svg className="pie-chart-svg" viewBox="0 0 200 200" style={{ width: '250px', height: '250px' }}>
                        {(() => {
                          // Calculate total for proportion (pie chart shows proportion)
                          const total = pieChartData.reduce((sum, d) => sum + d.value, 0)
                          // Consistent color palette for charts
                          const chartColors = ['#ff6b9d', '#4ecdc4', '#95e1d3', '#f38181', '#aa96da', '#c7ceea', '#ffd3a5', '#fd9853', '#22c55e', '#f59e0b']
                          let currentAngle = -90
                          return pieChartData.map((segment, idx) => {
                            const segmentColor = segment.color || chartColors[idx % chartColors.length]
                            // Use value for proportion calculation (pie shows proportion of total points)
                            const angle = total > 0 ? (segment.value / total) * 360 : 0
                            const startAngle = currentAngle
                            const endAngle = currentAngle + angle
                            currentAngle = endAngle
                            const startRad = (startAngle * Math.PI) / 180
                            const endRad = (endAngle * Math.PI) / 180
                            const x1 = 100 + 80 * Math.cos(startRad)
                            const y1 = 100 + 80 * Math.sin(startRad)
                            const x2 = 100 + 80 * Math.cos(endRad)
                            const y2 = 100 + 80 * Math.sin(endRad)
                            const largeArc = angle > 180 ? 1 : 0
                            const midAngle = (startAngle + endAngle) / 2
                            const labelX = 100 + 50 * Math.cos((midAngle * Math.PI) / 180)
                            const labelY = 100 + 50 * Math.sin((midAngle * Math.PI) / 180)
                            return (
                              <g key={idx}>
                                <path
                                  d={`M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArc} 1 ${x2} ${y2} Z`}
                                  fill={segmentColor}
                                  stroke="#fff"
                                  strokeWidth="2"
                                />
                                <text x={labelX} y={labelY} textAnchor="middle" fontSize="12" fill="#000" fontWeight="600">
                                  {Math.round(segment.value)}
                                </text>
                              </g>
                            )
                          })
                        })()}
                      </svg>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {pieChartData.map((segment, idx) => {
                          const chartColors = ['#ff6b9d', '#4ecdc4', '#95e1d3', '#f38181', '#aa96da', '#c7ceea', '#ffd3a5', '#fd9853', '#22c55e', '#f59e0b']
                          const segmentColor = segment.color || chartColors[idx % chartColors.length]
                          return (
                            <div key={`legend-${idx}`} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div style={{ width: '16px', height: '16px', backgroundColor: segmentColor, borderRadius: '2px', border: '1px solid rgba(0,0,0,0.1)' }}></div>
                              <span style={{ fontSize: '12px', color: '#000', fontWeight: 500 }}>
                                {segment.label}: {Math.round(segment.value)} pts
                              </span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="chart-empty">No data available</div>
                  )}
                </div>
              </div>

              <div className="chart-card scrollable-section">
                <div className="chart-title">Sub Parameters Average (Points)</div>
                <div className="chart-container">
                  {barChartData && barChartData.length > 0 ? (
                    <>
                    <div className="bar-chart-wrapper">
                      <svg className="bar-chart-svg" viewBox="0 0 500 350">
                        {(() => {
                          // Calculate max score for scaling
                          const maxScore = Math.max(...barChartData.map(item => item.score || 0), 12)
                          const scaleMax = Math.ceil(maxScore / 2) * 2 // Round up to nearest even number
                          const tickValues = []
                          for (let i = 0; i <= scaleMax; i += Math.max(1, Math.floor(scaleMax / 4))) {
                            tickValues.push(i)
                          }
                          return tickValues.map((val) => {
                            const y = 280 - (val / scaleMax) * 220
                          return (
                            <g key={val}>
                              <line x1="80" y1={y} x2="450" y2={y} stroke="#CCCCCC" strokeWidth="1" />
                              <text x="75" y={y + 4} textAnchor="end" fontSize="10" fill="#666">{val}</text>
                            </g>
                          )
                          })
                        })()}
                        {(() => {
                          const maxScore = Math.max(...barChartData.map(item => item.score || 0), 12)
                          const scaleMax = Math.ceil(maxScore / 2) * 2
                          return barChartData.slice(0, 15).map((item, idx) => {
                          const barCount = Math.min(barChartData.length, 15)
                          const barWidth = 350 / barCount
                          const x = 80 + idx * barWidth + barWidth * 0.1
                          const width = barWidth * 0.8
                            const height = (item.score / scaleMax) * 220
                          const y = 280 - height
                          const labelY = y - 5
                            // Consistent color palette for parameters - must match legend
                            const chartColors = ['#ff6b9d', '#4ecdc4', '#95e1d3', '#f38181', '#aa96da', '#c7ceea', '#ffd3a5', '#fd9853', '#22c55e', '#f59e0b', '#a78bfa', '#fb7185', '#34d399', '#fbbf24', '#60a5fa']
                            // Use parameter color from legend (item.color or fallback to chartColors)
                            const paramColor = item.color || chartColors[idx % chartColors.length]
                          return (
                            <g key={idx}>
                                <rect x={x} y={y} width={width} height={height} fill={paramColor} rx="2" stroke="#fff" strokeWidth="1" />
                              <text x={x + width / 2} y={labelY < 10 ? y + 15 : labelY} textAnchor="middle" fontSize="9" fill="#000" fontWeight="600">
                                  {Math.round(item.score)}
                              </text>
                              <text x={x + width / 2} y="300" textAnchor="middle" fontSize="7" fill="#666">
                                {item.name.length > 15 ? item.name.substring(0, 12) + '...' : item.name}
                              </text>
                            </g>
                          )
                          })
                        })()}
                        <line x1="80" y1="280" x2="450" y2="280" stroke="#999" strokeWidth="2" />
                      </svg>
                    </div>
                      {/* Parameter-based legend with colors */}
                      <div className="bar-chart-legend" style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(0,0,0,0.1)' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <div style={{ fontSize: '12px', fontWeight: 600, color: '#000', marginBottom: '4px' }}>Parameters:</div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', maxHeight: '150px', overflowY: 'auto' }}>
                            {barChartData.slice(0, 15).map((item, idx) => {
                              const chartColors = ['#ff6b9d', '#4ecdc4', '#95e1d3', '#f38181', '#aa96da', '#c7ceea', '#ffd3a5', '#fd9853', '#22c55e', '#f59e0b', '#a78bfa', '#fb7185', '#34d399', '#fbbf24', '#60a5fa']
                              const paramColor = item.color || chartColors[idx % chartColors.length]
              return (
                                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: '150px' }}>
                                  <div style={{ width: '14px', height: '14px', backgroundColor: paramColor, borderRadius: '2px', border: '1px solid rgba(0,0,0,0.1)', flexShrink: 0 }}></div>
                                  <span style={{ fontSize: '11px', color: '#000' }}>{item.name}</span>
                                    </div>
                                  )
                                })}
                              </div>
                            </div>
                      </div>
                    </>
                  ) : (
                    <div className="chart-empty">No data available</div>
                  )}
                    </div>
                  </div>
                </div>
          </div>
        )
        })()}
        {/* End of Executive Board View - COMMENTED OUT */}

        {activeView === 'call-audit' && (
          <div className="call-audit-content">
            
            <input ref={audioInputRef} type="file" accept="audio/*" style={{ display: 'none' }} onChange={onAudioSelected} />
            <input ref={textInputRef} type="file" accept=".txt" style={{ display: 'none' }} onChange={onTextSelected} />

            <div className="audit-controls">
              <button className="btn ghost audit-btn" onClick={() => audioInputRef.current?.click()}>
                Choose Audio
              </button>
              <button className="btn primary audit-btn" onClick={transcribeAudio} disabled={!canTranscribe}>
                {isTranscribing ? 'Transcribing…' : 'Transcribe Audio'}
              </button>
              <button className="btn ghost audit-btn" onClick={() => textInputRef.current?.click()}>
                Choose .txt
              </button>
              <button className="btn primary audit-btn" onClick={scoreTranscript} disabled={!canScore}>
                {isReviewing ? 'Scoring…' : 'Score Transcript'}
              </button>
              <button 
                className="btn primary audit-btn" 
                onClick={generateFinalReport} 
                disabled={!canFinalize}
                title={!canFinalize && (!result || result.total_score === undefined) ? 'Please score the transcript first using "Score Transcript" button' : ''}
              >
                {isFinalizing ? 'Generating…' : 'Generate Report'}
              </button>
            </div>

            <div
              className={`drop-zone ${isDragActive ? 'drag-active' : ''} ${audioFile || textFile ? 'file-selected' : ''}`}
              onClick={() => audioInputRef.current?.click()}
              onDragEnter={handleDragOver}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleFileDrop}
            >
              {audioFile || textFile ? (
                <>
                  <div className="file-selected-icon">✓</div>
                  <div className="drop-icon">File Selected</div>
                  <div className="drop-text file-name">{audioFile?.name || textFile?.name}</div>
                  <div className="file-size">
                    {audioFile ? `${(audioFile.size / (1024 * 1024)).toFixed(2)} MB` : ''}
                    {textFile ? `${(textFile.size / 1024).toFixed(2)} KB` : ''}
                  </div>
                  <div className="file-change-hint">Click to change file</div>
                </>
              ) : (
                <>
                  <div className="drop-icon">Upload</div>
                  <div className="drop-text">Drag & drop audio or .txt files here</div>
                </>
              )}
            </div>

            {isBusy && (
              <div className="loading-overlay">
                <div className="loading-card">
                  <div className="spinner" />
                  <div>{isTranscribing ? 'Transcribing audio…' : isReviewing ? 'Scoring transcript…' : 'Generating report…'}</div>
                  {stage === 'uploading' && <div className="loading-sub">Uploading… {uploadPct}%</div>}
                  {stage === 'processing' && <div className="loading-sub">Processing on server…</div>}
                </div>
              </div>
            )}

            {/* Deal Info Section - Temporarily hidden */}
            {/* <section className="tile tile-meta-form" style={{ marginBottom: '20px', background: '#f8f9fa', border: '2px solid #e9ecef', borderRadius: '12px', padding: '20px' }}>
              <div className="tile-label" style={{ marginBottom: '16px', fontSize: '18px', fontWeight: 'bold' }}>Deal Information <span style={{ color: '#ef4444' }}>*</span></div>
              <div className="form-grid">
                <label>
                  <span>Deal ID <span style={{ color: '#ef4444' }}>*</span></span>
                  <input 
                    value={dealId} 
                    onChange={(e) => setDealId(e.target.value)} 
                    placeholder="e.g. DEAL-123" 
                    required
                    style={{ borderColor: !dealId ? '#ef4444' : '#d1d5db' }}
                  />
                </label>
                <label>
                  <span>Client <span style={{ color: '#ef4444' }}>*</span></span>
                  <input 
                    value={clientName} 
                    onChange={(e) => setClientName(e.target.value)} 
                    placeholder="Client name" 
                    required
                    style={{ borderColor: !clientName ? '#ef4444' : '#d1d5db' }}
                  />
                </label>
                <label>
                  <span>Sales Rep <span style={{ color: '#ef4444' }}>*</span></span>
                  <input 
                    value={salesRep} 
                    onChange={(e) => setSalesRep(e.target.value)} 
                    placeholder="Rep name" 
                    required
                    style={{ borderColor: !salesRep ? '#ef4444' : '#d1d5db' }}
                  />
                </label>
                <label>
                  <span>Call Date</span>
                  <input type="date" value={callDate} onChange={(e) => setCallDate(e.target.value)} />
                </label>
              </div>
              {(!dealId || !clientName || !salesRep) && (
                <div style={{ marginTop: '12px', padding: '10px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', color: '#991b1b', fontSize: '14px' }}>
                  ⚠️ Please fill in all required fields (marked with *) before scoring. This information is required for dashboard reporting.
                </div>
              )}
            </section> */}

            <div className="audit-grid">
              <section className="tile tile-main">
                <div className="tile-label">Overall Score</div>
                <button
                  type="button"
                  className="score-big score-button"
                  onClick={() => {
                    setActiveTab('scores') // Reset to scores tab when opening
                    setIsRubricOpen(true)
                  }}
                  disabled={!result || !criteria.length}
                  style={{ color: scoreColor }}
                >
                  {result ? `${result.total_score}/${result.total_points}` : '--/--'}
                </button>
                <div className="progress">
                  <div 
                    className={`progress-bar ${result?.passed ? 'ok' : 'bad'}`} 
                    style={{ width: `${percent}%`, backgroundColor: scoreColor }} 
                  />
                </div>
                <div className="tile-sub">
                  <span style={{ color: scoreColor, fontWeight: 600 }}>
                    {result ? `${percent}% | ${result.passed ? 'Pass' : 'Fail'}` : '--'}
                  </span>
                  {criteria.length ? ' | Click for details' : ''}
                </div>
                {result && result.fatal_error_reason && result.total_score === 0 && (
                  <div style={{
                    marginTop: '16px',
                    padding: '12px',
                    background: '#fef2f2',
                    border: '2px solid #ef4444',
                    borderRadius: '8px',
                    color: '#991b1b',
                    fontSize: '13px',
                    lineHeight: '1.5',
                    fontWeight: 600
                  }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                      <span style={{ fontSize: '16px', lineHeight: '1' }}>⚠️</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ marginBottom: '4px', fontWeight: 700 }}>FATAL ERROR - Score Set to 0</div>
                        <div style={{ fontWeight: 500 }}>{result.fatal_error_reason}</div>
                      </div>
                    </div>
                  </div>
                )}
              </section>

              <section className="tile tile-transcript">
                <div className="tile-head">
                  <div>
                    <div className="tile-label">Transcript</div>
                    <div className="tile-sub">
                      {transcript ? (
                        transcriptionMetadata ? (
                          `Generated from audio • ${transcriptionMetadata.speaker_count} speakers • ${formatTime(transcriptionMetadata.duration)} • ${transcriptionMetadata.language_code?.toUpperCase() || 'Unknown'}`
                        ) : (
                          'Generated from audio or uploaded .txt'
                        )
                      ) : (
                        'No transcript yet'
                      )}
                    </div>
                  </div>
                </div>
                <div className={`transcript-box ${isBusy ? 'skeleton' : ''}`} style={{ 
                  whiteSpace: 'pre-wrap', 
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  lineHeight: '1.6',
                  maxHeight: '280px', // fixed height with internal scroll to avoid full-page scrolling
                  overflowY: 'auto',
                  wordWrap: 'break-word',
                  overflowWrap: 'break-word'
                }}>
                  {transcript || '—'}
                </div>
              </section>

              {finalReport && (
                <>
                  <section className="tile tile-summary">
                    <div className="tile-label">Overall Summary</div>
                    <div className="summary-content">
                      <div className="review-text">{renderWithBold(finalReport.overall_summary)}</div>
                    </div>
                  </section>

                  <section className="tile tile-summary">
                    <div className="tile-label">Agent Summary</div>
                    <div className="summary-content">
                      {finalReport.agent_summary && Array.isArray(finalReport.agent_summary.well_performed) ? (
                        <>
                          <div className="review-text">
                            <strong>Well Performed:</strong>
                            <ul>
                              {finalReport.agent_summary.well_performed.map((item, idx) => (
                                <li key={`wp-${idx}`}>{renderWithBold(item)}</li>
                              ))}
                            </ul>
                          </div>
                          <div className="review-text" style={{ marginTop: '12px' }}>
                            <strong>Areas of Improvement:</strong>
                            <ul>
                              {(finalReport.agent_summary.areas_of_improvement || []).map((item, idx) => (
                                <li key={`ai-${idx}`}>{renderWithBold(item)}</li>
                              ))}
                            </ul>
                          </div>
                        </>
                      ) : (
                        <div className="review-text">
                          {renderWithBold(finalReport.agent_summary || 'No agent summary available.')}
                        </div>
                      )}
                    </div>
                  </section>

                  <section className="tile tile-summary">
                    <div className="tile-label">Client Summary</div>
                    <div className="summary-content">
                      <div className="review-text">{renderWithBold(finalReport.client_summary)}</div>
                    </div>
                  </section>
                </>
              )}
            </div>

            {isRubricOpen && result && (() => {
              // Categorize criteria based on Empire rubric structure
              const categorizedCriteria = {
                'Greetings': [],
                'Project Knowledge': [],
                'Process Knowledge': [],
                'Soft Skills': [],
                'Closing': []
              }
              
              // Exact mapping based on rubric criteria names
              const categoryMap = {
                'Greetings': ['Greeting & Introduced Self', 'Brand Intro', 'Purpose of Call', 'Reaching Decision Maker/RPC'],
                'Project Knowledge': ['Effective Probing', 'Project Knowledge', 'Objection Handling', 'Follow Up'],
                'Process Knowledge': ['Call Control', 'Disposition'],
                'Soft Skills': ['Enthusiasm', 'Active Listening', 'Confidence', 'Professional', 'Language and Grammar', 'Clarity of Speech', 'Tone and Voice Modulation'],
                'Closing': ['Thanking Customer', 'Closing Script']
              }
              
              criteria.forEach(c => {
                const name = c.name || ''
                for (const [category, names] of Object.entries(categoryMap)) {
                  if (names.some(n => name.includes(n) || n.includes(name))) {
                    categorizedCriteria[category].push(c)
                    break
                  }
                }
              })

              // Determine color for each criterion based on percentage of max score
              // 0-50%: red, 50-75%: yellow, 75-100%: green
              const getScoreColor = (criterion) => {
                if (!criterion || typeof criterion.points_awarded !== 'number' || typeof criterion.max_points !== 'number') return '#ef4444'
                if (criterion.max_points === 0) return '#ef4444'
                const percentage = (criterion.points_awarded / criterion.max_points) * 100
                if (percentage >= 75) return '#22c55e' // green for 75-100%
                if (percentage >= 50) return '#fbbf24' // yellow for 50-75%
                return '#ef4444' // red for 0-50%
              }

              const fileName = audioFile?.name || textFile?.name || `${dealId || 'Unknown'} ${salesRep || 'Unknown'}`
              // Use transcriptionMetadata duration if available (most accurate), otherwise use finalReport or default
              const duration = formatDuration(finalReport?.call_duration, transcriptionMetadata?.duration)
              const callDateDisplay = callDate ? new Date(callDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric' }) : (finalReport?.call_date || 'Unknown')

              return (
                <div className="modal-backdrop" onClick={() => setIsRubricOpen(false)}>
                  <div className="modal-card rubric-modal-new" onClick={(e) => e.stopPropagation()}>
                    <div className="modal-head">
                      <div className="modal-title">Call Review Report</div>
                      <button className="modal-close" onClick={() => setIsRubricOpen(false)}>x</button>
                    </div>
                    
                    {/* Tab Navigation */}
                    <div className="modal-tabs" style={{ display: 'flex', gap: '8px', padding: '0 24px', borderBottom: '1px solid #e5e7eb', marginBottom: '16px' }}>
                      <button
                        className={`modal-tab ${activeTab === 'scores' ? 'active' : ''}`}
                        onClick={() => setActiveTab('scores')}
                        style={{
                          padding: '12px 24px',
                          border: 'none',
                          background: 'transparent',
                          cursor: 'pointer',
                          borderBottom: activeTab === 'scores' ? '2px solid #ff6b9d' : '2px solid transparent',
                          color: activeTab === 'scores' ? '#ff6b9d' : '#666',
                          fontWeight: activeTab === 'scores' ? 600 : 400,
                          fontSize: '14px'
                        }}
                      >
                        Scores
                      </button>
                      <button
                        className={`modal-tab ${activeTab === 'summaries' ? 'active' : ''}`}
                        onClick={() => setActiveTab('summaries')}
                        disabled={!finalReport}
                        style={{
                          padding: '12px 24px',
                          border: 'none',
                          background: 'transparent',
                          cursor: finalReport ? 'pointer' : 'not-allowed',
                          borderBottom: activeTab === 'summaries' ? '2px solid #ff6b9d' : '2px solid transparent',
                          color: finalReport ? (activeTab === 'summaries' ? '#ff6b9d' : '#666') : '#ccc',
                          fontWeight: activeTab === 'summaries' ? 600 : 400,
                          fontSize: '14px',
                          opacity: finalReport ? 1 : 0.5
                        }}
                      >
                        Summaries
                      </button>
                    </div>
                    
                    <div className="rubric-modal-content">
                      {/* Left Panel */}
                      <div className="rubric-left-panel">
                        <div className="executive-info">
                          <div className="executive-name">{salesRep || 'Executive 1'}</div>
                          <div className="executive-team">Team 1</div>
                        </div>
                        
                        <div className="call-details-box">
                          <div className="call-details-header">Call Details</div>
                          <div className="call-detail-item">
                            <span className="call-detail-label">File Name:</span>
                            <span className="call-detail-value">{fileName}</span>
                          </div>
                          <div className="call-detail-item">
                            <span className="call-detail-label">Duration:</span>
                            <span className="call-detail-value">{duration}</span>
                          </div>
                          <div className="call-detail-item">
                            <span className="call-detail-label">Date:</span>
                            <span className="call-detail-value">{callDateDisplay}</span>
                          </div>
                        </div>

                        <div className="total-score-box">
                          <div className="total-score-label">TOTAL SCORE</div>
                          <div 
                            className="total-score-value" 
                            style={{ 
                              color: result.total_points > 0 ? (() => {
                                const percentage = (result.total_score / result.total_points) * 100
                                if (percentage >= 75) return '#22c55e' // green for 75-100%
                                if (percentage >= 50) return '#fbbf24' // yellow for 50-75%
                                return '#ef4444' // red for 0-50%
                              })() : '#ef4444'
                            }}
                          >
                            {result.total_score} / {result.total_points}
                          </div>
                          {result.fatal_error_reason && result.total_score === 0 && (
                            <div style={{
                              marginTop: '12px',
                              padding: '10px',
                              background: '#fef2f2',
                              border: '2px solid #ef4444',
                              borderRadius: '6px',
                              color: '#991b1b',
                              fontSize: '11px',
                              lineHeight: '1.4',
                              fontWeight: 600
                            }}>
                              <div style={{ marginBottom: '4px', fontWeight: 700 }}>⚠️ FATAL ERROR</div>
                              <div style={{ fontWeight: 500 }}>{result.fatal_error_reason}</div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Right Panel */}
                      <div className="rubric-right-panel">
                        {activeTab === 'scores' ? (
                          Object.entries(categorizedCriteria).map(([category, categoryCriteria]) => (
                            categoryCriteria.length > 0 && (
                              <div 
                                key={category} 
                                className="rubric-category-group"
                              >
                                <div className="rubric-category-header">
                                  {category}
                                </div>
                                <div className="rubric-criteria-container">
                                  {categoryCriteria.map((c) => {
                                    const scoreColorValue = getScoreColor(c)
                                    const isExpanded = auditExpandedIds[c.id]
                                    return (
                                      <div 
                                        key={c.id} 
                                        className={`rubric-criterion-item ${isExpanded ? 'expanded' : ''}`}
                                      >
                                        <div className="rubric-criterion-main">
                                          <button
                                            type="button"
                                            className="criterion-toggle-btn"
                                            onClick={() => setAuditExpandedIds(prev => {
                                              const newState = { ...prev }
                                              if (newState[c.id]) {
                                                delete newState[c.id]
                                              } else {
                                                newState[c.id] = true
                                              }
                                              return newState
                                            })}
                                          >
                                            <span className={`arrow-icon ${isExpanded ? 'expanded' : ''}`}>
                                              {isExpanded ? '▾' : '▸'}
                                            </span>
                                            <span className="rubric-criterion-name">{c.name}</span>
                                          </button>
                                          <span 
                                            className="rubric-criterion-score"
                                            style={{ color: scoreColorValue, fontWeight: 700 }}
                                          >
                                            {c.points_awarded} / {c.max_points}
                                          </span>
                                        </div>
                                        {isExpanded && c.rationale && (
                                          <div className="rubric-criterion-rationale">
                                            {renderWithBold(c.rationale)}
                                          </div>
                                        )}
                                      </div>
                                    )
                                  })}
                                </div>
                              </div>
                            )
                          ))
                        ) : (
                          finalReport ? (
                            <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                              {finalReport.overall_summary && (
                                <div>
                                  <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: '#333' }}>Overall Summary</h3>
                                  <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#555', whiteSpace: 'pre-wrap' }}>
                                    {finalReport.overall_summary}
                                  </div>
                                </div>
                              )}
                              {finalReport.client_summary && (
                                <div>
                                  <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: '#333' }}>Client Summary</h3>
                                  <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#555', whiteSpace: 'pre-wrap' }}>
                                    {finalReport.client_summary}
                                  </div>
                                </div>
                              )}
                              {finalReport.agent_summary && (
                                <div>
                                  <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: '#333' }}>Agent Summary</h3>
                                  {Array.isArray(finalReport.agent_summary.well_performed) ? (
                                    <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#555' }}>
                                      <div style={{ marginBottom: '8px' }}>
                                        <strong>Well Performed:</strong>
                                        <ul>
                                          {finalReport.agent_summary.well_performed.map((item, idx) => (
                                            <li key={`wp-${idx}`}>{renderWithBold(item)}</li>
                                          ))}
                                        </ul>
                                      </div>
                                      <div>
                                        <strong>Areas of Improvement:</strong>
                                        <ul>
                                          {(finalReport.agent_summary.areas_of_improvement || []).map((item, idx) => (
                                            <li key={`ai-${idx}`}>{renderWithBold(item)}</li>
                                          ))}
                                        </ul>
                                      </div>
                                    </div>
                                  ) : (
                                    <div style={{ fontSize: '14px', lineHeight: '1.6', color: '#555', whiteSpace: 'pre-wrap' }}>
                                      {renderWithBold(finalReport.agent_summary)}
                                    </div>
                                  )}
                                </div>
                              )}
                              {!finalReport.overall_summary && !finalReport.client_summary && !finalReport.agent_summary && (
                                <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
                                  No summaries available. Please generate a report first.
                                </div>
                              )}
                            </div>
                          ) : (
                            <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
                              No summaries available. Please generate a report first.
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })()}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
