import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { google } from 'googleapis';
import { OAuth2Client } from 'google-auth-library';
import { createClient } from '@supabase/supabase-js';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';

// Types
interface WatchFolder {
  folderId: string;
  tenantName: string;
  lastChecked: Date;
  webhookId?: string;
}

interface DocumentMetadata {
  id: string;
  name: string;
  mimeType: string;
  size: number;
  modifiedTime: string;
  md5Checksum: string;
  webViewLink: string;
  parents: string[];
}

class GoogleDriveWatcherServer {
  private server: Server;
  private oauth2Client: OAuth2Client;
  private drive: any;
  private supabase: any;
  private watchFolders: Map<string, WatchFolder> = new Map();
  private monitoringInterval: NodeJS.Timeout | null = null;
  private isMonitoring = false;

  constructor() {
    this.server = new Server(
      {
        name: "google-drive-watcher",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Initialize OAuth2 client
    this.oauth2Client = new OAuth2Client(
      process.env.GOOGLE_CLIENT_ID,
      process.env.GOOGLE_CLIENT_SECRET,
      process.env.GOOGLE_REDIRECT_URI || 'http://localhost:8080/oauth2callback'
    );

    // Initialize Supabase client
    this.supabase = createClient(
      process.env.SUPABASE_URL || '',
      process.env.SUPABASE_KEY || ''
    );

    this.setupHandlers();
    this.loadConfiguration();
  }

  private async loadConfiguration() {
    try {
      // Load saved tokens if available
      const tokenPath = path.join(__dirname, '../.google-tokens.json');
      if (fs.existsSync(tokenPath)) {
        const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'));
        this.oauth2Client.setCredentials(tokens);
        this.drive = google.drive({ version: 'v3', auth: this.oauth2Client });
      }

      // Load watched folders from Supabase
      const { data: folders } = await this.supabase
        .from('rag_watch_folders')
        .select('*');

      if (folders) {
        folders.forEach((folder: any) => {
          this.watchFolders.set(folder.folder_id, {
            folderId: folder.folder_id,
            tenantName: folder.tenant_name,
            lastChecked: new Date(folder.last_checked),
            webhookId: folder.webhook_id
          });
        });
      }
    } catch (error) {
      console.error('Failed to load configuration:', error);
    }
  }

  private setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "authenticate",
          description: "Set up Google OAuth authentication",
          inputSchema: {
            type: "object",
            properties: {
              authCode: {
                type: "string",
                description: "OAuth authorization code"
              }
            }
          }
        },
        {
          name: "get_auth_url",
          description: "Get Google OAuth authentication URL",
          inputSchema: {
            type: "object",
            properties: {}
          }
        },
        {
          name: "add_watch_folder",
          description: "Add a folder to monitor for changes",
          inputSchema: {
            type: "object",
            properties: {
              folderId: {
                type: "string",
                description: "Google Drive folder ID"
              },
              tenantName: {
                type: "string",
                description: "Tenant name (e.g., 'acme-corp')"
              }
            },
            required: ["folderId", "tenantName"]
          }
        },
        {
          name: "remove_watch_folder",
          description: "Stop monitoring a folder",
          inputSchema: {
            type: "object",
            properties: {
              folderId: {
                type: "string",
                description: "Google Drive folder ID"
              }
            },
            required: ["folderId"]
          }
        },
        {
          name: "list_watch_folders",
          description: "List all monitored folders",
          inputSchema: {
            type: "object",
            properties: {}
          }
        },
        {
          name: "list_documents",
          description: "List documents in a folder",
          inputSchema: {
            type: "object",
            properties: {
              folderId: {
                type: "string",
                description: "Google Drive folder ID"
              },
              pageSize: {
                type: "number",
                description: "Number of results per page (default: 100)"
              },
              pageToken: {
                type: "string",
                description: "Token for next page of results"
              }
            },
            required: ["folderId"]
          }
        },
        {
          name: "get_document_metadata",
          description: "Get detailed metadata for a document",
          inputSchema: {
            type: "object",
            properties: {
              fileId: {
                type: "string",
                description: "Google Drive file ID"
              }
            },
            required: ["fileId"]
          }
        },
        {
          name: "download_document",
          description: "Download a document from Google Drive",
          inputSchema: {
            type: "object",
            properties: {
              fileId: {
                type: "string",
                description: "Google Drive file ID"
              },
              outputPath: {
                type: "string",
                description: "Local path to save the file"
              }
            },
            required: ["fileId", "outputPath"]
          }
        },
        {
          name: "queue_document",
          description: "Queue a document for RAG processing",
          inputSchema: {
            type: "object",
            properties: {
              fileId: {
                type: "string",
                description: "Google Drive file ID"
              },
              tenantName: {
                type: "string",
                description: "Tenant name"
              },
              priority: {
                type: "number",
                description: "Processing priority (1-10, default: 5)"
              }
            },
            required: ["fileId", "tenantName"]
          }
        },
        {
          name: "start_monitoring",
          description: "Start monitoring folders for changes",
          inputSchema: {
            type: "object",
            properties: {
              intervalSeconds: {
                type: "number",
                description: "Check interval in seconds (default: 300)"
              }
            }
          }
        },
        {
          name: "stop_monitoring",
          description: "Stop monitoring folders",
          inputSchema: {
            type: "object",
            properties: {}
          }
        },
        {
          name: "process_changes",
          description: "Manually check for and process folder changes",
          inputSchema: {
            type: "object",
            properties: {
              folderId: {
                type: "string",
                description: "Specific folder to check (optional)"
              }
            }
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "get_auth_url":
            return await this.getAuthUrl();
          
          case "authenticate":
            if (!args || typeof args !== 'object' || !('authCode' in args)) {
              throw new Error("authCode is required");
            }
            return await this.authenticate(args.authCode as string);
          
          case "add_watch_folder":
            if (!args || typeof args !== 'object' || !('folderId' in args) || !('tenantName' in args)) {
              throw new Error("folderId and tenantName are required");
            }
            return await this.addWatchFolder(args.folderId as string, args.tenantName as string);
          
          case "remove_watch_folder":
            if (!args || typeof args !== 'object' || !('folderId' in args)) {
              throw new Error("folderId is required");
            }
            return await this.removeWatchFolder(args.folderId as string);
          
          case "list_watch_folders":
            return await this.listWatchFolders();
          
          case "list_documents":
            if (!args || typeof args !== 'object' || !('folderId' in args)) {
              throw new Error("folderId is required");
            }
            return await this.listDocuments(
              args.folderId as string, 
              args.pageSize as number | undefined, 
              args.pageToken as string | undefined
            );
          
          case "get_document_metadata":
            if (!args || typeof args !== 'object' || !('fileId' in args)) {
              throw new Error("fileId is required");
            }
            return await this.getDocumentMetadata(args.fileId as string);
          
          case "download_document":
            if (!args || typeof args !== 'object' || !('fileId' in args) || !('outputPath' in args)) {
              throw new Error("fileId and outputPath are required");
            }
            return await this.downloadDocument(args.fileId as string, args.outputPath as string);
          
          case "queue_document":
            if (!args || typeof args !== 'object' || !('fileId' in args) || !('tenantName' in args)) {
              throw new Error("fileId and tenantName are required");
            }
            return await this.queueDocument(
              args.fileId as string, 
              args.tenantName as string, 
              args.priority as number | undefined
            );
          
          case "start_monitoring":
            return await this.startMonitoring(
              args && typeof args === 'object' && 'intervalSeconds' in args 
                ? args.intervalSeconds as number 
                : undefined
            );
          
          case "stop_monitoring":
            return await this.stopMonitoring();
          
          case "process_changes":
            return await this.processChanges(
              args && typeof args === 'object' && 'folderId' in args 
                ? args.folderId as string 
                : undefined
            );
          
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error: any) {
        throw new McpError(
          ErrorCode.InternalError,
          error.message || "Operation failed"
        );
      }
    });
  }

  private async getAuthUrl() {
    const authUrl = this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
      ]
    });

    return {
      content: [
        {
          type: "text",
          text: `Please visit this URL to authenticate:\n${authUrl}\n\nAfter authentication, you'll receive an authorization code. Use the 'authenticate' tool with that code.`
        }
      ]
    };
  }

  private async authenticate(authCode: string) {
    const { tokens } = await this.oauth2Client.getToken(authCode);
    this.oauth2Client.setCredentials(tokens);
    
    // Save tokens for future use
    const tokenPath = path.join(__dirname, '../.google-tokens.json');
    fs.writeFileSync(tokenPath, JSON.stringify(tokens));
    
    // Initialize Drive API
    this.drive = google.drive({ version: 'v3', auth: this.oauth2Client });
    
    return {
      content: [
        {
          type: "text",
          text: "Successfully authenticated with Google Drive!"
        }
      ]
    };
  }

  private async addWatchFolder(folderId: string, tenantName: string) {
    if (!this.drive) {
      throw new Error("Not authenticated. Please run 'authenticate' first.");
    }

    // Verify folder exists and is accessible
    const folder = await this.drive.files.get({
      fileId: folderId,
      fields: 'id,name,mimeType'
    });

    if (folder.data.mimeType !== 'application/vnd.google-apps.folder') {
      throw new Error("The specified ID is not a folder");
    }

    // Add to watch list
    this.watchFolders.set(folderId, {
      folderId,
      tenantName,
      lastChecked: new Date()
    });

    // Save to Supabase
    await this.supabase.from('rag_watch_folders').upsert({
      folder_id: folderId,
      tenant_name: tenantName,
      folder_name: folder.data.name,
      last_checked: new Date().toISOString()
    });

    return {
      content: [
        {
          type: "text",
          text: `Added folder '${folder.data.name}' (${folderId}) to watch list for tenant '${tenantName}'`
        }
      ]
    };
  }

  private async removeWatchFolder(folderId: string) {
    if (!this.watchFolders.has(folderId)) {
      throw new Error("Folder not in watch list");
    }

    this.watchFolders.delete(folderId);
    
    // Remove from Supabase
    await this.supabase
      .from('rag_watch_folders')
      .delete()
      .eq('folder_id', folderId);

    return {
      content: [
        {
          type: "text",
          text: `Removed folder ${folderId} from watch list`
        }
      ]
    };
  }

  private async listWatchFolders() {
    const folders = Array.from(this.watchFolders.entries()).map(([id, folder]) => ({
      folderId: id,
      tenantName: folder.tenantName,
      lastChecked: folder.lastChecked.toISOString()
    }));

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(folders, null, 2)
        }
      ]
    };
  }

  private async listDocuments(folderId: string, pageSize = 100, pageToken?: string) {
    if (!this.drive) {
      throw new Error("Not authenticated. Please run 'authenticate' first.");
    }

    const response = await this.drive.files.list({
      q: `'${folderId}' in parents and trashed = false`,
      fields: 'nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum, webViewLink)',
      pageSize,
      pageToken
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            files: response.data.files,
            nextPageToken: response.data.nextPageToken
          }, null, 2)
        }
      ]
    };
  }

  private async getDocumentMetadata(fileId: string): Promise<any> {
    if (!this.drive) {
      throw new Error("Not authenticated. Please run 'authenticate' first.");
    }

    const response = await this.drive.files.get({
      fileId,
      fields: 'id,name,mimeType,size,modifiedTime,md5Checksum,webViewLink,parents,description,properties'
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(response.data, null, 2)
        }
      ]
    };
  }

  private async downloadDocument(fileId: string, outputPath: string) {
    if (!this.drive) {
      throw new Error("Not authenticated. Please run 'authenticate' first.");
    }

    // Get file metadata first
    const metadata = await this.drive.files.get({
      fileId,
      fields: 'name,mimeType'
    });

    // Create output directory if needed
    const outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Download file
    const dest = fs.createWriteStream(outputPath);
    const response = await this.drive.files.get(
      { fileId, alt: 'media' },
      { responseType: 'stream' }
    );

    return new Promise((resolve, reject) => {
      response.data
        .on('end', () => {
          resolve({
            content: [
              {
                type: "text",
                text: `Downloaded '${metadata.data.name}' to ${outputPath}`
              }
            ]
          });
        })
        .on('error', (err: any) => {
          reject(new Error(`Download failed: ${err.message}`));
        })
        .pipe(dest);
    });
  }

  private async queueDocument(fileId: string, tenantName: string, priority = 5) {
    if (!this.drive) {
      throw new Error("Not authenticated. Please run 'authenticate' first.");
    }

    // Get document metadata
    const metadata = await this.drive.files.get({
      fileId,
      fields: 'id,name,mimeType,size,modifiedTime,md5Checksum,webViewLink,parents'
    });

    // Get tenant ID
    const { data: tenant } = await this.supabase
      .from('rag_tenants')
      .select('id')
      .eq('name', tenantName)
      .single();

    if (!tenant) {
      throw new Error(`Tenant '${tenantName}' not found`);
    }

    // Check if document already exists
    const { data: existingDoc } = await this.supabase
      .from('rag_documents')
      .select('id')
      .eq('source_id', fileId)
      .eq('tenant_id', tenant.id)
      .single();

    let documentId;
    
    if (existingDoc) {
      documentId = existingDoc.id;
      // Update document status
      await this.supabase
        .from('rag_documents')
        .update({ status: 'queued' })
        .eq('id', documentId);
    } else {
      // Create document record
      const { data: newDoc } = await this.supabase
        .from('rag_documents')
        .insert({
          tenant_id: tenant.id,
          source_type: 'google_drive',
          source_id: fileId,
          source_path: `drive://${fileId}`,
          filename: metadata.data.name,
          mime_type: metadata.data.mimeType,
          size_bytes: parseInt(metadata.data.size || '0'),
          checksum: metadata.data.md5Checksum,
          status: 'queued'
        })
        .select('id')
        .single();
      
      documentId = newDoc.id;
    }

    // Add to processing queue
    await this.supabase
      .from('rag_processing_queue')
      .insert({
        tenant_id: tenant.id,
        document_id: documentId,
        priority,
        processor_type: this.getProcessorType(metadata.data.mimeType),
        processing_config: {
          source: 'google_drive',
          file_id: fileId
        }
      });

    return {
      content: [
        {
          type: "text",
          text: `Queued document '${metadata.data.name}' for processing with priority ${priority}`
        }
      ]
    };
  }

  private getProcessorType(mimeType: string): string {
    // Map MIME types to processors
    const typeMap: { [key: string]: string } = {
      'application/pdf': 'pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
      'text/plain': 'text',
      'text/csv': 'csv',
      'application/vnd.google-apps.document': 'google_doc',
      'application/vnd.google-apps.spreadsheet': 'google_sheet'
    };

    return typeMap[mimeType] || 'general';
  }

  private async startMonitoring(intervalSeconds = 300) {
    if (this.isMonitoring) {
      return {
        content: [
          {
            type: "text",
            text: "Monitoring is already active"
          }
        ]
      };
    }

    this.isMonitoring = true;
    
    // Run initial check
    await this.processChanges();
    
    // Set up interval
    this.monitoringInterval = setInterval(async () => {
      try {
        await this.processChanges();
      } catch (error) {
        console.error('Error in monitoring cycle:', error);
      }
    }, intervalSeconds * 1000);

    return {
      content: [
        {
          type: "text",
          text: `Started monitoring ${this.watchFolders.size} folders with ${intervalSeconds}s interval`
        }
      ]
    };
  }

  private async stopMonitoring() {
    if (!this.isMonitoring) {
      return {
        content: [
          {
            type: "text",
            text: "Monitoring is not active"
          }
        ]
      };
    }

    this.isMonitoring = false;
    
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    return {
      content: [
        {
          type: "text",
          text: "Stopped monitoring"
        }
      ]
    };
  }

  private async processChanges(specificFolderId?: string) {
    if (!this.drive) {
      throw new Error("Not authenticated. Please run 'authenticate' first.");
    }

    const foldersToCheck = specificFolderId 
      ? [this.watchFolders.get(specificFolderId)].filter(Boolean)
      : Array.from(this.watchFolders.values());

    const results = [];

    for (const folder of foldersToCheck) {
      try {
        // Get files modified since last check
        const response = await this.drive.files.list({
          q: `'${folder.folderId}' in parents and modifiedTime > '${folder.lastChecked.toISOString()}' and trashed = false`,
          fields: 'files(id, name, mimeType, size, modifiedTime)',
          pageSize: 100
        });

        const newFiles = response.data.files || [];
        
        // Queue new files for processing
        for (const file of newFiles) {
          if (file.mimeType !== 'application/vnd.google-apps.folder') {
            await this.queueDocument(file.id, folder.tenantName);
          }
        }

        // Update last checked time
        folder.lastChecked = new Date();
        await this.supabase
          .from('rag_watch_folders')
          .update({ last_checked: folder.lastChecked.toISOString() })
          .eq('folder_id', folder.folderId);

        results.push({
          folderId: folder.folderId,
          tenantName: folder.tenantName,
          newFiles: newFiles.length,
          files: newFiles.map(f => f.name)
        });

      } catch (error: any) {
        results.push({
          folderId: folder.folderId,
          tenantName: folder.tenantName,
          error: error.message
        });
      }
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(results, null, 2)
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

// Create necessary tables in Supabase if they don't exist
// Note: This table should already be created by the main schema
const initSQL = `
-- Table rag_watch_folders should already exist from main schema
-- If not, it needs to be created with:
-- CREATE TABLE IF NOT EXISTS rag_watch_folders (...)
`;

const server = new GoogleDriveWatcherServer();
server.run().catch(console.error);