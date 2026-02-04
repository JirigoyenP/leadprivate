import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle, Sparkles, Download, RefreshCw, Zap, ChevronLeft, ChevronRight,
  Upload, RotateCcw, Send
} from 'lucide-react';
import { useLeads } from '../hooks/useLeads';
import LeadFilters from '../components/LeadFilters';
import LeadsTable from '../components/LeadsTable';
import LeadDetailPanel from '../components/LeadDetailPanel';
import PipelineView from '../components/PipelineView';
import ProcessingProgress from '../components/ProcessingProgress';
import {
  bulkActionLeads,
  processLeads,
  backfillLeads,
  rescoreLeads,
  getLeadDetail,
} from '../services/api';

export default function LeadsPage() {
  const navigate = useNavigate();
  const leads = useLeads();
  const [detailLead, setDetailLead] = useState<any>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [processingBatchId, setProcessingBatchId] = useState<number | null>(null);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleRowClick = async (lead: any) => {
    try {
      const res = await getLeadDetail(lead.id);
      setDetailLead(res.data);
    } catch {
      setDetailLead(lead);
    }
  };

  const handleBulkAction = async (action: string) => {
    if (leads.selectedIds.size === 0) {
      showMessage('error', 'Select leads first');
      return;
    }
    setActionLoading(action);
    try {
      const res = await bulkActionLeads(Array.from(leads.selectedIds), action);
      showMessage('success', res.data.message);
      leads.clearSelection();
      leads.refresh();
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Action failed');
    } finally {
      setActionLoading(null);
    }
  };

  const handleProcess = async () => {
    const ids = leads.selectedIds.size > 0 ? Array.from(leads.selectedIds) : undefined;
    setActionLoading('process');
    try {
      const res = await processLeads(ids);
      showMessage('success', res.data.message);
      setProcessingBatchId(res.data.batch_id);
      leads.clearSelection();
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Process failed');
    } finally {
      setActionLoading(null);
    }
  };

  const handleBackfill = async () => {
    setActionLoading('backfill');
    try {
      const res = await backfillLeads();
      showMessage('success', `Backfill complete: ${res.data.created} created, ${res.data.updated} updated (${res.data.total_leads} total)`);
      leads.refresh();
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Backfill failed');
    } finally {
      setActionLoading(null);
    }
  };

  const handleRescore = async () => {
    setActionLoading('rescore');
    try {
      const res = await rescoreLeads();
      showMessage('success', res.data.message);
      leads.refresh();
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Rescore failed');
    } finally {
      setActionLoading(null);
    }
  };

  const handleExport = () => {
    const ids = leads.selectedIds.size > 0 ? Array.from(leads.selectedIds).join(',') : '';
    const params = new URLSearchParams();
    if (ids) params.set('lead_ids', ids);
    if (leads.source) params.set('source', leads.source);
    if (leads.verificationStatus) params.set('verification_status', leads.verificationStatus);
    if (leads.scoreMin) params.set('score_min', leads.scoreMin);
    if (leads.scoreMax) params.set('score_max', leads.scoreMax);

    const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
    window.open(`${baseUrl}/leads/export?${params.toString()}`, '_blank');
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Leads</h2>
          <p className="text-sm text-slate-500 mt-1">
            {leads.total} total leads
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleBackfill}
            disabled={actionLoading === 'backfill'}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50"
          >
            <Upload className="w-3.5 h-3.5" />
            Backfill
          </button>
          <button
            onClick={handleRescore}
            disabled={actionLoading === 'rescore'}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Rescore All
          </button>
          <button
            onClick={() => leads.refresh()}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div
          className={`px-4 py-3 rounded-lg text-sm ${
            message.type === 'success'
              ? 'bg-green-50 text-green-700 border border-green-200'
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Pipeline View */}
      <PipelineView
        onProcess={handleProcess}
        processing={actionLoading === 'process'}
      />

      {/* Filters */}
      <LeadFilters
        search={leads.search}
        onSearchChange={leads.setSearch}
        source={leads.source}
        onSourceChange={leads.setSource}
        verificationStatus={leads.verificationStatus}
        onVerificationStatusChange={leads.setVerificationStatus}
        scoreMin={leads.scoreMin}
        onScoreMinChange={leads.setScoreMin}
        scoreMax={leads.scoreMax}
        onScoreMaxChange={leads.setScoreMax}
        onClearFilters={leads.clearFilters}
      />

      {/* Bulk Actions */}
      {leads.selectedIds.size > 0 && (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-indigo-50 border border-indigo-200 rounded-lg">
          <span className="text-sm font-medium text-indigo-700">
            {leads.selectedIds.size} selected
          </span>
          <div className="h-4 w-px bg-indigo-200" />
          <button
            onClick={() => handleBulkAction('verify')}
            disabled={actionLoading === 'verify'}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100 rounded"
          >
            <CheckCircle className="w-3 h-3" /> Verify
          </button>
          <button
            onClick={() => handleBulkAction('enrich')}
            disabled={actionLoading === 'enrich'}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100 rounded"
          >
            <Sparkles className="w-3 h-3" /> Enrich
          </button>
          <button
            onClick={handleProcess}
            disabled={actionLoading === 'process'}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100 rounded"
          >
            <Zap className="w-3 h-3" /> Process
          </button>
          <button
            onClick={handleExport}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100 rounded"
          >
            <Download className="w-3 h-3" /> Export
          </button>
          <button
            onClick={() => handleBulkAction('score')}
            disabled={actionLoading === 'score'}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100 rounded"
          >
            <RefreshCw className="w-3 h-3" /> Rescore
          </button>
          <button
            onClick={() => {
              const ids = Array.from(leads.selectedIds).join(',');
              navigate(`/outreach?lead_ids=${ids}`);
            }}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100 rounded"
          >
            <Send className="w-3 h-3" /> Push to Outreach
          </button>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg border border-slate-200">
        {leads.loading ? (
          <div className="p-12 text-center">
            <div className="inline-block w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-slate-400 mt-2">Loading leads...</p>
          </div>
        ) : (
          <LeadsTable
            leads={leads.leads}
            selectedIds={leads.selectedIds}
            onToggleSelect={leads.toggleSelect}
            onToggleSelectAll={leads.toggleSelectAll}
            allSelected={leads.leads.length > 0 && leads.selectedIds.size === leads.leads.length}
            sortBy={leads.sortBy}
            sortOrder={leads.sortOrder}
            onSort={leads.setSort}
            onRowClick={handleRowClick}
          />
        )}

        {/* Pagination */}
        {leads.totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200">
            <p className="text-sm text-slate-500">
              Showing {(leads.page - 1) * leads.pageSize + 1}-{Math.min(leads.page * leads.pageSize, leads.total)} of {leads.total}
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => leads.setPage(leads.page - 1)}
                disabled={leads.page <= 1}
                className="p-1.5 text-slate-400 hover:text-slate-600 disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: Math.min(leads.totalPages, 7) }, (_, i) => {
                let pageNum: number;
                if (leads.totalPages <= 7) {
                  pageNum = i + 1;
                } else if (leads.page <= 4) {
                  pageNum = i + 1;
                } else if (leads.page >= leads.totalPages - 3) {
                  pageNum = leads.totalPages - 6 + i;
                } else {
                  pageNum = leads.page - 3 + i;
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => leads.setPage(pageNum)}
                    className={`px-3 py-1 text-sm rounded ${
                      leads.page === pageNum
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                onClick={() => leads.setPage(leads.page + 1)}
                disabled={leads.page >= leads.totalPages}
                className="p-1.5 text-slate-400 hover:text-slate-600 disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {detailLead && (
        <LeadDetailPanel lead={detailLead} onClose={() => setDetailLead(null)} />
      )}

      {/* Processing Progress Modal */}
      {processingBatchId && (
        <ProcessingProgress
          batchId={processingBatchId}
          onClose={() => {
            setProcessingBatchId(null);
            leads.refresh();
          }}
          onComplete={() => leads.refresh()}
        />
      )}
    </div>
  );
}
