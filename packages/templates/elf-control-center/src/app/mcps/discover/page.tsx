'use client'

import { PageTransition } from '@/components/ui/page-transition'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useState, useEffect } from 'react'
import { API_BASE_URL } from '@/lib/constants'
import { mockMCPs, mcpEnvVars } from '@/lib/mock-mcps'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, Search, Download, CheckCircle, Star,
  Shield, Package, Github, Globe, Filter, X,
  AlertCircle, ExternalLink
} from 'lucide-react'
import Link from 'next/link'

interface PublicMCP {
  name: string
  description: string
  source: string
  installType: 'npm' | 'github' | 'docker'
  installCommand: string
  capabilities: string[]
  author: string
  verified: boolean
  stars: number
  installed?: boolean
}

export default function DiscoverMCPsPage() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('') // Actual search being performed
  const [filterType, setFilterType] = useState<'all' | 'npm' | 'github' | 'docker'>('all')
  const [onlyVerified, setOnlyVerified] = useState(false)
  const [selectedMCP, setSelectedMCP] = useState<PublicMCP | null>(null)
  const [installing, setInstalling] = useState<string | null>(null)

  const [publicMCPs, setPublicMCPs] = useState<PublicMCP[]>([])
  const [loading, setLoading] = useState(true)
  const [allMCPs, setAllMCPs] = useState<PublicMCP[]>([]) // Store all MCPs
  const [displayQuery, setDisplayQuery] = useState('') // What's shown in search box
  const [apiError, setApiError] = useState(false) // Track API errors

  // Fetch MCPs from API
  const fetchMCPs = async (query?: string) => {
    try {
      setLoading(true)
      const params = query ? `?query=${encodeURIComponent(query)}` : ''
      const response = await fetch(`${API_BASE_URL}/api/mcp/discover${params}`)
      const data = await response.json()

      if (data.success) {
        setPublicMCPs(data.mcps)
        if (!query) {
          setAllMCPs(data.mcps) // Store all MCPs for client-side filtering
        }
      } else {
        console.error('Failed to fetch MCPs:', data.message)
        // Use mock data as fallback
        const mockData = [
          {
            name: 'google-sheets',
            description: 'Read and write Google Sheets',
            source: '@modelcontextprotocol/server-google-sheets',
            installType: 'npm',
            installCommand: 'npx -y @modelcontextprotocol/server-google-sheets',
            capabilities: ['read_sheet', 'write_sheet', 'create_sheet', 'update_cell'],
            author: 'Anthropic',
            verified: true,
            stars: 150,
            installed: false,
          },
          {
            name: 'slack',
            description: 'Send messages and read channels in Slack',
            source: '@modelcontextprotocol/server-slack',
            installType: 'npm',
            installCommand: 'npx -y @modelcontextprotocol/server-slack',
            capabilities: ['send_message', 'read_channel', 'list_channels', 'upload_file'],
            author: 'Anthropic',
            verified: true,
            stars: 120,
            installed: false,
          },
          {
            name: 'github',
            description: 'Interact with GitHub repositories',
            source: '@modelcontextprotocol/server-github',
            installType: 'npm',
            installCommand: 'npx -y @modelcontextprotocol/server-github',
            capabilities: ['read_repo', 'create_issue', 'list_prs', 'commit_file'],
            author: 'Anthropic',
            verified: true,
            stars: 200,
            installed: true,
          },
          {
            name: 'filesystem',
            description: 'Read and write local files with security controls',
            source: '@modelcontextprotocol/server-filesystem',
            installType: 'npm',
            installCommand: 'npx -y @modelcontextprotocol/server-filesystem',
            capabilities: ['read_file', 'write_file', 'list_directory', 'delete_file'],
            author: 'Anthropic',
            verified: true,
            stars: 180,
            installed: true,
          },
          {
            name: 'google-docs',
            description: 'Read and write Google Docs documents',
            source: '@modelcontextprotocol/server-google-docs',
            installType: 'npm',
            installCommand: 'npx -y @modelcontextprotocol/server-google-docs',
            capabilities: ['read_document', 'write_document', 'create_document', 'format_text'],
            author: 'Anthropic',
            verified: true,
            stars: 130,
            installed: false,
          },
          {
            name: 'google-drive',
            description: 'Access and manage Google Drive files',
            source: '@modelcontextprotocol/server-google-drive',
            installType: 'npm',
            installCommand: 'npx -y @modelcontextprotocol/server-google-drive',
            capabilities: ['list_files', 'upload_file', 'download_file', 'create_folder'],
            author: 'Anthropic',
            verified: true,
            stars: 110,
            installed: false,
          },
          {
            name: 'twilio',
            description: 'Send and receive SMS messages via Twilio',
            source: '@modelcontextprotocol/server-twilio',
            installType: 'npm',
            installCommand: 'npx -y @modelcontextprotocol/server-twilio',
            capabilities: ['send_sms', 'receive_sms', 'list_messages', 'send_mms'],
            author: 'Community',
            verified: false,
            stars: 85,
            installed: false,
          },
        ]

        // Use the comprehensive mock data and apply smart filtering
        handleMockData(query)
      }
    } catch (error) {
      console.error('Error fetching MCPs:', error)
      setApiError(true)
      // Set mock data on error
      const mockData = [
        {
          name: 'slack',
          description: 'Send messages and read channels in Slack',
          source: '@modelcontextprotocol/server-slack',
          installType: 'npm',
          installCommand: 'npx -y @modelcontextprotocol/server-slack',
          capabilities: ['send_message', 'read_channel', 'list_channels', 'upload_file'],
          author: 'Anthropic',
          verified: true,
          stars: 120,
          installed: false,
        },
        {
          name: 'google-docs',
          description: 'Read and write Google Docs documents',
          source: '@modelcontextprotocol/server-google-docs',
          installType: 'npm',
          installCommand: 'npx -y @modelcontextprotocol/server-google-docs',
          capabilities: ['read_document', 'write_document', 'create_document', 'format_text'],
          author: 'Anthropic',
          verified: true,
          stars: 130,
          installed: false,
        },
        {
          name: 'google-drive',
          description: 'Access and manage Google Drive files',
          source: '@modelcontextprotocol/server-google-drive',
          installType: 'npm',
          installCommand: 'npx -y @modelcontextprotocol/server-google-drive',
          capabilities: ['list_files', 'upload_file', 'download_file', 'create_folder'],
          author: 'Anthropic',
          verified: true,
          stars: 110,
          installed: false,
        },
        {
          name: 'twilio',
          description: 'Send and receive SMS messages via Twilio',
          source: '@modelcontextprotocol/server-twilio',
          installType: 'npm',
          installCommand: 'npx -y @modelcontextprotocol/server-twilio',
          capabilities: ['send_sms', 'receive_sms', 'list_messages', 'send_mms'],
          author: 'Community',
          verified: false,
          stars: 85,
          installed: false,
        },
      ]

      // Use the comprehensive mock data and apply smart filtering
      handleMockData(query)
    } finally {
      setLoading(false)
    }
  }

  // Handle mock data with smart filtering
  const handleMockData = (query?: string) => {
    console.log('Using mock data with query:', query)

    if (query) {
      // Split query into words and filter out short words
      const searchTerms = query.toLowerCase()
        .split(/\s+/)
        .filter(term => term.length > 2)

      console.log('Search terms:', searchTerms)

      // Smart search that handles natural language
      const filtered = mockMCPs.filter(mcp => {
        // Score each MCP based on matches
        let score = 0

        searchTerms.forEach(term => {
          // Exact name match (highest score)
          if (mcp.name.toLowerCase() === term) score += 10
          // Name contains term
          else if (mcp.name.toLowerCase().includes(term)) score += 5

          // Description match
          if (mcp.description.toLowerCase().includes(term)) score += 3

          // Capability match
          if (mcp.capabilities.some(cap => cap.toLowerCase().includes(term))) score += 4

          // Special handling for common terms
          if (term === 'sms' || term === 'text' || term === 'message') {
            if (mcp.name === 'twilio' || mcp.capabilities.some(c => c.includes('sms'))) score += 5
          }
          if (term === 'email' && (mcp.name === 'sendgrid' || mcp.capabilities.some(c => c.includes('email')))) score += 5
          if ((term === 'send' || term === 'receive') && mcp.capabilities.some(c => c.includes(term))) score += 2
        })

        return score > 0
      })

      console.log(`Found ${filtered.length} matches for query: "${query}"`)
      setPublicMCPs(filtered)
    } else {
      // No query - show all MCPs
      setPublicMCPs(mockMCPs)
      setAllMCPs(mockMCPs)
    }
  }

  // Initial load
  useEffect(() => {
    fetchMCPs()
  }, [])

  const filteredMCPs = publicMCPs.filter(mcp => {
    const matchesType = filterType === 'all' || mcp.installType === filterType
    const matchesVerified = !onlyVerified || mcp.verified

    return matchesType && matchesVerified
  })

  const getInstallIcon = (type: string) => {
    switch (type) {
      case 'npm': return Package
      case 'github': return Github
      case 'docker': return Globe
      default: return Package
    }
  }

  const handleInstall = async (mcp: PublicMCP) => {
    setInstalling(mcp.name)

    try {
      // Show installation instructions since the API server might not be running
      // Get environment variables from the imported config
      const requiredEnvVars = mcpEnvVars[mcp.name] || []

      const confirmed = confirm(
        `To install ${mcp.name}:\n\n` +
        `1. Run this command in your terminal:\n` +
        `   ${mcp.installCommand}\n\n` +
        `2. ${requiredEnvVars.length > 0 ? `Set these environment variables:\n   ${requiredEnvVars.join('\n   ')}\n\n` : 'No environment variables required\n\n'}` +
        `3. The MCP will provide these capabilities:\n   ${mcp.capabilities.join('\n   ')}\n\n` +
        `Click OK to mark as installed (for demo purposes).`
      )

      if (confirmed) {
        // Update both states to reflect installation
        setPublicMCPs(prev => prev.map(m =>
          m.name === mcp.name ? { ...m, installed: true } : m
        ))
        setAllMCPs(prev => prev.map(m =>
          m.name === mcp.name ? { ...m, installed: true } : m
        ))
      }
    } catch (error) {
      console.error('Install error:', error)
      alert(`Error: ${error instanceof Error ? error.message : String(error)}`)
    } finally {
      setInstalling(null)
    }
  }

  const handleSearch = async () => {
    console.log('Searching for:', displayQuery)
    // Update search query and fetch results
    setSearchQuery(displayQuery)

    // Always try to fetch, the function handles filtering internally
    await fetchMCPs(displayQuery)
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSearch()
    }
  }

  return (
    <PageTransition variant="slide">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/mcps">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold">Discover Public MCPs</h1>
              <p className="text-muted-foreground mt-1">
                Find and integrate community MCP servers
              </p>
            </div>
          </div>
        </div>

        {/* API Error Notice */}
        {apiError && (
          <Card variant="neu" className="border-yellow-500/20 bg-yellow-500/5">
            <CardContent className="flex items-center gap-3 py-4">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">Using Demo Mode</p>
                <p className="text-xs text-muted-foreground">
                  The API server is not running. Showing demo MCPs with local search.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Search and Filters */}
        <Card variant="glass">
          <CardContent className="pt-6">
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search by name, description, or capability..."
                  className="w-full pl-10 pr-4 py-2 rounded-md bg-background border"
                  value={displayQuery}
                  onChange={(e) => setDisplayQuery(e.target.value)}
                  onKeyDown={handleKeyPress}
                />
              </div>
              <Button variant="outline" onClick={handleSearch}>
                <Search className="h-4 w-4 mr-2" />
                Search
              </Button>
            </div>

            <div className="flex gap-4 mt-4">
              <div className="flex gap-2">
                {(['all', 'npm', 'github', 'docker'] as const).map((type) => (
                  <button
                    key={type}
                    onClick={() => setFilterType(type)}
                    className={`px-3 py-1 text-sm rounded-md transition-colors ${
                      filterType === type
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground hover:bg-accent'
                    }`}
                  >
                    {type === 'all' ? 'All Sources' : type.toUpperCase()}
                  </button>
                ))}
              </div>

              <label className="flex items-center gap-2 ml-auto">
                <input
                  type="checkbox"
                  className="toggle"
                  checked={onlyVerified}
                  onChange={(e) => setOnlyVerified(e.target.checked)}
                />
                <span className="text-sm">Verified only</span>
              </label>
            </div>
          </CardContent>
        </Card>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        )}

        {/* Results Grid */}
        {!loading && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredMCPs.map((mcp) => {
            const Icon = getInstallIcon(mcp.installType)
            return (
              <Card
                key={mcp.name}
                variant={mcp.installed ? 'default' : 'gradient'}
                hover="lift"
                className="cursor-pointer"
                onClick={() => setSelectedMCP(mcp)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Icon className="h-5 w-5" />
                      <CardTitle className="text-lg">{mcp.name}</CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                      {mcp.verified && (
                        <Shield className="h-4 w-4 text-green-500" title="Verified" />
                      )}
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3" />
                        <span className="text-xs">{mcp.stars}</span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-3">
                    {mcp.description}
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-muted-foreground">Author:</span>
                      <span>{mcp.author}</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {mcp.capabilities.slice(0, 3).map((cap) => (
                        <span
                          key={cap}
                          className="text-xs px-2 py-1 rounded bg-muted"
                        >
                          {cap}
                        </span>
                      ))}
                      {mcp.capabilities.length > 3 && (
                        <span className="text-xs px-2 py-1 rounded bg-muted">
                          +{mcp.capabilities.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="mt-4">
                    {mcp.installed ? (
                      <div className="flex items-center gap-2 text-green-500">
                        <CheckCircle className="h-4 w-4" />
                        <span className="text-sm">Installed</span>
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        variant="default"
                        className="w-full"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleInstall(mcp)
                        }}
                        disabled={installing === mcp.name}
                      >
                        {installing === mcp.name ? (
                          <>Installing...</>
                        ) : (
                          <>
                            <Download className="h-3 w-3 mr-1" />
                            Install
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
          </div>
        )}

        {/* Empty State */}
        {!loading && filteredMCPs.length === 0 && (
          <Card variant="neu">
            <CardContent className="text-center py-12">
              <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="font-semibold text-lg mb-2">No MCPs Found</h3>
              <p className="text-muted-foreground mb-4">
                {searchQuery
                  ? `No MCPs found matching "${searchQuery}". Try different keywords.`
                  : 'No MCPs found matching your filters.'}
              </p>
              <div className="flex gap-2 justify-center">
                <Button variant="outline" onClick={() => {
                  setSearchQuery('')
                  setDisplayQuery('')
                  setFilterType('all')
                  setOnlyVerified(false)
                  fetchMCPs() // Fetch all MCPs
                }}>
                  Clear All Filters
                </Button>
                {searchQuery && (
                  <Button variant="default" onClick={() => {
                    setSearchQuery('')
                    setDisplayQuery('')
                    fetchMCPs() // Fetch all MCPs
                  }}>
                    Show All MCPs
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Detail Modal */}
        {selectedMCP && (
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <Card className="max-w-2xl w-full max-h-[90vh] overflow-auto">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-2xl">{selectedMCP.name}</CardTitle>
                    <p className="text-muted-foreground mt-1">{selectedMCP.description}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedMCP(null)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="font-semibold mb-2">Details</h3>
                  <dl className="grid gap-2">
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Source:</dt>
                      <dd className="font-mono text-sm">{selectedMCP.source}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Author:</dt>
                      <dd>{selectedMCP.author}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Type:</dt>
                      <dd>{selectedMCP.installType.toUpperCase()}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Stars:</dt>
                      <dd className="flex items-center gap-1">
                        <Star className="h-3 w-3" />
                        {selectedMCP.stars}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Status:</dt>
                      <dd>
                        {selectedMCP.installed ? (
                          <span className="text-green-500">Installed</span>
                        ) : (
                          <span className="text-muted-foreground">Not installed</span>
                        )}
                      </dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Capabilities</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedMCP.capabilities.map((cap) => (
                      <span
                        key={cap}
                        className="px-3 py-1 rounded-full bg-primary/10 text-sm"
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Installation</h3>
                  <div className="p-3 rounded-lg bg-muted font-mono text-sm">
                    {selectedMCP.installCommand}
                  </div>
                </div>

                {selectedMCP.verified && (
                  <div className="flex items-start gap-2 p-3 rounded-lg bg-green-500/10">
                    <Shield className="h-5 w-5 text-green-500 mt-0.5" />
                    <div>
                      <p className="font-semibold text-green-500">Verified MCP</p>
                      <p className="text-sm text-muted-foreground">
                        This MCP has been reviewed and verified by the community.
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex gap-3">
                  {!selectedMCP.installed && (
                    <Button
                      variant="gradient"
                      onClick={() => handleInstall(selectedMCP)}
                      disabled={installing === selectedMCP.name}
                      className="flex-1"
                    >
                      {installing === selectedMCP.name ? (
                        <>Installing...</>
                      ) : (
                        <>
                          <Download className="h-4 w-4 mr-2" />
                          Install MCP
                        </>
                      )}
                    </Button>
                  )}
                  <Button variant="outline" asChild>
                    <a
                      href={selectedMCP.installType === 'npm'
                        ? `https://www.npmjs.com/package/${selectedMCP.source}`
                        : selectedMCP.installType === 'github'
                        ? `https://${selectedMCP.source}`
                        : '#'
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View Source
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </PageTransition>
  )
}
