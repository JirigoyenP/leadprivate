import { useEffect, useState } from 'react';
import { Send, Link2, Unlink, RefreshCw, Download, CheckCircle, Loader2 } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import {
  connectInstantly,
  getOutreachStatus,
  disconnectInstantly,
  getOutreachCampaigns,
  pushLeadsToOutreach,
  getOutreachLogs,
  exportForOutreach,
} from '../services/api';
import { useSearchParams } from 'react-router-dom';

interface Campaign {
  id: string;
  name: string;
  status: string;
}

interface OutreachLog {
  id: number;
  lead_id: number;
  campaign_id: string;
  campaign_name?: string;
  status: string;
  variables_sent?: Record<string, string>;
  created_at?: string;
}

export default function OutreachPage() {
  const [searchParams] = useSearchParams();
  const [connected, setConnected] = useState(false);
  const [connectionLoading, setConnectionLoading] = useState(true);
  const [apiKey, setApiKey] = useState('');
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<string>('');
  const [logs, setLogs] = useState<OutreachLog[]>([]);
  const [logsTotal, setLogsTotal] = useState(0);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  // Get lead IDs from URL params (from LeadsPage "Push to Outreach" action)
  const leadIdsParam = searchParams.get('lead_ids');
  const leadIds = leadIdsParam ? leadIdsParam.split(',').map(Number) : [];

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  useEffect(() => {
    checkConnection();
    fetchLogs();
  }, []);

  const checkConnection = async () => {
    setConnectionLoading(true);
    try {
      const res = await getOutreachStatus();
      setConnected(res.data.connected);
      if (res.data.connected) {
        fetchCampaigns();
      }
    } catch {
      setConnected(false);
    } finally {
      setConnectionLoading(false);
    }
  };

  const handleConnect = async () => {
    if (!apiKey.trim()) return;
    setLoading('connect');
    try {
      const res = await connectInstantly(apiKey);
      if (res.data.connected) {
        setConnected(true);
        setApiKey('');
        showMessage('success', 'Connected to Instantly.ai');
        fetchCampaigns();
      } else {
        showMessage('error', res.data.error || 'Connection failed');
      }
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Connection failed');
    } finally {
      setLoading(null);
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectInstantly();
      setConnected(false);
      setCampaigns([]);
      showMessage('success', 'Disconnected from Instantly.ai');
    } catch {
      showMessage('error', 'Failed to disconnect');
    }
  };

  const fetchCampaigns = async () => {
    setLoading('campaigns');
    try {
      const res = await getOutreachCampaigns();
      setCampaigns(res.data.campaigns || []);
    } catch (err: any) {
      showMessage('error', 'Failed to load campaigns');
    } finally {
      setLoading(null);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await getOutreachLogs();
      setLogs(res.data.logs || []);
      setLogsTotal(res.data.total || 0);
    } catch {
      // Ignore
    }
  };

  const handlePush = async () => {
    if (!selectedCampaign || leadIds.length === 0) {
      showMessage('error', 'Select a campaign and ensure leads are selected');
      return;
    }
    const campaign = campaigns.find((c) => c.id === selectedCampaign);
    setLoading('push');
    try {
      const res = await pushLeadsToOutreach(leadIds, selectedCampaign, campaign?.name);
      showMessage('success', res.data.message);
      fetchLogs();
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Push failed');
    } finally {
      setLoading(null);
    }
  };

  const handleExport = async (format: string) => {
    setLoading('export');
    try {
      const res = await exportForOutreach(format, leadIds.length > 0 ? leadIds : undefined);
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `leads_${format}_export.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      showMessage('success', `Exported as ${format} format`);
    } catch {
      showMessage('error', 'Export failed');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Outreach</h2>
        <p className="text-sm text-slate-500 mt-1">Push leads to Instantly.ai campaigns or export for other tools</p>
      </div>

      {/* Message */}
      {message && (
        <div className={`px-4 py-3 rounded-lg text-sm ${
          message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message.text}
        </div>
      )}

      {/* Connection Section */}
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="text-sm font-semibold text-slate-900 mb-4">Instantly.ai Connection</h3>

        {connectionLoading ? (
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Loader2 className="w-4 h-4 animate-spin" /> Checking connection...
          </div>
        ) : connected ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-sm font-medium text-green-700">Connected to Instantly.ai</span>
            </div>
            <button
              onClick={handleDisconnect}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
            >
              <Unlink className="w-3.5 h-3.5" /> Disconnect
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your Instantly.ai API key"
              className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={handleConnect}
              disabled={!apiKey.trim() || loading === 'connect'}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading === 'connect' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Link2 className="w-3.5 h-3.5" />
              )}
              Connect
            </button>
          </div>
        )}
      </div>

      {/* Campaign Selection + Push */}
      {connected && (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-900">Push to Campaign</h3>
            <button
              onClick={fetchCampaigns}
              disabled={loading === 'campaigns'}
              className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
            >
              <RefreshCw className={`w-3 h-3 ${loading === 'campaigns' ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {leadIds.length > 0 && (
            <div className="mb-4 px-3 py-2 bg-indigo-50 border border-indigo-200 rounded-lg text-sm text-indigo-700">
              {leadIds.length} leads selected for push
            </div>
          )}

          <div className="flex items-center gap-3">
            <select
              value={selectedCampaign}
              onChange={(e) => setSelectedCampaign(e.target.value)}
              className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
            >
              <option value="">Select a campaign</option>
              {campaigns.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name || c.id} {c.status ? `(${c.status})` : ''}
                </option>
              ))}
            </select>
            <button
              onClick={handlePush}
              disabled={!selectedCampaign || leadIds.length === 0 || loading === 'push'}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading === 'push' ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
              Push Leads
            </button>
          </div>

          {leadIds.length === 0 && (
            <p className="mt-2 text-xs text-slate-400">
              Select leads from the Leads page using "Push to Outreach" to push them here.
            </p>
          )}
        </div>
      )}

      {/* Smart Export */}
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="text-sm font-semibold text-slate-900 mb-4">Smart CSV Export</h3>
        <p className="text-sm text-slate-500 mb-4">Export leads in formats optimized for popular outreach tools.</p>
        <div className="flex items-center gap-3">
          {[
            { format: 'instantly', label: 'Instantly Format' },
            { format: 'lemlist', label: 'Lemlist Format' },
            { format: 'general', label: 'General CSV' },
          ].map(({ format, label }) => (
            <button
              key={format}
              onClick={() => handleExport(format)}
              disabled={loading === 'export'}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Outreach History */}
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="px-6 py-4 border-b border-slate-200">
          <h3 className="text-sm font-semibold text-slate-900">Outreach History ({logsTotal})</h3>
        </div>
        {logs.length === 0 ? (
          <div className="px-6 py-12 text-center text-sm text-slate-400">
            No outreach activity yet
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 text-left">
                  <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Lead ID</th>
                  <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Campaign</th>
                  <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 text-sm text-slate-700">#{log.lead_id}</td>
                    <td className="px-4 py-3 text-sm text-slate-700">{log.campaign_name || log.campaign_id}</td>
                    <td className="px-4 py-3"><StatusBadge status={log.status} /></td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {log.created_at ? new Date(log.created_at).toLocaleString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
