/**
 * ElfAutomations Control Center API Client
 */

export interface SystemStatus {
  status: string;
  health_score: number;
  active_teams: number;
  total_teams: number;
  active_workflows: number;
  system_load: number;
  api_availability: {
    supabase: boolean;
    openai: boolean;
    anthropic: boolean;
    n8n: boolean;
  };
  last_updated: string;
}

export interface TeamInfo {
  id: string;
  name: string;
  display_name: string;
  department: string;
  placement: string;
  status: string;
  framework: string;
  llm_provider: string;
  llm_model: string;
  member_count: number;
  is_manager: boolean;
  reports_to?: string;
  subordinate_teams: string[];
  is_top_level?: boolean;
  enable_chat_interface?: boolean;
  chat_config?: {
    allowed_roles?: string[];
    max_session_duration_minutes?: number;
    max_messages_per_session?: number;
    enable_delegation_preview?: boolean;
    context_window_messages?: number;
    require_user_confirmation?: boolean;
  };
}

export interface CostMetrics {
  today_cost: number;
  today_budget: number;
  today_percentage: number;
  month_cost: number;
  month_budget: number;
  trend: 'up' | 'down' | 'stable';
  top_teams: Array<{
    team_name: string;
    total_cost: number;
    request_count: number;
  }>;
  cost_by_model: Record<string, number>;
  hourly_costs: Array<{
    hour: number;
    cost: number;
    requests: number;
  }>;
}

export interface WorkflowStatus {
  id: string;
  name: string;
  status: string;
  last_run?: string;
  success_rate: number;
  avg_duration: number;
  executions_today: number;
}

export interface WorkflowGenerateRequest {
  description: string;
  name: string;
  team: string;
  category: string;
}

export interface WorkflowGenerateResponse {
  workflow: any;
  metadata: {
    description: string;
    team: string;
    category: string;
    pattern?: string;
    trigger_type?: string;
    services?: any;
    created_at: string;
  };
}

export interface WorkflowDeployRequest {
  workflow: any;
  metadata: any;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  currentDescription?: string;
  context: string;
}

export interface WorkflowAnalysisRequest {
  workflow: any;
}

export interface WorkflowAnalysisResponse {
  issues: Array<{
    type: string;
    severity: string;
    node_id: string | null;
    title: string;
    description: string;
    recommendation: string;
    estimated_impact?: string;
  }>;
  metrics: {
    node_count: number;
    connection_count: number;
    complexity_score: number;
    estimated_execution_time: number;
    estimated_cost_per_run: number;
    parallel_execution_opportunities: number;
    ai_node_count: number;
    external_api_calls: number;
    database_operations: number;
  };
  suggestions: Array<{
    title: string;
    description: string;
    expected_improvement: string;
    implementation_steps: string[];
    complexity: string;
  }>;
  estimated_cost: number;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  difficulty: string;
  success_rate: number;
  usage_count: number;
}

export interface ChatResponse {
  content: string;
  suggestions?: string[];
}

export interface Activity {
  id: string;
  timestamp: string;
  type: string;
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'error';
  team?: string;
}

export interface DashboardData {
  system_status: SystemStatus;
  cost_metrics: CostMetrics;
  teams: TeamInfo[];
  workflows: WorkflowStatus[];
  recent_activities: Activity[];
  alerts: any[];
}

class ControlCenterAPI {
  private baseUrl: string;
  private ws: WebSocket | null = null;

  constructor(baseUrl: string = 'http://localhost:8001') {
    this.baseUrl = baseUrl;
  }

  // Fetch methods
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await fetch(`${this.baseUrl}/api/system/status`);
    if (!response.ok) throw new Error('Failed to fetch system status');
    return response.json();
  }

  async getCostMetrics(): Promise<CostMetrics> {
    const response = await fetch(`${this.baseUrl}/api/costs/metrics`);
    if (!response.ok) throw new Error('Failed to fetch cost metrics');
    return response.json();
  }

  async getTeams(): Promise<TeamInfo[]> {
    const response = await fetch(`${this.baseUrl}/api/teams`);
    if (!response.ok) throw new Error('Failed to fetch teams');
    return response.json();
  }

  async getWorkflows(): Promise<WorkflowStatus[]> {
    const response = await fetch(`${this.baseUrl}/api/workflows`);
    if (!response.ok) throw new Error('Failed to fetch workflows');
    return response.json();
  }

  async getChatToken(teamId: string): Promise<{ token: string; expires_in: number }> {
    const response = await fetch(`${this.baseUrl}/api/teams/${teamId}/chat/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Include auth headers if available
        ...(localStorage.getItem('auth_token') && {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        })
      }
    });
    if (!response.ok) throw new Error('Failed to get chat token');
    return response.json();
  }

  async generateWorkflow(request: WorkflowGenerateRequest): Promise<WorkflowGenerateResponse> {
    const response = await fetch(`${this.baseUrl}/api/workflows/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Failed to generate workflow');
    }
    return response.json();
  }

  async generateAIWorkflow(request: WorkflowGenerateRequest & { use_ai: boolean }): Promise<WorkflowGenerateResponse> {
    const response = await fetch(`${this.baseUrl}/api/workflows/generate-ai`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Failed to generate AI workflow');
    }
    return response.json();
  }

  async analyzeWorkflow(request: WorkflowAnalysisRequest): Promise<WorkflowAnalysisResponse> {
    const response = await fetch(`${this.baseUrl}/api/workflows/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Failed to analyze workflow');
    }
    return response.json();
  }

  async getWorkflowTemplates(category?: string): Promise<{ templates: WorkflowTemplate[] }> {
    const url = category
      ? `${this.baseUrl}/api/workflows/templates?category=${category}`
      : `${this.baseUrl}/api/workflows/templates`;

    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch templates');
    return response.json();
  }

  async deployWorkflow(request: WorkflowDeployRequest): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/workflows/deploy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Failed to deploy workflow');
    }
    return response.json();
  }

  async chatWithWorkflowAssistant(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/workflows/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Failed to chat with assistant');
    }
    return response.json();
  }

  async getActivities(): Promise<Activity[]> {
    const response = await fetch(`${this.baseUrl}/api/activities`);
    if (!response.ok) throw new Error('Failed to fetch activities');
    return response.json();
  }

  async getDashboardData(): Promise<DashboardData> {
    const response = await fetch(`${this.baseUrl}/api/dashboard`);
    if (!response.ok) throw new Error('Failed to fetch dashboard data');
    return response.json();
  }

  // WebSocket methods
  connectWebSocket(onMessage: (data: any) => void, onError?: (error: Event) => void) {
    this.ws = new WebSocket(`ws://localhost:8001/ws`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        this.connectWebSocket(onMessage, onError);
      }, 5000);
    };
  }

  disconnectWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // Utility methods
  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(amount);
  }

  formatPercentage(value: number): string {
    return `${value.toFixed(1)}%`;
  }

  formatDuration(seconds: number): string {
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  }
}

// Export singleton instance
export const api = new ControlCenterAPI();

// Export types and class
export { ControlCenterAPI };
