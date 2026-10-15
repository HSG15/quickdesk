import React, { useState, useEffect } from 'react'
import {
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  LogOut,
  Send,
  Search,
  FileText,
  Clock,
  Sparkles,
  History,
  Check,
  ChevronRight,
  PlusCircle,
} from 'lucide-react'
import { api, clearStoredToken, getStoredToken } from './api/client'
import type { User, Ticket, AuditLog, TicketCategory, TicketPriority } from './types'

export default function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [authLoading, setAuthLoading] = useState(true)

  // Login form state
  const [email, setEmail] = useState('agent@quickdesk.com')
  const [password, setPassword] = useState('agent123')
  const [loginError, setLoginError] = useState<string | null>(null)
  const [submittingLogin, setSubmittingLogin] = useState(false)

  // Employee Portal State
  const [employeeTickets, setEmployeeTickets] = useState<Ticket[]>([])
  const [newTitle, setNewTitle] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [newAttachment, setNewAttachment] = useState('')
  const [ticketSubmitLoading, setTicketSubmitLoading] = useState(false)
  const [ticketSubmitSuccess, setTicketSubmitSuccess] = useState(false)
  const [employeeError, setEmployeeError] = useState<string | null>(null)
  const [selectedEmployeeTicket, setSelectedEmployeeTicket] = useState<Ticket | null>(null)

  // Agent Dashboard State
  const [agentTickets, setAgentTickets] = useState<Ticket[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [priorityFilter, setPriorityFilter] = useState<string>('')
  const [agentLoading, setAgentLoading] = useState(false)
  const [agentError, setAgentError] = useState<string | null>(null)

  // Agent Selected Ticket & Override/Reply State
  const [activeTicket, setActiveTicket] = useState<Ticket | null>(null)
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [overrideCategory, setOverrideCategory] = useState<TicketCategory>('IT')
  const [overridePriority, setOverridePriority] = useState<TicketPriority>('Medium')
  const [overrideLoading, setOverrideLoading] = useState(false)
  const [replyText, setReplyText] = useState('')
  const [replyLoading, setReplyLoading] = useState(false)
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null)

  // Load authenticated user on mount
  useEffect(() => {
    const token = getStoredToken()
    if (token) {
      api.getMe()
        .then((user) => setCurrentUser(user))
        .catch(() => clearStoredToken())
        .finally(() => setAuthLoading(false))
    } else {
      setAuthLoading(false)
    }
  }, [])

  // Fetch data whenever user role or filters change
  useEffect(() => {
    if (!currentUser) return

    if (currentUser.role === 'employee') {
      loadEmployeeTickets()
    } else if (currentUser.role === 'agent') {
      loadAgentTickets()
    }
  }, [currentUser, searchQuery, statusFilter, categoryFilter, priorityFilter])

  const loadEmployeeTickets = async () => {
    try {
      const tickets = await api.getMyTickets()
      setEmployeeTickets(tickets)
    } catch (err: unknown) {
      if (err instanceof Error) setEmployeeError(err.message)
    }
  }

  const loadAgentTickets = async () => {
    setAgentLoading(true)
    setAgentError(null)
    try {
      const tickets = await api.getAllTickets({
        search: searchQuery || undefined,
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
        priority: priorityFilter || undefined,
      })
      setAgentTickets(tickets)
    } catch (err: unknown) {
      if (err instanceof Error) setAgentError(err.message)
    } finally {
      setAgentLoading(false)
    }
  }

  const handleLogin = async (e?: React.FormEvent, customEmail?: string, customPass?: string) => {
    if (e) e.preventDefault()
    setSubmittingLogin(true)
    setLoginError(null)

    const loginEmail = customEmail || email
    const loginPass = customPass || password

    try {
      const data = await api.login(loginEmail, loginPass)
      setCurrentUser(data.user)
      setActiveTicket(null)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setLoginError(err.message)
      } else {
        setLoginError('Authentication failed')
      }
    } finally {
      setSubmittingLogin(false)
    }
  }

  const handleLogout = () => {
    clearStoredToken()
    setCurrentUser(null)
    setActiveTicket(null)
    setSelectedEmployeeTicket(null)
  }

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim() || !newDescription.trim()) return

    setTicketSubmitLoading(true)
    setEmployeeError(null)
    try {
      const created = await api.createTicket({
        title: newTitle,
        description: newDescription,
        attachment_filename: newAttachment.trim() || undefined,
      })
      setEmployeeTickets([created, ...employeeTickets])
      setNewTitle('')
      setNewDescription('')
      setNewAttachment('')
      setTicketSubmitSuccess(true)
      setTimeout(() => setTicketSubmitSuccess(false), 4000)
    } catch (err: unknown) {
      if (err instanceof Error) setEmployeeError(err.message)
    } finally {
      setTicketSubmitLoading(false)
    }
  }

  const selectAgentTicket = async (ticket: Ticket) => {
    setActiveTicket(ticket)
    setOverrideCategory(ticket.category)
    setOverridePriority(ticket.priority)
    setReplyText(ticket.final_reply || ticket.ai_draft_reply || '')
    setActionSuccessMessage(null)

    // Fetch audit history
    try {
      const logs = await api.getAuditLogs(ticket.id)
      setAuditLogs(logs)
    } catch {
      setAuditLogs([])
    }
  }

  const handleApplyOverride = async () => {
    if (!activeTicket) return
    setOverrideLoading(true)
    setActionSuccessMessage(null)
    try {
      const updated = await api.overrideClassification(activeTicket.id, {
        category: overrideCategory,
        priority: overridePriority,
      })
      setActiveTicket(updated)
      // Update in agent tickets list
      setAgentTickets(agentTickets.map((t) => (t.id === updated.id ? updated : t)))
      // Refresh audit logs
      const logs = await api.getAuditLogs(updated.id)
      setAuditLogs(logs)
      setActionSuccessMessage('Classification updated and audit log recorded!')
      setTimeout(() => setActionSuccessMessage(null), 3000)
    } catch (err: unknown) {
      if (err instanceof Error) alert(err.message)
    } finally {
      setOverrideLoading(false)
    }
  }

  const handleSendReply = async () => {
    if (!activeTicket || !replyText.trim()) return
    setReplyLoading(true)
    setActionSuccessMessage(null)
    try {
      const updated = await api.replyAndResolve(activeTicket.id, replyText)
      setActiveTicket(updated)
      setAgentTickets(agentTickets.map((t) => (t.id === updated.id ? updated : t)))
      setActionSuccessMessage('Reply sent! Ticket marked as Resolved.')
    } catch (err: unknown) {
      if (err instanceof Error) alert(err.message)
    } finally {
      setReplyLoading(false)
    }
  }

  // Priority badge styling
  const getPriorityBadge = (p: TicketPriority) => {
    switch (p) {
      case 'High':
        return 'bg-rose-50 text-rose-700 border-rose-200'
      case 'Medium':
        return 'bg-amber-50 text-amber-700 border-amber-200'
      case 'Low':
        return 'bg-slate-100 text-slate-700 border-slate-200'
    }
  }

  // Category badge styling
  const getCategoryBadge = (c: TicketCategory) => {
    switch (c) {
      case 'IT':
        return 'bg-blue-50 text-blue-700 border-blue-200'
      case 'HR':
        return 'bg-purple-50 text-purple-700 border-purple-200'
      case 'Finance':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200'
      case 'Admin':
        return 'bg-cyan-50 text-cyan-700 border-cyan-200'
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200'
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-800">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              Q
            </div>
            <div>
              <span className="font-semibold text-slate-900 text-lg tracking-tight">QuickDesk</span>
              <span className="ml-2 text-xs font-medium px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                Phase 3: Ticket Workflow
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {currentUser ? (
              <div className="flex items-center space-x-3">
                {/* 1-Click Role Switcher for Interview / Assessment Demo */}
                <div className="hidden sm:flex items-center bg-slate-100 p-1 rounded-lg text-xs font-medium border border-slate-200">
                  <span className="px-2 text-slate-500">Quick Switch:</span>
                  <button
                    onClick={() => handleLogin(undefined, 'agent@quickdesk.com', 'agent123')}
                    className={`px-2.5 py-1 rounded transition-colors ${
                      currentUser.role === 'agent'
                        ? 'bg-white text-indigo-700 shadow-xs font-semibold'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Agent (Alice)
                  </button>
                  <button
                    onClick={() => handleLogin(undefined, 'employee@quickdesk.com', 'employee123')}
                    className={`px-2.5 py-1 rounded transition-colors ${
                      currentUser.role === 'employee'
                        ? 'bg-white text-indigo-700 shadow-xs font-semibold'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Employee (Bob)
                  </button>
                </div>

                <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
                  <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-medium text-xs">
                    {currentUser.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="text-left hidden md:block">
                    <p className="text-xs font-semibold text-slate-900 leading-tight">{currentUser.name}</p>
                    <p className="text-[11px] text-slate-500 capitalize">{currentUser.role}</p>
                  </div>
                </div>

                <button
                  onClick={handleLogout}
                  title="Logout"
                  className="p-1.5 text-slate-500 hover:text-slate-800 rounded-md hover:bg-slate-100 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-slate-500">Demo Accounts:</span>
                <button
                  onClick={() => handleLogin(undefined, 'agent@quickdesk.com', 'agent123')}
                  className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-medium rounded border border-indigo-200 transition-colors"
                >
                  Agent Login
                </button>
                <button
                  onClick={() => handleLogin(undefined, 'employee@quickdesk.com', 'employee123')}
                  className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded border border-slate-200 transition-colors"
                >
                  Employee Login
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {!currentUser ? (
          /* Authentication Screen */
          <div className="max-w-md mx-auto my-12 bg-white p-8 rounded-xl border border-slate-200 shadow-xs">
            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-indigo-600 text-white rounded-xl flex items-center justify-center font-bold text-2xl mx-auto shadow-sm">
                Q
              </div>
              <h2 className="text-xl font-bold text-slate-900 mt-3">Welcome to QuickDesk</h2>
              <p className="text-xs text-slate-500 mt-1">Sign in with an internal employee or agent account</p>
            </div>

            {loginError && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{loginError}</span>
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={submittingLogin}
                className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-lg shadow-sm transition-colors disabled:opacity-50 flex items-center justify-center"
              >
                {submittingLogin ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Sign In'}
              </button>
            </form>

            <div className="mt-6 pt-6 border-t border-slate-100">
              <p className="text-xs font-medium text-slate-600 mb-2 text-center">1-Click Fast Assessment Login:</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => handleLogin(undefined, 'agent@quickdesk.com', 'agent123')}
                  className="p-2 border border-indigo-200 rounded-lg bg-indigo-50/50 hover:bg-indigo-50 text-indigo-700 text-left transition-colors"
                >
                  <p className="font-semibold">Alice (Support Agent)</p>
                  <p className="text-[10px] text-indigo-500">agent@quickdesk.com</p>
                </button>
                <button
                  type="button"
                  onClick={() => handleLogin(undefined, 'employee@quickdesk.com', 'employee123')}
                  className="p-2 border border-slate-200 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 text-left transition-colors"
                >
                  <p className="font-semibold">Bob (Employee)</p>
                  <p className="text-[10px] text-slate-500">employee@quickdesk.com</p>
                </button>
              </div>
            </div>
          </div>
        ) : currentUser.role === 'employee' ? (
          /* ============================================================== */
          /* EMPLOYEE PORTAL VIEW                                           */
          /* ============================================================== */
          <div className="space-y-8">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Employee Helpdesk Portal</h1>
              <p className="text-xs text-slate-500 mt-1">
                Welcome back, {currentUser.name}. Submit IT or workplace requests and track your ticket status.
              </p>
            </div>

            {employeeError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{employeeError}</span>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Ticket Submission Form */}
              <div className="lg:col-span-5 bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-center space-x-2 mb-4">
                  <PlusCircle className="w-5 h-5 text-indigo-600" />
                  <h2 className="text-base font-semibold text-slate-900">Submit a New Ticket</h2>
                </div>

                {ticketSubmitSuccess && (
                  <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                    <span>Your ticket has been submitted and categorized by AI!</span>
                  </div>
                )}

                <form onSubmit={handleCreateTicket} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Issue Summary (Title) <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. VPN is not connecting from home"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Detailed Description <span className="text-rose-500">*</span>
                    </label>
                    <textarea
                      rows={4}
                      placeholder="Describe what happened, any error messages, or what you need access to..."
                      value={newDescription}
                      onChange={(e) => setNewDescription(e.target.value)}
                      className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Attachment Filename (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. vpn_error_screenshot.png"
                      value={newAttachment}
                      onChange={(e) => setNewAttachment(e.target.value)}
                      className="w-full text-sm px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <p className="text-[11px] text-slate-400 mt-1">Store reference to relevant logs or screenshots.</p>
                  </div>

                  <button
                    type="submit"
                    disabled={ticketSubmitLoading}
                    className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-lg shadow-sm transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
                  >
                    {ticketSubmitLoading ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        <span>Submit Ticket</span>
                      </>
                    )}
                  </button>
                </form>
              </div>

              {/* My Tickets List */}
              <div className="lg:col-span-7 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-5 h-5 text-indigo-600" />
                    <h2 className="text-base font-semibold text-slate-900">My Submitted Tickets</h2>
                  </div>
                  <span className="text-xs text-slate-500">
                    Total: <strong>{employeeTickets.length}</strong>
                  </span>
                </div>

                {employeeTickets.length === 0 ? (
                  <div className="bg-white p-8 rounded-xl border border-slate-200 text-center text-slate-500 text-sm">
                    <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                    <p className="font-semibold text-slate-700">No tickets submitted yet</p>
                    <p className="text-xs text-slate-400 mt-1">Use the form on the left to submit your first request.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {employeeTickets.map((t) => (
                      <div
                        key={t.id}
                        onClick={() => setSelectedEmployeeTicket(t)}
                        className="bg-white p-4 rounded-xl border border-slate-200 hover:border-indigo-300 shadow-xs cursor-pointer transition-all hover:shadow-sm"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs font-mono text-slate-400">#{t.id}</span>
                              <h3 className="text-sm font-semibold text-slate-900">{t.title}</h3>
                            </div>
                            <p className="text-xs text-slate-500 line-clamp-1 mt-1">{t.description}</p>
                          </div>
                          <span
                            className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full border ${
                              t.status === 'Resolved'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : 'bg-blue-50 text-blue-700 border-blue-200'
                            }`}
                          >
                            {t.status}
                          </span>
                        </div>

                        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-0.5 rounded border ${getCategoryBadge(t.category)}`}>
                              {t.category}
                            </span>
                            <span className={`px-2 py-0.5 rounded border ${getPriorityBadge(t.priority)}`}>
                              {t.priority}
                            </span>
                          </div>
                          <span className="text-slate-400 flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            {new Date(t.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Employee Ticket Detail Modal */}
            {selectedEmployeeTicket && (
              <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
                <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-xl w-full p-6 space-y-4">
                  <div className="flex items-start justify-between border-b border-slate-100 pb-3">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono text-slate-400">#{selectedEmployeeTicket.id}</span>
                        <span
                          className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
                            selectedEmployeeTicket.status === 'Resolved'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : 'bg-blue-50 text-blue-700 border-blue-200'
                          }`}
                        >
                          {selectedEmployeeTicket.status}
                        </span>
                      </div>
                      <h3 className="text-base font-bold text-slate-900 mt-1">{selectedEmployeeTicket.title}</h3>
                    </div>
                    <button
                      onClick={() => setSelectedEmployeeTicket(null)}
                      className="text-slate-400 hover:text-slate-700 text-sm font-semibold p-1"
                    >
                      ✕
                    </button>
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Original Request
                    </h4>
                    <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg whitespace-pre-wrap border border-slate-200/60">
                      {selectedEmployeeTicket.description}
                    </p>
                    {selectedEmployeeTicket.attachment_filename && (
                      <p className="text-[11px] text-slate-500 mt-1">
                        Attachment: <code>{selectedEmployeeTicket.attachment_filename}</code>
                      </p>
                    )}
                  </div>

                  <div>
                    <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Support Agent Resolution
                    </h4>
                    {selectedEmployeeTicket.final_reply ? (
                      <div className="bg-emerald-50/60 border border-emerald-200 p-3.5 rounded-lg text-xs text-emerald-900 whitespace-pre-wrap">
                        <p className="font-semibold text-emerald-800 mb-1 flex items-center">
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                          Final Reply from Support:
                        </p>
                        {selectedEmployeeTicket.final_reply}
                        {selectedEmployeeTicket.resolved_at && (
                          <p className="text-[10px] text-emerald-600 mt-2">
                            Resolved at: {new Date(selectedEmployeeTicket.resolved_at).toLocaleString()}
                          </p>
                        )}
                      </div>
                    ) : (
                      <div className="bg-amber-50/50 border border-amber-200 p-3 rounded-lg text-xs text-amber-800 flex items-center space-x-2">
                        <Clock className="w-4 h-4 shrink-0 text-amber-600" />
                        <span>A support technician has been assigned and is reviewing your request.</span>
                      </div>
                    )}
                  </div>

                  <div className="pt-2 text-right">
                    <button
                      onClick={() => setSelectedEmployeeTicket(null)}
                      className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs rounded-lg transition-colors"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* ============================================================== */
          /* AGENT DASHBOARD VIEW                                           */
          /* ============================================================== */
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Support Agent Dashboard</h1>
                <p className="text-xs text-slate-500 mt-1">
                  Review incoming tickets, override AI suggestions with audit tracking, and resolve with AI-assisted drafts.
                </p>
              </div>

              {/* Status summary pill */}
              <div className="flex items-center space-x-2 text-xs">
                <span className="px-3 py-1 bg-white border border-slate-200 rounded-lg shadow-2xs">
                  Open: <strong className="text-blue-600">{agentTickets.filter((t) => t.status === 'Open').length}</strong>
                </span>
                <span className="px-3 py-1 bg-white border border-slate-200 rounded-lg shadow-2xs">
                  Resolved: <strong className="text-emerald-600">{agentTickets.filter((t) => t.status === 'Resolved').length}</strong>
                </span>
              </div>
            </div>

            {/* Filter & Search Bar */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by title..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
                >
                  <option value="">All Statuses</option>
                  <option value="Open">Open</option>
                  <option value="Resolved">Resolved</option>
                </select>
              </div>

              <div>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
                >
                  <option value="">All Categories</option>
                  <option value="IT">IT</option>
                  <option value="HR">HR</option>
                  <option value="Finance">Finance</option>
                  <option value="Admin">Admin</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
                >
                  <option value="">All Priorities</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
            </div>

            {agentError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{agentError}</span>
              </div>
            )}

            {/* Split Screen Layout: Ticket Table on Left, Ticket Detail/Workflow on Right */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Ticket Table */}
              <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
                <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-slate-900">All Company Tickets</h2>
                  <span className="text-xs text-slate-500">{agentTickets.length} tickets matching filters</span>
                </div>

                {agentTickets.length === 0 ? (
                  <div className="p-12 text-center text-slate-400 text-sm">
                    {agentLoading ? (
                      <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-600 mb-2" />
                    ) : (
                      <p>No tickets match the current search filters.</p>
                    )}
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50/80 text-slate-600 border-b border-slate-100 uppercase tracking-wider font-semibold">
                        <tr>
                          <th className="py-2.5 px-3">ID</th>
                          <th className="py-2.5 px-3">Title & Submitter</th>
                          <th className="py-2.5 px-3">Category</th>
                          <th className="py-2.5 px-3">Priority</th>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {agentTickets.map((t) => {
                          const isSelected = activeTicket?.id === t.id
                          return (
                            <tr
                              key={t.id}
                              onClick={() => selectAgentTicket(t)}
                              className={`cursor-pointer transition-colors ${
                                isSelected ? 'bg-indigo-50/60' : 'hover:bg-slate-50'
                              }`}
                            >
                              <td className="py-3 px-3 font-mono text-slate-400">#{t.id}</td>
                              <td className="py-3 px-3">
                                <p className="font-medium text-slate-900 line-clamp-1">{t.title}</p>
                                <p className="text-[11px] text-slate-400">Employee #{t.employee_id}</p>
                              </td>
                              <td className="py-3 px-3">
                                <span className={`px-2 py-0.5 rounded border text-[11px] ${getCategoryBadge(t.category)}`}>
                                  {t.category}
                                </span>
                              </td>
                              <td className="py-3 px-3">
                                <span className={`px-2 py-0.5 rounded border text-[11px] ${getPriorityBadge(t.priority)}`}>
                                  {t.priority}
                                </span>
                              </td>
                              <td className="py-3 px-3">
                                <span
                                  className={`inline-flex items-center text-[11px] font-medium px-2 py-0.5 rounded-full border ${
                                    t.status === 'Resolved'
                                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                      : 'bg-blue-50 text-blue-700 border-blue-200'
                                  }`}
                                >
                                  {t.status}
                                </span>
                              </td>
                              <td className="py-3 px-3 text-right">
                                <button className="p-1 text-slate-400 hover:text-indigo-600">
                                  <ChevronRight className="w-4 h-4" />
                                </button>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Ticket Inspector & Reply Panel */}
              <div className="lg:col-span-5 space-y-4">
                {activeTicket ? (
                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-5">
                    {/* Header */}
                    <div className="border-b border-slate-100 pb-3 flex items-start justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-mono text-slate-400">Ticket #{activeTicket.id}</span>
                          <span
                            className={`text-xs font-medium px-2 py-0.5 rounded-full border ${
                              activeTicket.status === 'Resolved'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : 'bg-blue-50 text-blue-700 border-blue-200'
                            }`}
                          >
                            {activeTicket.status}
                          </span>
                        </div>
                        <h3 className="text-base font-bold text-slate-900 mt-1">{activeTicket.title}</h3>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          Submitted on {new Date(activeTicket.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>

                    {actionSuccessMessage && (
                      <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs flex items-center space-x-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>{actionSuccessMessage}</span>
                      </div>
                    )}

                    {/* Original Description */}
                    <div>
                      <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                        Employee Description
                      </h4>
                      <p className="text-xs text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-200/70 whitespace-pre-wrap">
                        {activeTicket.description}
                      </p>
                      {activeTicket.attachment_filename && (
                        <p className="text-[11px] text-slate-500 mt-1">
                          Attachment: <code>{activeTicket.attachment_filename}</code>
                        </p>
                      )}
                    </div>

                    {/* Classification & Override Controls */}
                    <div className="bg-slate-50/70 p-4 rounded-xl border border-slate-200/80 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                          Classification & Overrides
                        </h4>
                        <span className="text-[11px] text-slate-500">
                          Original AI Suggestion: <strong>{activeTicket.ai_suggested_category}</strong> (
                          {activeTicket.ai_suggested_priority})
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div>
                          <label className="block text-[11px] font-medium text-slate-600 mb-1">Active Category</label>
                          <select
                            value={overrideCategory}
                            onChange={(e) => setOverrideCategory(e.target.value as TicketCategory)}
                            className="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white"
                          >
                            <option value="IT">IT</option>
                            <option value="HR">HR</option>
                            <option value="Finance">Finance</option>
                            <option value="Admin">Admin</option>
                            <option value="Other">Other</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-[11px] font-medium text-slate-600 mb-1">Active Priority</label>
                          <select
                            value={overridePriority}
                            onChange={(e) => setOverridePriority(e.target.value as TicketPriority)}
                            className="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white"
                          >
                            <option value="High">High</option>
                            <option value="Medium">Medium</option>
                            <option value="Low">Low</option>
                          </select>
                        </div>
                      </div>

                      <button
                        onClick={handleApplyOverride}
                        disabled={
                          overrideLoading ||
                          (overrideCategory === activeTicket.category && overridePriority === activeTicket.priority)
                        }
                        className="w-full py-1.5 px-3 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-40"
                      >
                        {overrideLoading ? 'Updating...' : 'Update Classification (Audited)'}
                      </button>
                    </div>

                    {/* Audit Trail List */}
                    {auditLogs.length > 0 && (
                      <div>
                        <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                          <History className="w-3.5 h-3.5 text-indigo-600" />
                          <span>Override Audit History</span>
                        </div>
                        <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                          {auditLogs.map((log) => (
                            <div
                              key={log.id}
                              className="text-[11px] p-2 bg-slate-50 border border-slate-200/70 rounded-lg flex items-center justify-between"
                            >
                              <div>
                                <span className="font-semibold text-slate-800">{log.agent.name}</span> changed{' '}
                                <span className="font-medium text-indigo-700">{log.field_name}</span> from{' '}
                                <span className="line-through text-slate-400">{log.old_value}</span> to{' '}
                                <span className="font-semibold text-emerald-700">{log.new_value}</span>
                              </div>
                              <span className="text-[10px] text-slate-400">
                                {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* AI Draft & Final Reply Section */}
                    <div className="space-y-3 pt-2 border-t border-slate-100">
                      {activeTicket.ai_draft_reply && (
                        <div className="bg-indigo-50/50 border border-indigo-100 p-3 rounded-lg text-xs text-indigo-900">
                          <div className="flex items-center space-x-1 font-semibold text-indigo-800 mb-1">
                            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                            <span>Initial AI Draft Reply:</span>
                          </div>
                          <p className="italic text-indigo-800/80">{activeTicket.ai_draft_reply}</p>
                        </div>
                      )}

                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                          {activeTicket.status === 'Resolved' ? 'Final Reply Sent to Employee' : 'Edit & Send Final Reply'}
                        </label>
                        <textarea
                          rows={4}
                          disabled={activeTicket.status === 'Resolved'}
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-slate-100 disabled:text-slate-600"
                          placeholder="Type or customize the final reply..."
                        />
                      </div>

                      {activeTicket.status === 'Resolved' ? (
                        <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-medium flex items-center justify-between">
                          <span className="flex items-center">
                            <Check className="w-4 h-4 mr-1 text-emerald-600" /> Ticket Resolved
                          </span>
                          <span className="text-[10px] text-emerald-600">
                            {activeTicket.resolved_at ? new Date(activeTicket.resolved_at).toLocaleString() : ''}
                          </span>
                        </div>
                      ) : (
                        <button
                          onClick={handleSendReply}
                          disabled={replyLoading || !replyText.trim()}
                          className="w-full py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-xs rounded-lg shadow-sm transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
                        >
                          {replyLoading ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                          ) : (
                            <>
                              <Send className="w-4 h-4" />
                              <span>Send Reply & Mark Resolved</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="bg-white p-12 rounded-xl border border-slate-200 text-center text-slate-400 text-sm">
                    <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                    <p className="font-semibold text-slate-700">No ticket selected</p>
                    <p className="text-xs text-slate-400 mt-1">Select a ticket from the table to inspect details and respond.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        QuickDesk • AI Solution Engineer Assessment • Built with FastAPI, React, PostgreSQL & Groq
      </footer>
    </div>
  )
}
