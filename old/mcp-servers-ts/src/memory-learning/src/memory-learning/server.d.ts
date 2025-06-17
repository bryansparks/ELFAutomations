import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { BaseMCPServer } from '../shared/base-server.js';
export declare class MemoryLearningMCPServer extends BaseMCPServer {
    private supabase;
    private mockQdrant;
    private embeddingCache;
    constructor();
    private createMockQdrantClient;
    private generateMockEmbedding;
    getTools(): Tool[];
    handleToolCall(name: string, args: any): Promise<any>;
    private storeMemory;
    private retrieveMemories;
    private getSimilarExperiences;
    private findSuccessfulPatterns;
    private analyzeOutcome;
    private updatePatternConfidence;
    private getTeamInsights;
    private createCollection;
    private pruneOldMemories;
    private exportKnowledgeBase;
    private groupBy;
    private average;
}
//# sourceMappingURL=server.d.ts.map