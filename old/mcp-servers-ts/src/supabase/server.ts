import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { BaseMCPServer } from '../shared/base-server.js';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

const QuerySchema = z.object({
  query: z.string().describe('SQL query to execute'),
  params: z.array(z.any()).optional().describe('Query parameters'),
});

const TableSchema = z.object({
  table: z.string().describe('Table name'),
  data: z.record(z.any()).describe('Data to insert/update'),
  conditions: z.record(z.any()).optional().describe('Conditions for update/delete'),
});

export class SupabaseMCPServer extends BaseMCPServer {
  private supabase: SupabaseClient;

  constructor() {
    super('supabase-mcp-server', '1.0.0');

    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseKey) {
      throw new Error('SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required');
    }

    this.supabase = createClient(supabaseUrl, supabaseKey);
  }

  protected getTools(): Tool[] {
    return [
      this.createTool(
        'query_database',
        'Execute a SQL query against the Supabase database',
        QuerySchema
      ),
      this.createTool(
        'insert_record',
        'Insert a new record into a table',
        TableSchema
      ),
      this.createTool(
        'update_record',
        'Update records in a table',
        TableSchema
      ),
      this.createTool(
        'delete_record',
        'Delete records from a table',
        z.object({
          table: z.string().describe('Table name'),
          conditions: z.record(z.any()).describe('Conditions for deletion'),
        })
      ),
      this.createTool(
        'list_tables',
        'List all tables in the database',
        z.object({})
      ),
    ];
  }

  protected async handleToolCall(name: string, args: any): Promise<any> {
    try {
      switch (name) {
        case 'query_database':
          return await this.queryDatabase(args);
        case 'insert_record':
          return await this.insertRecord(args);
        case 'update_record':
          return await this.updateRecord(args);
        case 'delete_record':
          return await this.deleteRecord(args);
        case 'list_tables':
          return await this.listTables();
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      return this.createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }

  private async queryDatabase(args: any) {
    const { query, params } = this.validateInput(QuerySchema, args);

    const { data, error } = await this.supabase.rpc('execute_sql', {
      query_text: query,
      query_params: params || [],
    });

    if (error) {
      throw new Error(`Database query failed: ${error.message}`);
    }

    return this.createSuccessResponse({
      query,
      results: data,
      count: Array.isArray(data) ? data.length : 1,
    });
  }

  private async insertRecord(args: any) {
    const { table, data } = this.validateInput(TableSchema, args);

    const { data: result, error } = await this.supabase
      .from(table)
      .insert(data)
      .select();

    if (error) {
      throw new Error(`Insert failed: ${error.message}`);
    }

    return this.createSuccessResponse({
      operation: 'insert',
      table,
      inserted: result,
    });
  }

  private async updateRecord(args: any) {
    const { table, data, conditions } = this.validateInput(TableSchema, args);

    if (!conditions) {
      throw new Error('Conditions are required for update operations');
    }

    let query = this.supabase.from(table).update(data);

    // Apply conditions
    for (const [key, value] of Object.entries(conditions)) {
      query = query.eq(key, value);
    }

    const { data: result, error } = await query.select();

    if (error) {
      throw new Error(`Update failed: ${error.message}`);
    }

    return this.createSuccessResponse({
      operation: 'update',
      table,
      updated: result,
    });
  }

  private async deleteRecord(args: any) {
    const { table, conditions } = this.validateInput(
      z.object({
        table: z.string(),
        conditions: z.record(z.any()),
      }),
      args
    );

    let query = this.supabase.from(table).delete();

    // Apply conditions
    for (const [key, value] of Object.entries(conditions)) {
      query = query.eq(key, value);
    }

    const { data: result, error } = await query.select();

    if (error) {
      throw new Error(`Delete failed: ${error.message}`);
    }

    return this.createSuccessResponse({
      operation: 'delete',
      table,
      deleted: result,
    });
  }

  private async listTables() {
    const { data, error } = await this.supabase.rpc('get_table_list');

    if (error) {
      throw new Error(`Failed to list tables: ${error.message}`);
    }

    return this.createSuccessResponse({
      tables: data,
    });
  }
}

// Entry point for the server
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new SupabaseMCPServer();
  server.start().catch(console.error);
}
