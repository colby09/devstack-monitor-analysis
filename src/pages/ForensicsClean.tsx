import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Download, Play, RefreshCw, FileText, AlertTriangle, CheckCircle, FileSearch, BarChart3 } from 'lucide-react';

interface ForensicAnalysis {
  id: string;
  status: string;
  progress: number;
  current_step: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

interface ForensicResults {
  id: string;
  instance_id: string;
  instance_name: string;
  status: string;
  dump_info: {
    file_path: string;
    file_size: number;
    created_at: string;
    instance_id: string;
    instance_name: string;
  };
  summary: {
    total_tools_run: number;
    successful_tools: number;
    failed_tools: number;
    key_findings: string[];
    security_indicators: string[];
    credentials_found: any[];
    file_signatures: any[];
    network_artifacts: any[];
  };
  report_available: boolean;
}

interface Instance {
  id: string;
  name: string;
  status: string;
  flavor: string;
  image: string;
  ip_address?: string;
}

const ForensicsPage: React.FC = () => {
  const [instances, setInstances] = useState<Instance[]>([]);
  const [analyses, setAnalyses] = useState<ForensicAnalysis[]>([]);
  const [selectedInstance, setSelectedInstance] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [results, setResults] = useState<{[key: string]: ForensicResults}>({});

  // Fetch instances
  const fetchInstances = async () => {
    try {
      const response = await fetch('/api/instances');
      if (response.ok) {
        const data = await response.json();
        setInstances(data);
      }
    } catch (error) {
      console.error('Failed to fetch instances:', error);
    }
  };

  // Fetch analyses
  const fetchAnalyses = async () => {
    try {
      const response = await fetch('/api/integrated-forensic');
      if (response.ok) {
        const data = await response.json();
        setAnalyses(data);
        
        // Fetch results for completed analyses
        for (const analysis of data) {
          if (analysis.status === 'completed' && !results[analysis.id]) {
            fetchResults(analysis.id);
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch analyses:', error);
    }
  };

  // Fetch specific analysis results
  const fetchResults = async (analysisId: string) => {
    try {
      const response = await fetch(`/api/integrated-forensic/results/${analysisId}`);
      if (response.ok) {
        const data = await response.json();
        setResults(prev => ({...prev, [analysisId]: data}));
      }
    } catch (error) {
      console.error('Failed to fetch results:', error);
    }
  };

  // Start new analysis
  const startAnalysis = async () => {
    if (!selectedInstance) return;
    
    const instance = instances.find(i => i.id === selectedInstance);
    if (!instance) return;

    setLoading(true);
    try {
      const response = await fetch('/api/integrated-forensic/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          instance_id: instance.id,
          instance_name: instance.name,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Analysis started:', data);
        await fetchAnalyses();
        setSelectedInstance(''); // Reset selection
      } else {
        const error = await response.json();
        console.error('Failed to start analysis:', error);
      }
    } catch (error) {
      console.error('Failed to start analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  // Download report
  const downloadReport = async (analysisId: string) => {
    try {
      const response = await fetch(`/api/integrated-forensic/report/${analysisId}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `forensic_report_${analysisId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to download report:', error);
    }
  };

  // Auto-refresh analyses
  useEffect(() => {
    fetchInstances();
    fetchAnalyses();

    const interval = setInterval(() => {
      setRefreshing(true);
      fetchAnalyses().finally(() => setRefreshing(false));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      case 'pending': return 'bg-yellow-500';
      case 'dumping_memory':
      case 'analyzing':
      case 'generating_report': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'failed': return <AlertTriangle className="h-4 w-4" />;
      default: return <RefreshCw className="h-4 w-4 animate-spin" />;
    }
  };

  const formatStatus = (status: string) => {
    return status.replace('_', ' ').toUpperCase();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <FileSearch className="h-8 w-8 text-blue-600" />
            Forensic Analysis Center
          </h1>
          <p className="text-muted-foreground mt-2">
            Complete memory dump + multi-tool analysis + YARA + PDF report pipeline
          </p>
        </div>
        <Button
          onClick={() => fetchAnalyses()}
          disabled={refreshing}
          variant="outline"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Analysis Pipeline Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Analysis Pipeline
          </CardTitle>
          <CardDescription>
            Automated forensic analysis combines multiple tools for comprehensive memory analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                1
              </div>
              <div>
                <div className="font-semibold">Memory Dump</div>
                <div className="text-sm text-gray-600">virsh dump</div>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                2
              </div>
              <div>
                <div className="font-semibold">Multi-Tool Analysis</div>
                <div className="text-sm text-gray-600">Binwalk, Foremost, YARA</div>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
              <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                3
              </div>
              <div>
                <div className="font-semibold">Advanced YARA</div>
                <div className="text-sm text-gray-600">Credentials, Config</div>
              </div>
            </div>
            <div className="flex items-center space-x-3 p-3 bg-orange-50 rounded-lg">
              <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                4
              </div>
              <div>
                <div className="font-semibold">PDF Report</div>
                <div className="text-sm text-gray-600">Professional Report</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Start New Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Start New Forensic Analysis
          </CardTitle>
          <CardDescription>
            Select an instance to perform complete forensic analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2">Select Instance</label>
              <select
                value={selectedInstance}
                onChange={(e) => setSelectedInstance(e.target.value)}
                className="w-full p-2 border rounded-md"
                disabled={loading}
              >
                <option value="">Choose an instance...</option>
                {instances.map((instance) => (
                  <option key={instance.id} value={instance.id}>
                    {instance.name} ({instance.status})
                  </option>
                ))}
              </select>
            </div>
            <Button
              onClick={startAnalysis}
              disabled={!selectedInstance || loading}
              className="min-w-[120px]"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Start Analysis
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Analyses List */}
      <div className="grid gap-4">
        {analyses.map((analysis) => (
          <Card key={analysis.id} className="w-full">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {getStatusIcon(analysis.status)}
                    Analysis {analysis.id.slice(0, 8)}
                  </CardTitle>
                  <CardDescription>
                    Started: {new Date(analysis.created_at).toLocaleString()}
                    {analysis.completed_at && (
                      <> • Completed: {new Date(analysis.completed_at).toLocaleString()}</>
                    )}
                  </CardDescription>
                </div>
                <Badge className={getStatusColor(analysis.status)}>
                  {formatStatus(analysis.status)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Progress */}
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>{analysis.current_step}</span>
                    <span>{analysis.progress}%</span>
                  </div>
                  <Progress value={analysis.progress} className="w-full" />
                </div>

                {/* Error Message */}
                {analysis.error_message && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-800">{analysis.error_message}</AlertDescription>
                  </Alert>
                )}

                {/* Results for completed analyses */}
                {analysis.status === 'completed' && results[analysis.id] && (
                  <Tabs defaultValue="summary" className="w-full">
                    <TabsList>
                      <TabsTrigger value="summary">Summary</TabsTrigger>
                      <TabsTrigger value="findings">Key Findings</TabsTrigger>
                      <TabsTrigger value="security">Security</TabsTrigger>
                      <TabsTrigger value="technical">Technical</TabsTrigger>
                    </TabsList>

                    <TabsContent value="summary" className="space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <Card>
                          <CardContent className="p-4">
                            <div className="text-2xl font-bold">
                              {results[analysis.id].summary.total_tools_run}
                            </div>
                            <p className="text-sm text-muted-foreground">Tools Run</p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardContent className="p-4">
                            <div className="text-2xl font-bold text-green-600">
                              {results[analysis.id].summary.successful_tools}
                            </div>
                            <p className="text-sm text-muted-foreground">Successful</p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardContent className="p-4">
                            <div className="text-2xl font-bold">
                              {results[analysis.id].summary.credentials_found.length}
                            </div>
                            <p className="text-sm text-muted-foreground">Credentials</p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardContent className="p-4">
                            <div className="text-2xl font-bold">
                              {(results[analysis.id].dump_info.file_size / 1024 / 1024).toFixed(1)}MB
                            </div>
                            <p className="text-sm text-muted-foreground">Dump Size</p>
                          </CardContent>
                        </Card>
                      </div>
                    </TabsContent>

                    <TabsContent value="findings" className="space-y-2">
                      {results[analysis.id].summary.key_findings.map((finding, index) => (
                        <div key={index} className="p-3 bg-muted rounded-md">
                          • {finding}
                        </div>
                      ))}
                    </TabsContent>

                    <TabsContent value="security" className="space-y-2">
                      {results[analysis.id].summary.security_indicators.map((indicator, index) => (
                        <div key={index} className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                          <AlertTriangle className="h-4 w-4 inline mr-2 text-yellow-600" />
                          {indicator}
                        </div>
                      ))}
                      {results[analysis.id].summary.credentials_found.map((cred, index) => (
                        <div key={index} className="p-3 bg-red-50 border border-red-200 rounded-md">
                          <strong>Credential Found:</strong> {cred.type || 'Unknown'} - {cred.value || 'N/A'}
                        </div>
                      ))}
                    </TabsContent>

                    <TabsContent value="technical" className="space-y-2">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-semibold mb-2">Dump Information</h4>
                          <div className="text-sm space-y-1">
                            <div>File: {results[analysis.id].dump_info.file_path}</div>
                            <div>Size: {(results[analysis.id].dump_info.file_size / 1024 / 1024).toFixed(2)} MB</div>
                            <div>Instance: {results[analysis.id].dump_info.instance_name}</div>
                          </div>
                        </div>
                        <div>
                          <h4 className="font-semibold mb-2">Analysis Statistics</h4>
                          <div className="text-sm space-y-1">
                            <div>Tools Run: {results[analysis.id].summary.total_tools_run}</div>
                            <div>Successful: {results[analysis.id].summary.successful_tools}</div>
                            <div>Failed: {results[analysis.id].summary.failed_tools}</div>
                          </div>
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  {analysis.status === 'completed' && results[analysis.id]?.report_available && (
                    <Button
                      onClick={() => downloadReport(analysis.id)}
                      variant="outline"
                      size="sm"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download PDF Report
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {analyses.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Forensic Analyses</h3>
            <p className="text-muted-foreground mb-4">
              Start your first forensic analysis by selecting an instance above.
            </p>
            <p className="text-sm text-muted-foreground">
              The analysis includes: Memory dump → Multi-tool analysis → YARA → PDF report
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ForensicsPage;
