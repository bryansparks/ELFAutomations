import { z } from 'zod';
import { BaseMCPServer } from '../shared/base-server.js';
import { createClient } from '@supabase/supabase-js';
import { v4 as uuidv4 } from 'uuid';
// Schema definitions for memory operations
const StoreMemorySchema = z.object({
    content: z.string().describe('Memory content to store'),
    type: z.enum(['interaction', 'decision', 'learning', 'experience', 'insight']).describe('Type of memory'),
    context: z.record(z.any()).describe('Additional context as key-value pairs'),
    team_id: z.string().optional().describe('Team ID that created this memory'),
    agent_name: z.string().optional().describe('Agent name that created this memory'),
    tags: z.array(z.string()).optional().describe('Tags for categorization'),
    importance_score: z.number().min(0).max(1).optional().describe('Importance score (0-1)'),
});
const RetrieveMemoriesSchema = z.object({
    query: z.string().describe('Search query for semantic similarity'),
    filters: z.object({
        team_id: z.string().optional(),
        type: z.string().optional(),
        tags: z.array(z.string()).optional(),
        min_importance: z.number().optional(),
    }).optional().describe('Filters to apply'),
    top_k: z.number().min(1).max(100).default(10).describe('Number of results to return'),
});
const GetSimilarExperiencesSchema = z.object({
    situation: z.string().describe('Current situation description'),
    team_id: z.string().optional().describe('Filter by team ID'),
    min_similarity: z.number().min(0).max(1).default(0.7).describe('Minimum similarity score'),
});
const FindSuccessfulPatternsSchema = z.object({
    task_type: z.string().describe('Type of task to find patterns for'),
    min_confidence: z.number().min(0).max(1).default(0.7).describe('Minimum confidence score'),
    limit: z.number().min(1).max(50).default(10).describe('Maximum patterns to return'),
});
const AnalyzeOutcomeSchema = z.object({
    action: z.string().describe('Action that was taken'),
    result: z.record(z.any()).describe('Result of the action'),
    context: z.record(z.any()).describe('Context in which action was taken'),
    success: z.boolean().describe('Was the outcome successful?'),
});
const UpdatePatternConfidenceSchema = z.object({
    pattern_id: z.string().describe('Pattern ID to update'),
    success: z.boolean().describe('Was this pattern successful in new application?'),
});
const GetTeamInsightsSchema = z.object({
    team_id: z.string().describe('Team ID to get insights for'),
    timeframe: z.enum(['day', 'week', 'month', 'quarter', 'year', 'all']).default('month').describe('Time period for insights'),
});
const CreateCollectionSchema = z.object({
    name: z.string().describe('Collection name'),
    description: z.string().describe('Collection description'),
    config: z.record(z.any()).optional().describe('Collection configuration'),
    team_id: z.string().optional().describe('Team that owns this collection'),
});
const PruneOldMemoriesSchema = z.object({
    retention_policy: z.object({
        days: z.number().min(1).optional().describe('Keep memories for N days'),
        max_count: z.number().min(1).optional().describe('Keep only N most recent memories'),
        min_importance: z.number().min(0).max(1).optional().describe('Keep only memories above this importance'),
    }).describe('Retention policy to apply'),
    dry_run: z.boolean().default(true).describe('Preview what would be deleted without actually deleting'),
});
const ExportKnowledgeBaseSchema = z.object({
    format: z.enum(['json', 'csv', 'markdown']).describe('Export format'),
    filters: z.object({
        team_id: z.string().optional(),
        type: z.string().optional(),
        start_date: z.string().optional(),
        end_date: z.string().optional(),
    }).optional().describe('Filters to apply to export'),
});
export class MemoryLearningMCPServer extends BaseMCPServer {
    supabase;
    mockQdrant;
    embeddingCache = new Map();
    constructor() {
        super('memory-learning-mcp-server', '1.0.0');
        const supabaseUrl = process.env.SUPABASE_URL;
        const supabaseKey = process.env.SUPABASE_SERVICE_KEY;
        if (!supabaseUrl || !supabaseKey) {
            throw new Error('Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables');
        }
        this.supabase = createClient(supabaseUrl, supabaseKey);
        // Initialize mock Qdrant client
        this.mockQdrant = this.createMockQdrantClient();
    }
    createMockQdrantClient() {
        const storage = new Map();
        return {
            async upsert(collection, points) {
                if (!storage.has(collection)) {
                    storage.set(collection, []);
                }
                const existing = storage.get(collection);
                points.forEach(point => {
                    const index = existing.findIndex(p => p.id === point.id);
                    if (index >= 0) {
                        existing[index] = point;
                    }
                    else {
                        existing.push(point);
                    }
                });
            },
            async search(collection, query) {
                const points = storage.get(collection) || [];
                // Simple mock search - in real implementation would use vector similarity
                return points.slice(0, query.limit || 10).map(p => ({
                    id: p.id,
                    score: Math.random() * 0.5 + 0.5, // Mock similarity score
                    payload: p.payload
                }));
            },
            async delete(collection, ids) {
                const points = storage.get(collection) || [];
                const filtered = points.filter(p => !ids.includes(p.id));
                storage.set(collection, filtered);
            }
        };
    }
    async generateMockEmbedding(text) {
        // Check cache first
        if (this.embeddingCache.has(text)) {
            return this.embeddingCache.get(text);
        }
        // Generate deterministic mock embedding based on text
        const embedding = new Array(1536).fill(0).map((_, i) => {
            const charCode = text.charCodeAt(i % text.length) || 0;
            return Math.sin(charCode * (i + 1)) * 0.1;
        });
        this.embeddingCache.set(text, embedding);
        return embedding;
    }
    tools() {
        return [
            {
                name: 'store_memory',
                description: 'Store experiences with embeddings in vector database',
                inputSchema: {
                    type: 'object',
                    properties: StoreMemorySchema.shape,
                    required: ['content', 'type'],
                },
            },
            {
                name: 'retrieve_memories',
                description: 'Semantic search for relevant memories',
                inputSchema: {
                    type: 'object',
                    properties: RetrieveMemoriesSchema.shape,
                    required: ['query'],
                },
            },
            {
                name: 'get_similar_experiences',
                description: 'Find related past situations',
                inputSchema: {
                    type: 'object',
                    properties: GetSimilarExperiencesSchema.shape,
                    required: ['situation'],
                },
            },
            {
                name: 'find_successful_patterns',
                description: 'Identify patterns that led to success',
                inputSchema: {
                    type: 'object',
                    properties: FindSuccessfulPatternsSchema.shape,
                    required: ['task_type'],
                },
            },
            {
                name: 'analyze_outcome',
                description: 'Learn from action results',
                inputSchema: {
                    type: 'object',
                    properties: AnalyzeOutcomeSchema.shape,
                    required: ['action', 'result', 'context', 'success'],
                },
            },
            {
                name: 'update_pattern_confidence',
                description: 'Adjust confidence based on new data',
                inputSchema: {
                    type: 'object',
                    properties: UpdatePatternConfidenceSchema.shape,
                    required: ['pattern_id', 'success'],
                },
            },
            {
                name: 'get_team_insights',
                description: 'Analytics and insights per team',
                inputSchema: {
                    type: 'object',
                    properties: GetTeamInsightsSchema.shape,
                    required: ['team_id'],
                },
            },
            {
                name: 'create_collection',
                description: 'Organize memory spaces',
                inputSchema: {
                    type: 'object',
                    properties: CreateCollectionSchema.shape,
                    required: ['name', 'description'],
                },
            },
            {
                name: 'prune_old_memories',
                description: 'Manage memory retention',
                inputSchema: {
                    type: 'object',
                    properties: PruneOldMemoriesSchema.shape,
                    required: ['retention_policy'],
                },
            },
            {
                name: 'export_knowledge_base',
                description: 'Export knowledge for backup or sharing',
                inputSchema: {
                    type: 'object',
                    properties: ExportKnowledgeBaseSchema.shape,
                    required: ['format'],
                },
            },
        ];
    }
    async handleToolCall(name, args) {
        switch (name) {
            case 'store_memory':
                return this.storeMemory(args);
            case 'retrieve_memories':
                return this.retrieveMemories(args);
            case 'get_similar_experiences':
                return this.getSimilarExperiences(args);
            case 'find_successful_patterns':
                return this.findSuccessfulPatterns(args);
            case 'analyze_outcome':
                return this.analyzeOutcome(args);
            case 'update_pattern_confidence':
                return this.updatePatternConfidence(args);
            case 'get_team_insights':
                return this.getTeamInsights(args);
            case 'create_collection':
                return this.createCollection(args);
            case 'prune_old_memories':
                return this.pruneOldMemories(args);
            case 'export_knowledge_base':
                return this.exportKnowledgeBase(args);
            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    }
    async storeMemory(args) {
        try {
            // Generate ID and embedding
            const memoryId = uuidv4();
            const vectorId = uuidv4();
            const embedding = await this.generateMockEmbedding(args.content);
            // Store in Supabase
            const { data, error } = await this.supabase
                .from('memory_entries')
                .insert({
                id: memoryId,
                team_id: args.team_id,
                agent_name: args.agent_name,
                entry_type: args.type,
                title: args.content.substring(0, 100) + (args.content.length > 100 ? '...' : ''),
                content: args.content,
                context: args.context || {},
                tags: args.tags || [],
                vector_id: vectorId,
                collection_name: 'default',
                embedding_model: 'mock-embedding',
                embedding_dimension: 1536,
                importance_score: args.importance_score || 0.5,
            })
                .select()
                .single();
            if (error)
                throw error;
            // Store in mock Qdrant
            await this.mockQdrant.upsert('default', [{
                    id: vectorId,
                    vector: embedding,
                    payload: {
                        memory_id: memoryId,
                        team_id: args.team_id,
                        type: args.type,
                        content: args.content,
                        tags: args.tags || [],
                    }
                }]);
            return {
                success: true,
                memory_id: memoryId,
                vector_id: vectorId,
                message: 'Memory stored successfully',
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error storing memory',
            };
        }
    }
    async retrieveMemories(args) {
        try {
            // Generate query embedding
            const queryEmbedding = await this.generateMockEmbedding(args.query);
            // Search in mock Qdrant
            const searchResults = await this.mockQdrant.search('default', {
                vector: queryEmbedding,
                limit: args.top_k,
                filter: args.filters,
            });
            // Fetch full memory details from Supabase
            const memoryIds = searchResults.map(r => r.payload.memory_id);
            if (memoryIds.length === 0) {
                return {
                    success: true,
                    memories: [],
                    message: 'No relevant memories found',
                };
            }
            let query = this.supabase
                .from('memory_entries')
                .select('*')
                .in('id', memoryIds);
            // Apply filters
            if (args.filters?.team_id) {
                query = query.eq('team_id', args.filters.team_id);
            }
            if (args.filters?.type) {
                query = query.eq('entry_type', args.filters.type);
            }
            if (args.filters?.min_importance) {
                query = query.gte('importance_score', args.filters.min_importance);
            }
            const { data, error } = await query;
            if (error)
                throw error;
            // Combine with similarity scores
            const memories = data?.map(memory => {
                const searchResult = searchResults.find(r => r.payload.memory_id === memory.id);
                return {
                    ...memory,
                    similarity_score: searchResult?.score || 0,
                };
            }).sort((a, b) => b.similarity_score - a.similarity_score);
            // Update access counts
            await this.supabase
                .from('memory_access_logs')
                .insert(memoryIds.map(id => ({
                memory_id: id,
                access_type: 'search',
                query_text: args.query,
            })));
            return {
                success: true,
                memories: memories || [],
                total_found: memories?.length || 0,
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error retrieving memories',
            };
        }
    }
    async getSimilarExperiences(args) {
        // Reuse retrieve_memories with specific filters
        const searchArgs = {
            query: args.situation,
            filters: {
                team_id: args.team_id,
                type: 'experience',
            },
            top_k: 20,
        };
        const result = await this.retrieveMemories(searchArgs);
        if (result.success && result.memories) {
            // Filter by minimum similarity
            const filtered = result.memories.filter(m => m.similarity_score >= args.min_similarity);
            return {
                success: true,
                experiences: filtered,
                message: `Found ${filtered.length} similar experiences`,
            };
        }
        return result;
    }
    async findSuccessfulPatterns(args) {
        try {
            const { data, error } = await this.supabase
                .from('learning_patterns')
                .select('*')
                .eq('pattern_type', 'success')
                .gte('confidence_score', args.min_confidence)
                .order('confidence_score', { ascending: false })
                .limit(args.limit);
            if (error)
                throw error;
            // Filter patterns that match the task type
            const relevantPatterns = (data || []).filter(pattern => {
                const conditions = pattern.conditions;
                return conditions.task_types?.includes(args.task_type) ||
                    conditions.categories?.includes(args.task_type);
            });
            return {
                success: true,
                patterns: relevantPatterns,
                total_found: relevantPatterns.length,
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error finding patterns',
            };
        }
    }
    async analyzeOutcome(args) {
        try {
            // Store the outcome as a memory
            const memoryResult = await this.storeMemory({
                content: `Action: ${args.action}\nResult: ${JSON.stringify(args.result)}`,
                type: args.success ? 'learning' : 'experience',
                context: {
                    ...args.context,
                    action: args.action,
                    result: args.result,
                    success: args.success,
                },
                importance_score: args.success ? 0.8 : 0.6,
            });
            if (!memoryResult.success)
                throw new Error(memoryResult.error);
            // Look for existing patterns
            const { data: patterns } = await this.supabase
                .from('learning_patterns')
                .select('*')
                .contains('conditions', { action_type: args.action });
            let patternId;
            if (patterns && patterns.length > 0) {
                // Update existing pattern
                const pattern = patterns[0];
                patternId = pattern.id;
                await this.updatePatternConfidence({
                    pattern_id: patternId,
                    success: args.success,
                });
            }
            else if (args.success) {
                // Create new success pattern
                const { data: newPattern, error } = await this.supabase
                    .from('learning_patterns')
                    .insert({
                    pattern_type: 'success',
                    title: `Successful ${args.action}`,
                    description: `Pattern discovered from successful ${args.action}`,
                    conditions: {
                        action_type: args.action,
                        context: args.context,
                    },
                    actions: {
                        performed: args.action,
                    },
                    outcomes: args.result,
                    confidence_score: 0.6,
                    supporting_memories: [memoryResult.memory_id],
                })
                    .select()
                    .single();
                if (error)
                    throw error;
                patternId = newPattern.id;
            }
            return {
                success: true,
                memory_id: memoryResult.memory_id,
                pattern_id: patternId,
                analysis: {
                    outcome_type: args.success ? 'success' : 'failure',
                    confidence_impact: args.success ? 'increased' : 'decreased',
                    recommendation: args.success
                        ? `Continue using this approach for ${args.action}`
                        : `Consider alternative approaches for ${args.action}`,
                },
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error analyzing outcome',
            };
        }
    }
    async updatePatternConfidence(args) {
        try {
            // Use the SQL function defined in the schema
            const { error } = await this.supabase.rpc('update_pattern_confidence', {
                pattern_id: args.pattern_id,
                was_successful: args.success,
            });
            if (error)
                throw error;
            // Get updated pattern
            const { data: pattern } = await this.supabase
                .from('learning_patterns')
                .select('*')
                .eq('id', args.pattern_id)
                .single();
            return {
                success: true,
                pattern_id: args.pattern_id,
                new_confidence: pattern?.confidence_score,
                occurrence_count: pattern?.occurrence_count,
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error updating pattern confidence',
            };
        }
    }
    async getTeamInsights(args) {
        try {
            // Get team profile
            const { data: profile } = await this.supabase
                .from('team_knowledge_profiles')
                .select('*')
                .eq('team_id', args.team_id)
                .single();
            // Get recent memories
            let memoriesQuery = this.supabase
                .from('memory_entries')
                .select('*')
                .eq('team_id', args.team_id)
                .order('created_at', { ascending: false });
            // Apply timeframe filter
            const now = new Date();
            const timeframeDays = {
                day: 1,
                week: 7,
                month: 30,
                quarter: 90,
                year: 365,
                all: null,
            };
            if (timeframeDays[args.timeframe] !== null) {
                const startDate = new Date(now.getTime() - timeframeDays[args.timeframe] * 24 * 60 * 60 * 1000);
                memoriesQuery = memoriesQuery.gte('created_at', startDate.toISOString());
            }
            const { data: memories } = await memoriesQuery;
            // Get patterns discovered by this team
            const { data: patterns } = await this.supabase
                .from('learning_patterns')
                .select('*')
                .eq('discovered_by_team', args.team_id);
            // Calculate insights
            const insights = {
                team_id: args.team_id,
                timeframe: args.timeframe,
                profile: profile || null,
                statistics: {
                    total_memories: memories?.length || 0,
                    memory_types: this.groupBy(memories || [], 'entry_type'),
                    average_importance: this.average(memories?.map(m => m.importance_score) || []),
                    most_accessed: memories?.sort((a, b) => b.accessed_count - a.accessed_count).slice(0, 5),
                },
                patterns: {
                    total_discovered: patterns?.length || 0,
                    high_confidence: patterns?.filter(p => p.confidence_score > 0.8).length || 0,
                    pattern_types: this.groupBy(patterns || [], 'pattern_type'),
                },
                recent_activity: {
                    memories_created: memories?.filter(m => {
                        const created = new Date(m.created_at);
                        const daysSince = (now.getTime() - created.getTime()) / (24 * 60 * 60 * 1000);
                        return daysSince <= 7;
                    }).length || 0,
                },
            };
            return {
                success: true,
                insights,
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error getting team insights',
            };
        }
    }
    async createCollection(args) {
        try {
            const { data, error } = await this.supabase
                .from('memory_collections')
                .insert({
                name: args.name,
                description: args.description,
                team_id: args.team_id,
                config: args.config || {},
            })
                .select()
                .single();
            if (error)
                throw error;
            return {
                success: true,
                collection: data,
                message: `Collection '${args.name}' created successfully`,
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error creating collection',
            };
        }
    }
    async pruneOldMemories(args) {
        try {
            let query = this.supabase
                .from('memory_entries')
                .select('id, created_at, importance_score, vector_id');
            const toDelete = [];
            const vectorsToDelete = [];
            // Apply retention policies
            const { data: memories } = await query;
            if (!memories) {
                return {
                    success: true,
                    deleted_count: 0,
                    message: 'No memories to prune',
                };
            }
            const now = new Date();
            memories.forEach(memory => {
                let shouldDelete = false;
                // Check days retention
                if (args.retention_policy.days) {
                    const created = new Date(memory.created_at);
                    const daysSince = (now.getTime() - created.getTime()) / (24 * 60 * 60 * 1000);
                    if (daysSince > args.retention_policy.days) {
                        shouldDelete = true;
                    }
                }
                // Check importance threshold
                if (args.retention_policy.min_importance &&
                    memory.importance_score < args.retention_policy.min_importance) {
                    shouldDelete = true;
                }
                if (shouldDelete) {
                    toDelete.push(memory.id);
                    if (memory.vector_id) {
                        vectorsToDelete.push(memory.vector_id);
                    }
                }
            });
            // Apply max count limit
            if (args.retention_policy.max_count && memories.length > args.retention_policy.max_count) {
                const sorted = memories.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
                const excess = sorted.slice(args.retention_policy.max_count);
                excess.forEach(memory => {
                    if (!toDelete.includes(memory.id)) {
                        toDelete.push(memory.id);
                        if (memory.vector_id) {
                            vectorsToDelete.push(memory.vector_id);
                        }
                    }
                });
            }
            if (args.dry_run) {
                return {
                    success: true,
                    dry_run: true,
                    would_delete: toDelete.length,
                    memories_to_delete: toDelete,
                    message: `Would delete ${toDelete.length} memories (dry run)`,
                };
            }
            // Actually delete
            if (toDelete.length > 0) {
                const { error } = await this.supabase
                    .from('memory_entries')
                    .delete()
                    .in('id', toDelete);
                if (error)
                    throw error;
                // Delete from mock Qdrant
                if (vectorsToDelete.length > 0) {
                    await this.mockQdrant.delete('default', vectorsToDelete);
                }
            }
            return {
                success: true,
                deleted_count: toDelete.length,
                message: `Deleted ${toDelete.length} memories based on retention policy`,
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error pruning memories',
            };
        }
    }
    async exportKnowledgeBase(args) {
        try {
            // Build query
            let query = this.supabase
                .from('memory_entries')
                .select('*')
                .order('created_at', { ascending: false });
            // Apply filters
            if (args.filters?.team_id) {
                query = query.eq('team_id', args.filters.team_id);
            }
            if (args.filters?.type) {
                query = query.eq('entry_type', args.filters.type);
            }
            if (args.filters?.start_date) {
                query = query.gte('created_at', args.filters.start_date);
            }
            if (args.filters?.end_date) {
                query = query.lte('created_at', args.filters.end_date);
            }
            const { data: memories, error } = await query;
            if (error)
                throw error;
            // Also get patterns
            const { data: patterns } = await this.supabase
                .from('learning_patterns')
                .select('*');
            let exportData;
            switch (args.format) {
                case 'json':
                    exportData = JSON.stringify({
                        export_date: new Date().toISOString(),
                        memories: memories || [],
                        patterns: patterns || [],
                        statistics: {
                            total_memories: memories?.length || 0,
                            total_patterns: patterns?.length || 0,
                        },
                    }, null, 2);
                    break;
                case 'csv':
                    // Simple CSV for memories
                    const headers = ['id', 'team_id', 'type', 'title', 'content', 'importance_score', 'created_at'];
                    const rows = (memories || []).map(m => headers.map(h => JSON.stringify(m[h] || '')).join(','));
                    exportData = [headers.join(','), ...rows].join('\n');
                    break;
                case 'markdown':
                    exportData = `# Knowledge Base Export

**Export Date:** ${new Date().toISOString()}

## Statistics
- Total Memories: ${memories?.length || 0}
- Total Patterns: ${patterns?.length || 0}

## Memories

${(memories || []).map(m => `### ${m.title}
- **Type:** ${m.entry_type}
- **Team:** ${m.team_id || 'Unknown'}
- **Importance:** ${m.importance_score}
- **Created:** ${m.created_at}

${m.content}

---
`).join('\n')}

## Learning Patterns

${(patterns || []).map(p => `### ${p.title}
- **Type:** ${p.pattern_type}
- **Confidence:** ${p.confidence_score}
- **Occurrences:** ${p.occurrence_count}

${p.description}

---
`).join('\n')}`;
                    break;
                default:
                    throw new Error(`Unsupported format: ${args.format}`);
            }
            return {
                success: true,
                format: args.format,
                data: exportData,
                statistics: {
                    memories_exported: memories?.length || 0,
                    patterns_exported: patterns?.length || 0,
                },
            };
        }
        catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error exporting knowledge base',
            };
        }
    }
    // Helper methods
    groupBy(array, key) {
        return array.reduce((acc, item) => {
            const value = String(item[key]);
            acc[value] = (acc[value] || 0) + 1;
            return acc;
        }, {});
    }
    average(numbers) {
        if (numbers.length === 0)
            return 0;
        return numbers.reduce((a, b) => a + b, 0) / numbers.length;
    }
}
// Create and start the server
const server = new MemoryLearningMCPServer();
server.start();
//# sourceMappingURL=server.js.map