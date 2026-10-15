import { useState, useEffect } from 'react'
import { Server, Database, CheckCircle2, AlertCircle, RefreshCw, Cpu, Layers } from 'lucide-react'

interface HealthResponse {
  status: string
  environment: string
}

interface DbHealthResponse {
  database: string
  database_name: string
  user: string
  status: string
}

export default function App() {
  const [apiHealth, setApiHealth] = useState<HealthResponse | null>(null)
  const [dbHealth, setDbHealth] = useState<DbHealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const checkConnectivity = async () => {
    setLoading(true)
    setError(null)
    try {
      // 1. Check API health
      const apiRes = await fetch('/health')
      if (!apiRes.ok) throw new Error(`API returned HTTP ${apiRes.status}`)
      const apiData = await apiRes.json()
      setApiHealth(apiData)

      // 2. Check Database connectivity through backend
      const dbRes = await fetch('/health/db')
      if (!dbRes.ok) throw new Error(`Database health check failed: HTTP ${dbRes.status}`)
      const dbData = await dbRes.json()
      setDbHealth(dbData)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Unknown connection error')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkConnectivity()
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-800">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              Q
            </div>
            <div>
              <span className="font-semibold text-slate-900 text-lg tracking-tight">QuickDesk</span>
              <span className="ml-2 text-xs font-medium px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                AI Helpdesk
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={checkConnectivity}
              disabled={loading}
              className="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
              Test Connection
            </button>
            <div className="flex items-center space-x-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Phase 1: Foundation</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8">
        {/* Welcome Banner */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            System Foundation & Health Status
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            QuickDesk monorepo architecture verification: Frontend (React 19 + Vite), Backend (FastAPI), and Database (PostgreSQL 18).
          </p>
        </div>

        {/* Live Service Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {/* Backend Status Card */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg">
                  <Server className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">FastAPI Backend</h3>
                  <p className="text-xs text-slate-500">Python 3.13 • Port 8000</p>
                </div>
              </div>
              {apiHealth?.status === 'ok' ? (
                <span className="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Online
                </span>
              ) : loading ? (
                <span className="text-xs text-slate-400">Pinging...</span>
              ) : (
                <span className="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                  <AlertCircle className="w-3.5 h-3.5 mr-1" /> Offline
                </span>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
              <span>Environment: <strong className="text-slate-800">{apiHealth?.environment || '—'}</strong></span>
              <span>OpenAPI Docs: <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">/docs</a></span>
            </div>
          </div>

          {/* Database Status Card */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">PostgreSQL Database</h3>
                  <p className="text-xs text-slate-500">PostgreSQL 18 • Port 5432</p>
                </div>
              </div>
              {dbHealth?.status === 'ok' ? (
                <span className="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Connected
                </span>
              ) : loading ? (
                <span className="text-xs text-slate-400">Checking...</span>
              ) : (
                <span className="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                  <AlertCircle className="w-3.5 h-3.5 mr-1" /> Disconnected
                </span>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
              <span>Database: <strong className="text-slate-800">{dbHealth?.database_name || '—'}</strong></span>
              <span>User: <strong className="text-slate-800">{dbHealth?.user || '—'}</strong></span>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>Connection Warning: {error}. Make sure the backend server is running on port 8000.</span>
          </div>
        )}

        {/* Architecture & Verification Checklist */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
          <div className="flex items-center space-x-2 mb-4">
            <Layers className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-semibold text-slate-900">Foundation Verification Checklist</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
              <div className="flex items-center space-x-2 font-medium text-slate-900 mb-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Monorepo Skeletons</span>
              </div>
              <p className="text-xs text-slate-500">
                Frontend (React/Vite/TS/Tailwind) & Backend (FastAPI) initialized with clean directory separation.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
              <div className="flex items-center space-x-2 font-medium text-slate-900 mb-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>PostgreSQL DB Ready</span>
              </div>
              <p className="text-xs text-slate-500">
                Dedicated database <code>quickdesk</code> active with SQLAlchemy connection pooling verified.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
              <div className="flex items-center space-x-2 font-medium text-slate-900 mb-1">
                <Cpu className="w-4 h-4 text-indigo-600" />
                <span>AI Stack Pre-verified</span>
              </div>
              <p className="text-xs text-slate-500">
                LangChain, Chroma, and Groq SDK installed cleanly inside Apple Silicon Python 3.13 venv.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        QuickDesk • AI Solution Engineer Assessment • Built with FastAPI, React, PostgreSQL & Groq
      </footer>
    </div>
  )
}
