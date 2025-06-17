import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { BaseMCPServer } from '../../shared/base-server.js';

const EmailSchema = z.object({
  to: z.string().email().describe('Recipient email address'),
  subject: z.string().describe('Email subject'),
  body: z.string().describe('Email body content'),
  cc: z.array(z.string().email()).optional().describe('CC recipients'),
  bcc: z.array(z.string().email()).optional().describe('BCC recipients'),
});

const CalendarEventSchema = z.object({
  title: z.string().describe('Event title'),
  description: z.string().optional().describe('Event description'),
  startTime: z.string().describe('Start time (ISO 8601 format)'),
  endTime: z.string().describe('End time (ISO 8601 format)'),
  attendees: z.array(z.string().email()).optional().describe('Attendee email addresses'),
  location: z.string().optional().describe('Event location'),
});

const TaskSchema = z.object({
  title: z.string().describe('Task title'),
  description: z.string().optional().describe('Task description'),
  priority: z.enum(['low', 'medium', 'high']).default('medium').describe('Task priority'),
  dueDate: z.string().optional().describe('Due date (ISO 8601 format)'),
  assignee: z.string().optional().describe('Assigned person'),
  tags: z.array(z.string()).optional().describe('Task tags'),
});

export class BusinessToolsMCPServer extends BaseMCPServer {
  constructor() {
    super('business-tools-mcp-server', '1.0.0');
  }

  protected getTools(): Tool[] {
    return [
      this.createTool(
        'send_email',
        'Send an email using the configured email service',
        EmailSchema
      ),
      this.createTool(
        'create_calendar_event',
        'Create a calendar event',
        CalendarEventSchema
      ),
      this.createTool(
        'create_task',
        'Create a new task in the task management system',
        TaskSchema
      ),
      this.createTool(
        'get_weather',
        'Get current weather information for a location',
        z.object({
          location: z.string().describe('Location (city, state/country)'),
        })
      ),
      this.createTool(
        'web_search',
        'Perform a web search and return results',
        z.object({
          query: z.string().describe('Search query'),
          limit: z.number().min(1).max(20).default(10).describe('Number of results to return'),
        })
      ),
      this.createTool(
        'generate_report',
        'Generate a business report based on data and template',
        z.object({
          reportType: z.enum(['sales', 'financial', 'operational', 'custom']).describe('Type of report'),
          dateRange: z.object({
            start: z.string().describe('Start date (ISO 8601)'),
            end: z.string().describe('End date (ISO 8601)'),
          }).describe('Date range for the report'),
          format: z.enum(['pdf', 'excel', 'json']).default('json').describe('Output format'),
          filters: z.record(z.any()).optional().describe('Additional filters'),
        })
      ),
    ];
  }

  protected async handleToolCall(name: string, args: any): Promise<any> {
    try {
      switch (name) {
        case 'send_email':
          return await this.sendEmail(args);
        case 'create_calendar_event':
          return await this.createCalendarEvent(args);
        case 'create_task':
          return await this.createTask(args);
        case 'get_weather':
          return await this.getWeather(args);
        case 'web_search':
          return await this.webSearch(args);
        case 'generate_report':
          return await this.generateReport(args);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      return this.createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }

  private async sendEmail(args: any) {
    const emailData = this.validateInput(EmailSchema, args);

    // Mock implementation - replace with actual email service integration
    console.log('Sending email:', emailData);

    return this.createSuccessResponse({
      operation: 'send_email',
      status: 'sent',
      messageId: `msg_${Date.now()}`,
      recipient: emailData.to,
      subject: emailData.subject,
      timestamp: new Date().toISOString(),
    });
  }

  private async createCalendarEvent(args: any) {
    const eventData = this.validateInput(CalendarEventSchema, args);

    // Mock implementation - replace with actual calendar service integration
    console.log('Creating calendar event:', eventData);

    return this.createSuccessResponse({
      operation: 'create_calendar_event',
      status: 'created',
      eventId: `evt_${Date.now()}`,
      title: eventData.title,
      startTime: eventData.startTime,
      endTime: eventData.endTime,
      timestamp: new Date().toISOString(),
    });
  }

  private async createTask(args: any) {
    const taskData = this.validateInput(TaskSchema, args);

    // Mock implementation - replace with actual task management integration
    console.log('Creating task:', taskData);

    return this.createSuccessResponse({
      operation: 'create_task',
      status: 'created',
      taskId: `task_${Date.now()}`,
      title: taskData.title,
      priority: taskData.priority,
      createdAt: new Date().toISOString(),
    });
  }

  private async getWeather(args: any) {
    const { location } = this.validateInput(
      z.object({ location: z.string() }),
      args
    );

    // Mock implementation - replace with actual weather API integration
    console.log('Getting weather for:', location);

    return this.createSuccessResponse({
      operation: 'get_weather',
      location,
      weather: {
        temperature: '22°C',
        condition: 'Partly cloudy',
        humidity: '65%',
        windSpeed: '10 km/h',
        timestamp: new Date().toISOString(),
      },
    });
  }

  private async webSearch(args: any) {
    const { query, limit } = this.validateInput(
      z.object({
        query: z.string(),
        limit: z.number().min(1).max(20).default(10),
      }),
      args
    );

    // Mock implementation - replace with actual search API integration
    console.log('Performing web search:', query);

    return this.createSuccessResponse({
      operation: 'web_search',
      query,
      results: Array.from({ length: Math.min(limit || 10, 3) }, (_, i) => ({
        title: `Search Result ${i + 1} for "${query}"`,
        url: `https://example.com/result-${i + 1}`,
        snippet: `This is a mock search result snippet for query: ${query}`,
      })),
      totalResults: limit || 10,
      timestamp: new Date().toISOString(),
    });
  }

  private async generateReport(args: any) {
    const reportData = this.validateInput(
      z.object({
        reportType: z.enum(['sales', 'financial', 'operational', 'custom']),
        dateRange: z.object({
          start: z.string(),
          end: z.string(),
        }),
        format: z.enum(['pdf', 'excel', 'json']).default('json'),
        filters: z.record(z.any()).optional(),
      }),
      args
    );

    // Mock implementation - replace with actual report generation
    console.log('Generating report:', reportData);

    return this.createSuccessResponse({
      operation: 'generate_report',
      reportId: `rpt_${Date.now()}`,
      type: reportData.reportType,
      format: reportData.format,
      dateRange: reportData.dateRange,
      status: 'generated',
      downloadUrl: `https://reports.example.com/report_${Date.now()}.${reportData.format}`,
      timestamp: new Date().toISOString(),
    });
  }
}

// Entry point for the server
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new BusinessToolsMCPServer();
  server.start().catch(console.error);
}
