import React, { useState, useEffect } from 'react';
import {
  FileText,
  UploadCloud,
  Layers,
  Database,
  Search,
  Trash2,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  Cpu,
  Zap,
  Lock,
  FileCheck,
  X
} from 'lucide-react';
import { ragAdminApi, aiAssistantApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const AdminRagDashboard = () => {
  const { user, isAdmin } = useAuth();

  const [activeTab, setActiveTab] = useState('upload'); // 'upload' | 'registry' | 'tester'
  const [documents, setDocuments] = useState([]);
  const [totalDocs, setTotalDocs] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Upload Form State
  const [uploadMode, setUploadMode] = useState('pdf'); // 'pdf' | 'text'
  const [topic, setTopic] = useState('');
  const [textContent, setTextContent] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [chunkSize, setChunkSize] = useState(500);
  const [overlap, setOverlap] = useState(100);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { success: bool, message: string, data?: any }

  // Vector Search Tester State
  const [testQuery, setTestQuery] = useState('What are the daily transfer limits?');
  const [testResults, setTestResults] = useState(null);
  const [testing, setTesting] = useState(false);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const data = await ragAdminApi.listDocuments();
      setDocuments(data.documents || []);
      setTotalDocs(data.total_documents || 0);
    } catch (e) {
      console.error('Failed to load ChromaDB documents:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  if (!isAdmin) {
    return (
      <div className="rounded-2xl bg-[#0f1117] border border-rose-500/20 p-8 text-center space-y-3">
        <ShieldAlert className="h-10 w-10 text-rose-400 mx-auto" />
        <h3 className="text-base font-semibold text-slate-100">Access Restricted</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Role-Based Access Control (RBAC) active: Your current account role (<strong>{user?.role || 'CUSTOMER'}</strong>) does not have administrator privileges to manage the RAG vector store.
        </p>
      </div>
    );
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      if (!topic) {
        // Auto-fill topic from file name without extension
        const cleanName = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
        setTopic(cleanName.charAt(0).toUpperCase() + cleanName.slice(1));
      }
    }
  };

  const handleIngest = async (e) => {
    e.preventDefault();
    setUploadStatus(null);
    setUploading(true);

    try {
      let res;
      if (uploadMode === 'pdf') {
        if (!selectedFile) {
          throw new Error('Please select a PDF or text file to upload.');
        }
        res = await ragAdminApi.uploadFile(selectedFile, topic, chunkSize, overlap);
      } else {
        if (!textContent.trim()) {
          throw new Error('Please enter text content to chunk.');
        }
        res = await ragAdminApi.uploadText(topic, textContent, chunkSize, overlap);
      }

      setUploadStatus({
        success: true,
        message: res.message,
        data: res,
      });

      // Clear form
      setSelectedFile(null);
      setTextContent('');
      setTopic('');
      await fetchDocuments();
    } catch (err) {
      setUploadStatus({
        success: false,
        message: err.response?.data?.detail || err.message || 'Ingestion failed.',
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (docId) => {
    if (!window.confirm(`Delete chunk ${docId} from ChromaDB?`)) return;
    try {
      await ragAdminApi.deleteDocument(docId);
      await fetchDocuments();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete chunk.');
    }
  };

  const handleDeleteBatch = async (batchId) => {
    if (!window.confirm(`Delete all chunks belonging to batch ${batchId}?`)) return;
    try {
      await ragAdminApi.deleteBatch(batchId);
      await fetchDocuments();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete batch.');
    }
  };

  const handleRunTestQuery = async (e) => {
    e.preventDefault();
    if (!testQuery.trim()) return;
    setTesting(true);
    setTestResults(null);
    const start = performance.now();
    try {
      const res = await aiAssistantApi.sendChat([
        { role: 'user', content: testQuery }
      ]);
      const elapsed = (performance.now() - start).toFixed(0);
      setTestResults({
        reply: res.reply,
        tools_used: res.tools_used,
        elapsed_ms: elapsed
      });
    } catch (err) {
      setTestResults({
        reply: 'Query failed: ' + (err.response?.data?.detail || err.message),
        elapsed_ms: 0
      });
    } finally {
      setTesting(false);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      doc.topic?.toLowerCase().includes(q) ||
      doc.content?.toLowerCase().includes(q) ||
      doc.id?.toLowerCase().includes(q) ||
      doc.batch_id?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      
      {/* Header telemetry banner */}
      <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-[11px] font-semibold">
                ADMIN CONSOLE
              </span>
              <span className="text-xs text-slate-500 font-mono">•</span>
              <span className="text-xs text-slate-400 font-mono">RBAC Authorization Verified</span>
            </div>
            <h2 className="text-lg font-semibold text-white">ChromaDB Vector RAG Knowledge Base</h2>
            <p className="text-xs text-slate-400 font-mono">
              In-memory zero-storage document parsing • Parallel atomic chunking • Real-time vector search
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="px-3 py-2 rounded-xl bg-black/40 border border-white/[0.06] text-right">
              <div className="text-[10px] text-slate-500 uppercase font-mono">Total Chunks</div>
              <div className="text-base font-semibold text-emerald-400 font-mono">{totalDocs}</div>
            </div>
            <button
              onClick={fetchDocuments}
              className="p-2.5 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-slate-300 hover:text-white transition-colors cursor-pointer"
              title="Refresh Registry"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center space-x-2 mt-6 pt-4 border-t border-white/[0.06] text-xs overflow-x-auto pb-1 no-scrollbar">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors cursor-pointer flex items-center space-x-1.5 whitespace-nowrap ${
              activeTab === 'upload'
                ? 'bg-white text-slate-950 font-semibold'
                : 'bg-white/[0.04] text-slate-400 hover:text-slate-200 border border-white/[0.06]'
            }`}
          >
            <UploadCloud className="h-3.5 w-3.5" />
            <span>Ingest Document</span>
          </button>

          <button
            onClick={() => setActiveTab('registry')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors cursor-pointer flex items-center space-x-1.5 whitespace-nowrap ${
              activeTab === 'registry'
                ? 'bg-white text-slate-950 font-semibold'
                : 'bg-white/[0.04] text-slate-400 hover:text-slate-200 border border-white/[0.06]'
            }`}
          >
            <Database className="h-3.5 w-3.5" />
            <span>Vector Registry ({totalDocs})</span>
          </button>

          <button
            onClick={() => setActiveTab('tester')}
            className={`px-3.5 py-1.5 rounded-lg font-medium transition-colors cursor-pointer flex items-center space-x-1.5 whitespace-nowrap ${
              activeTab === 'tester'
                ? 'bg-white text-slate-950 font-semibold'
                : 'bg-white/[0.04] text-slate-400 hover:text-slate-200 border border-white/[0.06]'
            }`}
          >
            <Zap className="h-3.5 w-3.5" />
            <span>Semantic Tester</span>
          </button>
        </div>
      </div>

      {/* TAB 1: INGEST NEW DOCUMENT */}
      {activeTab === 'upload' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Main Ingest Form */}
          <div className="lg:col-span-8 rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 shadow-lg space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
              <div>
                <h3 className="text-sm font-semibold text-white">Document Ingestion Pipeline</h3>
                <p className="text-[11px] text-slate-500 font-mono">Parallel chunking & transactional commit</p>
              </div>

              {/* Ingestion Mode Toggle */}
              <div className="flex items-center space-x-1 p-1 rounded-lg bg-black/40 border border-white/[0.06] text-xs">
                <button
                  type="button"
                  onClick={() => setUploadMode('pdf')}
                  className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                    uploadMode === 'pdf' ? 'bg-emerald-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  In-Memory PDF Stream
                </button>
                <button
                  type="button"
                  onClick={() => setUploadMode('text')}
                  className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                    uploadMode === 'text' ? 'bg-emerald-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Raw Markdown / Text
                </button>
              </div>
            </div>

            {uploadStatus && (
              <div
                className={`p-3.5 rounded-xl border text-xs flex items-start space-x-2.5 ${
                  uploadStatus.success
                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                    : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                }`}
              >
                {uploadStatus.success ? (
                  <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
                ) : (
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                )}
                <div className="space-y-1 flex-1">
                  <div className="font-semibold">{uploadStatus.message}</div>
                  {uploadStatus.data && (
                    <div className="font-mono text-[10px] text-emerald-400/80">
                      Batch ID: {uploadStatus.data.batch_id} • Chunks: {uploadStatus.data.total_chunks} • Chars: {uploadStatus.data.char_count}
                    </div>
                  )}
                </div>
                <button onClick={() => setUploadStatus(null)} className="text-slate-400 hover:text-slate-200">
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            )}

            <form onSubmit={handleIngest} className="space-y-4">
              {/* Topic Header */}
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">
                  Document Topic / Knowledge Title
                </label>
                <input
                  type="text"
                  required
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g. Foreign Exchange Remittance Policies, Loan Underwriting Criteria"
                  className="w-full px-3 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/60"
                />
              </div>

              {/* Mode: PDF / File Ingest */}
              {uploadMode === 'pdf' ? (
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">
                    Upload PDF / Document (In-Memory Processing)
                  </label>
                  <div className="p-6 border-2 border-dashed border-white/[0.1] rounded-xl text-center bg-black/20 hover:border-emerald-500/40 transition-colors">
                    <input
                      type="file"
                      id="rag-file-input"
                      accept=".pdf,.txt,.md"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                    <label htmlFor="rag-file-input" className="cursor-pointer space-y-2 block">
                      <FileText className="h-8 w-8 text-emerald-400 mx-auto" />
                      <div className="text-xs text-slate-300 font-medium">
                        {selectedFile ? (
                          <span className="text-emerald-400 font-mono">{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                        ) : (
                          <span>Click to browse or drop PDF / text files here</span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        Zero disk storage • In-memory byte-stream parser
                      </div>
                    </label>
                  </div>
                </div>
              ) : (
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">
                    Raw Knowledge Text / Policy Content
                  </label>
                  <textarea
                    rows={8}
                    required
                    value={textContent}
                    onChange={(e) => setTextContent(e.target.value)}
                    placeholder="Paste bank terms, interest disclosures, FAQ Q&As, or compliance documentation..."
                    className="w-full p-3 bg-black/40 border border-white/[0.08] rounded-lg text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/60 font-mono leading-relaxed"
                  />
                </div>
              )}

              {/* Chunking Sliders */}
              <div className="grid grid-cols-2 gap-4 p-3.5 rounded-xl bg-black/40 border border-white/[0.06]">
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Chunk Character Size</span>
                    <span className="font-mono text-emerald-400">{chunkSize} chars</span>
                  </div>
                  <input
                    type="range"
                    min="200"
                    max="1500"
                    step="50"
                    value={chunkSize}
                    onChange={(e) => setChunkSize(parseInt(e.target.value))}
                    className="w-full accent-emerald-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Sliding Window Overlap</span>
                    <span className="font-mono text-emerald-400">{overlap} chars</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="300"
                    step="25"
                    value={overlap}
                    onChange={(e) => setOverlap(parseInt(e.target.value))}
                    className="w-full accent-emerald-500"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs transition-all flex items-center space-x-2 shadow-md disabled:opacity-50 cursor-pointer"
                >
                  <Cpu className={`h-4 w-4 ${uploading ? 'animate-spin' : ''}`} />
                  <span>{uploading ? 'Chunking & Ingesting in Parallel...' : 'Execute Parallel Atomic Ingestion'}</span>
                </button>
              </div>
            </form>
          </div>

          {/* Architecture Details Column */}
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-5 shadow-lg space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
                <Lock className="h-4 w-4 text-emerald-400" />
                <span>Zero File Storage Guarantee</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                PDFs uploaded through this portal are parsed strictly in RAM byte-streams via <code className="text-slate-300">pypdf</code>. No file is ever created or written to the host filesystem.
              </p>
            </div>

            <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-5 shadow-lg space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
                <Zap className="h-4 w-4 text-emerald-400" />
                <span>All-or-Nothing Atomic Guarantee</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Embedding and vector insertion are distributed across worker threads. If <strong>any single chunk fails</strong> (e.g. ChromaDB timeout), an immediate transaction rollback deletes all partial chunks, ensuring zero data corruption.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: VECTOR REGISTRY TABLE */}
      {activeTab === 'registry' && (
        <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 shadow-lg space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/[0.06]">
            <div>
              <h3 className="text-sm font-semibold text-white">ChromaDB Chunk Registry</h3>
              <p className="text-[11px] text-slate-500 font-mono">List of indexed embedding vectors</p>
            </div>

            <div className="relative">
              <Search className="h-3.5 w-3.5 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter by topic, batch ID, text..."
                className="pl-8 pr-3 py-1.5 bg-black/40 border border-white/[0.08] rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/60 w-64"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-white/[0.06] text-slate-400 uppercase font-mono text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Topic</th>
                  <th className="py-2.5 px-3">Chunk ID / Batch</th>
                  <th className="py-2.5 px-3">Content Snippet</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {loading ? (
                  <tr>
                    <td colSpan="4" className="py-12 text-center text-slate-500 font-mono">
                      Querying ChromaDB vector registry...
                    </td>
                  </tr>
                ) : filteredDocs.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="py-12 text-center text-slate-500">
                      No vector chunks match your search query.
                    </td>
                  </tr>
                ) : (
                  filteredDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-3 font-medium text-slate-200 whitespace-nowrap">
                        {doc.topic || 'General Policy'}
                      </td>
                      <td className="py-3 px-3 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                        <div>{doc.id}</div>
                        {doc.batch_id && (
                          <div className="text-[10px] text-slate-600 flex items-center space-x-1">
                            <span>batch: {doc.batch_id}</span>
                            <button
                              onClick={() => handleDeleteBatch(doc.batch_id)}
                              className="text-rose-400/70 hover:text-rose-400 text-[10px] ml-1 cursor-pointer"
                              title="Delete entire batch"
                            >
                              [del batch]
                            </button>
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-3 text-slate-300 max-w-md line-clamp-2 text-[11px] leading-relaxed">
                        {doc.content}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => handleDeleteDoc(doc.id)}
                          className="p-1.5 rounded-lg bg-white/[0.04] hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-white/[0.06] transition-colors cursor-pointer"
                          title="Delete chunk from ChromaDB"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: SEMANTIC TESTER */}
      {activeTab === 'tester' && (
        <div className="rounded-2xl bg-[#0f1117] border border-white/[0.08] p-6 shadow-lg space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Live Semantic Vector Search Tester</h3>
            <p className="text-[11px] text-slate-500 font-mono">Test ChromaDB similarity query retrieval against Nova AI</p>
          </div>

          <form onSubmit={handleRunTestQuery} className="flex gap-2">
            <input
              type="text"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              placeholder="Type a policy or banking inquiry to test semantic retrieval..."
              className="flex-1 px-3.5 py-2 bg-black/40 border border-white/[0.08] rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500/60"
            />
            <button
              type="submit"
              disabled={testing || !testQuery.trim()}
              className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs flex items-center space-x-1.5 transition-all disabled:opacity-50 cursor-pointer"
            >
              <Zap className={`h-3.5 w-3.5 ${testing ? 'animate-spin' : ''}`} />
              <span>{testing ? 'Querying...' : 'Run Query'}</span>
            </button>
          </form>

          {testResults && (
            <div className="mt-4 p-4 rounded-xl bg-black/40 border border-white/[0.06] space-y-2 text-xs">
              <div className="flex items-center justify-between text-slate-400 font-mono text-[10px] pb-2 border-b border-white/[0.04]">
                <span>Response Time: <strong className="text-emerald-400">{testResults.elapsed_ms} ms</strong></span>
                {testResults.tools_used && testResults.tools_used.length > 0 && (
                  <span>Invoked Tools: <strong className="text-slate-200">{testResults.tools_used.join(', ')}</strong></span>
                )}
              </div>
              <div className="text-slate-200 whitespace-pre-wrap leading-relaxed">
                {testResults.reply}
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
