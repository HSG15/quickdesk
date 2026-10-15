export type UserRole = 'employee' | 'agent'

export interface User {
  id: number
  name: string
  email: string
  role: UserRole
  created_at: string
}

export type TicketCategory = 'IT' | 'HR' | 'Finance' | 'Admin' | 'Other'
export type TicketPriority = 'Low' | 'Medium' | 'High'
export type TicketStatus = 'Open' | 'Resolved'

export interface TicketEmployeeSummary {
  id: number
  name: string
  email: string
}

export interface TicketCitation {
  article_id: string
  title: string
  source: string
  category?: string
  score?: number
}

export interface Ticket {
  id: number
  title: string
  description: string
  attachment_filename: string | null
  employee_id: number
  employee?: TicketEmployeeSummary
  category: TicketCategory
  priority: TicketPriority
  ai_suggested_category: TicketCategory | null
  ai_suggested_priority: TicketPriority | null
  ai_suggestion_method: string
  status: TicketStatus
  ai_draft_reply: string | null
  final_reply: string | null
  citations?: TicketCitation[]
  created_at: string
  resolved_at: string | null
  updated_at: string
}

export interface AuditLog {
  id: number
  ticket_id: number
  agent_id: number
  agent: {
    id: number
    name: string
    email: string
  }
  field_name: string
  old_value: string
  new_value: string
  created_at: string
}
