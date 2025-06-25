import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import {
  Upload,
  FileJson,
  Link,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2
} from 'lucide-react';

interface WorkflowImporterProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: (workflowId: string) => void;
}

export function WorkflowImporter({ isOpen, onClose, onImportSuccess }: WorkflowImporterProps) {
  const [importType, setImportType] = useState<'json' | 'file' | 'url'>('json');
  const [jsonContent, setJsonContent] = useState('');
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [url, setUrl] = useState('');
  const [category, setCategory] = useState('imported');
  const [ownerTeam, setOwnerTeam] = useState('default');
  const [validate, setValidate] = useState(true);
  const [process, setProcess] = useState(true);
  const [autoFix, setAutoFix] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [validationReport, setValidationReport] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // File drop handler
  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setFileName(file.name);
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setFileContent(content);
        setError(null);

        // Try to parse JSON to validate format
        try {
          JSON.parse(content);
        } catch {
          setError('Invalid JSON file. Please check the file format.');
        }
      };
      reader.readAsText(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/json': ['.json']
    },
    maxFiles: 1
  });

  const handleImport = async () => {
    setIsImporting(true);
    setError(null);
    setValidationReport(null);

    try {
      let source = '';

      // Determine source based on import type
      if (importType === 'json') {
        source = jsonContent;
        // Validate JSON
        try {
          JSON.parse(source);
        } catch (e) {
          console.error('JSON Parse Error:', e);
          console.log('Source content:', source);
          throw new Error(`Invalid JSON format: ${e.message}`);
        }
      } else if (importType === 'file') {
        if (!fileContent) {
          throw new Error('No file selected');
        }
        source = fileContent;
      } else if (importType === 'url') {
        if (!url) {
          throw new Error('No URL provided');
        }
        source = url;
      }

      // Make API call to import workflow
      const response = await fetch('/api/workflows/import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          source,
          sourceType: importType,
          ownerTeam,
          category,
          validate,
          process,
          autoFix
        })
      });

      if (!response.ok) {
        console.error('Response status:', response.status);
        console.error('Response headers:', response.headers);
        const text = await response.text();
        console.error('Response body:', text);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        // Show validation report if available
        if (result.validationReport) {
          setValidationReport(result.validationReport);
        }

        // Notify success
        setTimeout(() => {
          onImportSuccess(result.workflow.id);
          onClose();
        }, 2000);
      } else {
        setError(result.error || 'Import failed');
        if (result.validationReport) {
          setValidationReport(result.validationReport);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Import failed');
    } finally {
      setIsImporting(false);
    }
  };

  const renderValidationReport = () => {
    if (!validationReport) return null;

    const { status, errors, warnings, suggestions } = validationReport;

    return (
      <div className="space-y-4 mt-4">
        <div className="flex items-center gap-2">
          {status === 'passed' && <CheckCircle className="h-5 w-5 text-green-500" />}
          {status === 'warnings' && <AlertCircle className="h-5 w-5 text-yellow-500" />}
          {status === 'failed' && <XCircle className="h-5 w-5 text-red-500" />}
          <span className="font-semibold">
            Validation {status === 'passed' ? 'Passed' : status === 'warnings' ? 'Passed with Warnings' : 'Failed'}
          </span>
        </div>

        {errors && errors.length > 0 && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <div className="font-semibold mb-1">Errors:</div>
              <ul className="list-disc list-inside space-y-1">
                {errors.map((error: any, index: number) => (
                  <li key={index}>
                    {error.message}
                    {error.suggestion && <span className="text-sm text-muted-foreground"> - {error.suggestion}</span>}
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {warnings && warnings.length > 0 && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <div className="font-semibold mb-1">Warnings:</div>
              <ul className="list-disc list-inside space-y-1">
                {warnings.map((warning: any, index: number) => (
                  <li key={index}>
                    {warning.message}
                    {warning.suggestion && <span className="text-sm text-muted-foreground"> - {warning.suggestion}</span>}
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {suggestions && suggestions.length > 0 && (
          <div className="bg-muted p-3 rounded-md">
            <div className="font-semibold mb-1">Suggestions:</div>
            <ul className="list-disc list-inside space-y-1">
              {suggestions.map((suggestion: string, index: number) => (
                <li key={index} className="text-sm">{suggestion}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Import Workflow</DialogTitle>
          <DialogDescription>
            Import a workflow from JSON, file, or URL. The workflow will be validated and processed for compatibility.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Import Type Selection */}
          <div className="space-y-3">
            <Label>Import Source</Label>
            <RadioGroup value={importType} onValueChange={(value: any) => setImportType(value)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="json" id="json" />
                <Label htmlFor="json" className="flex items-center gap-2 cursor-pointer">
                  <FileJson className="h-4 w-4" />
                  Paste JSON
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="file" id="file" />
                <Label htmlFor="file" className="flex items-center gap-2 cursor-pointer">
                  <Upload className="h-4 w-4" />
                  Upload File
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="url" id="url" />
                <Label htmlFor="url" className="flex items-center gap-2 cursor-pointer">
                  <Link className="h-4 w-4" />
                  From URL
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Import Source Input */}
          {importType === 'json' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="json-input">Workflow JSON</Label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const demoWorkflow = {
                      name: "Demo Webhook Workflow",
                      nodes: [
                        {
                          id: "1",
                          name: "Webhook",
                          type: "n8n-nodes-base.webhook",
                          position: [250, 300],
                          parameters: {
                            path: "demo-webhook"
                          }
                        }
                      ],
                      connections: {}
                    };
                    setJsonContent(JSON.stringify(demoWorkflow, null, 2));
                    setError(null);
                  }}
                >
                  Load Demo
                </Button>
              </div>
              <Textarea
                id="json-input"
                placeholder="Paste your N8N workflow JSON here..."
                className="min-h-[200px] font-mono text-sm"
                value={jsonContent}
                onChange={(e) => setJsonContent(e.target.value)}
              />
            </div>
          )}

          {importType === 'file' && (
            <div className="space-y-2">
              <Label>Upload Workflow File</Label>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                  ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
                  ${fileName ? 'bg-muted' : ''}
                `}
              >
                <input {...getInputProps()} />
                {fileName ? (
                  <div className="flex items-center justify-center gap-2">
                    <FileJson className="h-6 w-6 text-muted-foreground" />
                    <span className="font-medium">{fileName}</span>
                  </div>
                ) : (
                  <div>
                    <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      {isDragActive ? 'Drop the file here...' : 'Drag & drop a workflow file here, or click to select'}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {importType === 'url' && (
            <div className="space-y-2">
              <Label htmlFor="url-input">Workflow URL</Label>
              <Input
                id="url-input"
                type="url"
                placeholder="https://example.com/workflow.json"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
          )}

          {/* Workflow Details */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Input
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g., automation, integration"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="owner-team">Owner Team</Label>
              <Input
                id="owner-team"
                value={ownerTeam}
                onChange={(e) => setOwnerTeam(e.target.value)}
                placeholder="e.g., marketing, sales"
              />
            </div>
          </div>

          {/* Import Options */}
          <div className="space-y-3">
            <Label>Import Options</Label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="validate"
                  checked={validate}
                  onCheckedChange={(checked) => setValidate(checked as boolean)}
                />
                <Label htmlFor="validate" className="text-sm font-normal cursor-pointer">
                  Validate workflow (check for errors and compatibility)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="process"
                  checked={process}
                  onCheckedChange={(checked) => setProcess(checked as boolean)}
                />
                <Label htmlFor="process" className="text-sm font-normal cursor-pointer">
                  Process workflow (update for compatibility with our environment)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="auto-fix"
                  checked={autoFix}
                  onCheckedChange={(checked) => setAutoFix(checked as boolean)}
                />
                <Label htmlFor="auto-fix" className="text-sm font-normal cursor-pointer">
                  Auto-fix common issues (experimental)
                </Label>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Validation Report */}
          {renderValidationReport()}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isImporting}>
            Cancel
          </Button>
          <Button onClick={handleImport} disabled={isImporting}>
            {isImporting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Importing...
              </>
            ) : (
              'Import Workflow'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
