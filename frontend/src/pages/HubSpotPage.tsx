import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Link2, Link2Off, RefreshCw, Play, Upload, Trash2 } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import {
  getHubSpotStatus,
  getHubSpotAuthUrl,
  disconnectHubSpot,
  getHubSpotContacts,
  verifyHubSpotContacts,
  syncHubSpotResults,
  getBatchStatus,
  deleteHubSpotContacts,
  verifyAndEnrichHubSpotContacts,
  syncHubSpotEnrichment,
  HubSpotContact,
} from '../services/api';

export default function HubSpotPage() {
  const [searchParams] = useSearchParams();
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [contacts, setContacts] = useState<HubSpotContact[]>([]);
  const [selectedContacts, setSelectedContacts] = useState<Set<string>>(new Set());
  const [verifying, setVerifying] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | undefined>();
  const [loadingMore, setLoadingMore] = useState(false);
  const [currentBatchId, setCurrentBatchId] = useState<number | null>(null);
  const [message, setMessage] = useState('');
  const [batchProgress, setBatchProgress] = useState<{ processed: number; total: number } | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [currentPhase, setCurrentPhase] = useState<'verification' | 'enrichment' | null>(null);

  useEffect(() => {
    checkStatus();
    if (searchParams.get('connected') === 'true') {
      setMessage('Successfully connected to HubSpot!');
    }
  }, [searchParams]);

  const checkStatus = async () => {
    setLoading(true);
    try {
      const response = await getHubSpotStatus();
      setConnected(response.data.connected);
      if (response.data.connected) {
        await fetchContacts();
      }
    } catch (err) {
      console.error('Failed to check status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const response = await getHubSpotAuthUrl();
      window.location.href = response.data.auth_url;
    } catch (err) {
      console.error('Failed to get auth URL:', err);
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectHubSpot();
      setConnected(false);
      setContacts([]);
    } catch (err) {
      console.error('Failed to disconnect:', err);
    }
  };

  const fetchContacts = async (cursor?: string) => {
    try {
      if (cursor) {
        setLoadingMore(true);
      }
      const response = await getHubSpotContacts({ limit: 100, after: cursor });
      if (cursor) {
        setContacts(prev => [...prev, ...response.data.contacts]);
      } else {
        setContacts(response.data.contacts);
      }
      setHasMore(response.data.has_more);
      setNextCursor(response.data.next_cursor);
    } catch (err) {
      console.error('Failed to fetch contacts:', err);
    } finally {
      setLoadingMore(false);
    }
  };

  const loadMore = () => {
    if (nextCursor && !loadingMore) {
      fetchContacts(nextCursor);
    }
  };

  const handleSelectAll = () => {
    if (selectedContacts.size === contacts.length) {
      setSelectedContacts(new Set());
    } else {
      setSelectedContacts(new Set(contacts.map((c) => c.id)));
    }
  };

  const handleSelectContact = (id: string) => {
    const newSelected = new Set(selectedContacts);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedContacts(newSelected);
  };

  const pollBatchStatus = async (batchId: number) => {
    try {
      const response = await getBatchStatus(batchId);
      const batch = response.data;

      setBatchProgress({ processed: batch.processed_emails, total: batch.total_emails });

      if (batch.status === 'completed') {
        setMessage(`Verification completed! ${batch.valid_count} valid, ${batch.invalid_count} invalid, ${batch.unknown_count} unknown. Click "Sync to HubSpot" to update contacts.`);
        setBatchProgress(null);
        setVerifying(false);
      } else if (batch.status === 'failed') {
        setMessage(`Verification failed: ${batch.error_message || 'Unknown error'}`);
        setBatchProgress(null);
        setVerifying(false);
      } else {
        // Still processing, poll again
        setMessage(`Verifying... ${batch.processed_emails}/${batch.total_emails} emails processed`);
        setTimeout(() => pollBatchStatus(batchId), 2000);
      }
    } catch (err) {
      console.error('Failed to poll batch status:', err);
      setBatchProgress(null);
      setVerifying(false);
    }
  };

  const handleVerifySelected = async () => {
    if (selectedContacts.size === 0) {
      setMessage('Please select contacts first');
      return;
    }

    setVerifying(true);
    setMessage('Starting verification...');

    try {
      // Build contacts array with id and email from selected contacts
      const contactsToVerify = contacts
        .filter(c => selectedContacts.has(c.id))
        .map(c => ({ id: c.id, email: c.email }));
      console.log('Verifying contacts:', contactsToVerify);
      const response = await verifyHubSpotContacts(contactsToVerify);
      setCurrentBatchId(response.data.batch_id);
      setMessage(`Verification started for ${response.data.contacts_queued} contacts...`);
      // Start polling for status
      setTimeout(() => pollBatchStatus(response.data.batch_id), 1000);
    } catch (err: unknown) {
      console.error('Failed to verify:', err);
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setMessage(error.response?.data?.detail || error.message || 'Failed to start verification');
      setVerifying(false);
    }
  };

  const handleVerifyAll = async () => {
    setVerifying(true);
    setMessage('Fetching unverified contacts from HubSpot...');

    try {
      const response = await verifyHubSpotContacts();
      if (response.data.batch_id === 0) {
        setMessage('No unverified contacts found');
        setVerifying(false);
        return;
      }
      setCurrentBatchId(response.data.batch_id);
      setMessage(`Verification started for ${response.data.contacts_queued} contacts...`);
      // Start polling for status
      setTimeout(() => pollBatchStatus(response.data.batch_id), 1000);
    } catch (err) {
      console.error('Failed to verify:', err);
      setMessage('Failed to start verification');
      setVerifying(false);
    }
  };

  const handleSyncResults = async () => {
    if (!currentBatchId) return;

    setSyncing(true);
    setMessage('Syncing results to HubSpot...');

    try {
      const response = await syncHubSpotResults(currentBatchId);
      setMessage(`Done! Synced ${response.data.contacts_updated} contacts to HubSpot`);
      setSelectedContacts(new Set());
      setCurrentBatchId(null);
      await fetchContacts();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setMessage(`Sync failed: ${error.response?.data?.detail || 'Unknown error'}`);
    } finally {
      setSyncing(false);
    }
  };

  const pollEnrichBatchStatus = async (batchId: number) => {
    try {
      const response = await getBatchStatus(batchId);
      const batch = response.data;

      setBatchProgress({ processed: batch.processed_emails, total: batch.total_emails });

      if (batch.status === 'completed') {
        setMessage(`Verify & Enrich completed! ${batch.valid_count} valid emails enriched. Click "Sync Enrichment" to update HubSpot.`);
        setBatchProgress(null);
        setEnriching(false);
        setCurrentPhase(null);
      } else if (batch.status === 'failed') {
        setMessage(`Process failed: ${batch.error_message || 'Unknown error'}`);
        setBatchProgress(null);
        setEnriching(false);
        setCurrentPhase(null);
      } else if (batch.status === 'enriching') {
        setCurrentPhase('enrichment');
        setMessage(`Enriching with Apollo... ${batch.processed_emails}/${batch.total_emails}`);
        setTimeout(() => pollEnrichBatchStatus(batchId), 2000);
      } else {
        // Still verifying
        setCurrentPhase('verification');
        setMessage(`Verifying emails... ${batch.processed_emails}/${batch.total_emails}`);
        setTimeout(() => pollEnrichBatchStatus(batchId), 2000);
      }
    } catch (err) {
      console.error('Failed to poll batch status:', err);
      setBatchProgress(null);
      setEnriching(false);
      setCurrentPhase(null);
    }
  };

  const handleVerifyAndEnrichSelected = async () => {
    if (selectedContacts.size === 0) {
      setMessage('Please select contacts first');
      return;
    }

    setEnriching(true);
    setCurrentPhase('verification');
    setMessage('Starting verification & enrichment...');

    try {
      const contactsToProcess = contacts
        .filter(c => selectedContacts.has(c.id))
        .map(c => ({ id: c.id, email: c.email }));

      const response = await verifyAndEnrichHubSpotContacts(contactsToProcess);
      setCurrentBatchId(response.data.batch_id);
      setMessage(`Processing ${response.data.contacts_queued} contacts (verify + enrich)...`);
      setTimeout(() => pollEnrichBatchStatus(response.data.batch_id), 1000);
    } catch (err: unknown) {
      console.error('Failed to verify and enrich:', err);
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setMessage(error.response?.data?.detail || error.message || 'Failed to start process');
      setEnriching(false);
      setCurrentPhase(null);
    }
  };

  const handleVerifyAndEnrichAll = async () => {
    setEnriching(true);
    setCurrentPhase('verification');
    setMessage('Fetching unverified contacts from HubSpot...');

    try {
      const response = await verifyAndEnrichHubSpotContacts();
      if (response.data.batch_id === 0) {
        setMessage('No unverified contacts found');
        setEnriching(false);
        setCurrentPhase(null);
        return;
      }
      setCurrentBatchId(response.data.batch_id);
      setMessage(`Processing ${response.data.contacts_queued} contacts (verify + enrich)...`);
      setTimeout(() => pollEnrichBatchStatus(response.data.batch_id), 1000);
    } catch (err) {
      console.error('Failed to verify and enrich:', err);
      setMessage('Failed to start process');
      setEnriching(false);
      setCurrentPhase(null);
    }
  };

  const handleSyncEnrichment = async () => {
    if (!currentBatchId) return;

    setSyncing(true);
    setMessage('Syncing verification results to HubSpot...');

    try {
      // First sync verification results
      await syncHubSpotResults(currentBatchId);

      setMessage('Syncing enrichment data to HubSpot...');
      // Then sync enrichment data
      const enrichResponse = await syncHubSpotEnrichment(currentBatchId);

      setMessage(`Done! Updated ${enrichResponse.data.contacts_updated} contacts with enrichment data`);
      setSelectedContacts(new Set());
      setCurrentBatchId(null);
      await fetchContacts();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setMessage(`Sync failed: ${error.response?.data?.detail || 'Unknown error'}`);
    } finally {
      setSyncing(false);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedContacts.size === 0) {
      setMessage('Please select contacts first');
      return;
    }

    const confirmDelete = window.confirm(
      `Are you sure you want to permanently delete ${selectedContacts.size} contact(s) from HubSpot? This cannot be undone.`
    );

    if (!confirmDelete) return;

    setDeleting(true);
    setMessage(`Deleting ${selectedContacts.size} contacts...`);

    try {
      const contactIds = Array.from(selectedContacts);
      const response = await deleteHubSpotContacts(contactIds);

      if (response.data.failed_count > 0) {
        setMessage(`Deleted ${response.data.deleted_count} contacts. ${response.data.failed_count} failed.`);
      } else {
        setMessage(`Successfully deleted ${response.data.deleted_count} contacts from HubSpot`);
      }

      setSelectedContacts(new Set());
      await fetchContacts();
    } catch (err: unknown) {
      console.error('Failed to delete:', err);
      const error = err as { response?: { data?: { detail?: string } } };
      setMessage(`Delete failed: ${error.response?.data?.detail || 'Unknown error'}`);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">HubSpot Integration</h2>
        <p className="mt-1 text-sm text-gray-600">
          Connect to HubSpot to verify and sync contact emails
        </p>
      </div>

      {message && (
        <div className={`p-4 rounded-md ${deleting ? 'bg-red-50 border border-red-200' : enriching ? 'bg-purple-50 border border-purple-200' : verifying || syncing ? 'bg-yellow-50 border border-yellow-200' : 'bg-indigo-50 border border-indigo-200'}`}>
          <div className="flex items-center gap-2">
            {(verifying || syncing || deleting || enriching) && <RefreshCw className={`h-4 w-4 animate-spin ${deleting ? 'text-red-600' : enriching ? 'text-purple-600' : 'text-yellow-600'}`} />}
            <p className={`text-sm ${deleting ? 'text-red-700' : enriching ? 'text-purple-700' : verifying || syncing ? 'text-yellow-700' : 'text-indigo-700'}`}>{message}</p>
          </div>
          {batchProgress && (
            <div className="mt-2">
              {currentPhase && (
                <div className="flex gap-2 mb-1 text-xs">
                  <span className={`${currentPhase === 'verification' ? 'text-purple-700 font-medium' : 'text-gray-400'}`}>1. Verification</span>
                  <span className="text-gray-400">→</span>
                  <span className={`${currentPhase === 'enrichment' ? 'text-purple-700 font-medium' : 'text-gray-400'}`}>2. Enrichment</span>
                </div>
              )}
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${enriching ? 'bg-purple-600' : 'bg-indigo-600'}`}
                  style={{ width: `${(batchProgress.processed / batchProgress.total) * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {connected ? (
              <>
                <div className="h-3 w-3 bg-green-500 rounded-full" />
                <span className="text-sm font-medium text-gray-900">Connected to HubSpot</span>
              </>
            ) : (
              <>
                <div className="h-3 w-3 bg-gray-300 rounded-full" />
                <span className="text-sm font-medium text-gray-600">Not connected</span>
              </>
            )}
          </div>

          {connected ? (
            <button
              onClick={handleDisconnect}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <Link2Off className="h-4 w-4 mr-2" />
              Disconnect
            </button>
          ) : (
            <button
              onClick={handleConnect}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-orange-500 hover:bg-orange-600"
            >
              <Link2 className="h-4 w-4 mr-2" />
              Connect HubSpot
            </button>
          )}
        </div>
      </div>

      {connected && (
        <>
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Actions</h3>

            {/* Verify & Enrich Section - Primary workflow */}
            <div className="mb-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <h4 className="text-sm font-medium text-purple-900 mb-2">Verify & Enrich (Recommended)</h4>
              <p className="text-xs text-purple-700 mb-3">
                Validates emails with ZeroBounce, then enriches valid contacts with Apollo.io data (job title, company, phone, LinkedIn).
              </p>
              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={handleVerifyAndEnrichSelected}
                  disabled={selectedContacts.size === 0 || verifying || syncing || enriching}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {enriching ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  {enriching ? `${currentPhase === 'enrichment' ? 'Enriching' : 'Verifying'}...` : `Verify & Enrich Selected (${selectedContacts.size})`}
                </button>
                <button
                  onClick={handleVerifyAndEnrichAll}
                  disabled={verifying || syncing || enriching}
                  className="inline-flex items-center px-3 py-2 border border-purple-300 text-sm font-medium rounded-md text-purple-700 bg-white hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Verify & Enrich All Unverified
                </button>
                {currentBatchId && !verifying && !enriching && (
                  <button
                    onClick={handleSyncEnrichment}
                    disabled={syncing}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {syncing ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Upload className="h-4 w-4 mr-2" />
                    )}
                    {syncing ? 'Syncing...' : 'Sync Enrichment to HubSpot'}
                  </button>
                )}
              </div>
            </div>

            {/* Verify Only Section */}
            <div className="mb-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Verify Only</h4>
              <p className="text-xs text-gray-600 mb-3">
                Only validates emails with ZeroBounce (no Apollo enrichment).
              </p>
              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={handleVerifySelected}
                  disabled={selectedContacts.size === 0 || verifying || syncing || enriching}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {verifying ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  {verifying ? 'Verifying...' : `Verify Selected (${selectedContacts.size})`}
                </button>
                <button
                  onClick={handleVerifyAll}
                  disabled={verifying || syncing || enriching}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Verify All Unverified
                </button>
                {currentBatchId && !verifying && !enriching && (
                  <button
                    onClick={handleSyncResults}
                    disabled={syncing}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {syncing ? (
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Upload className="h-4 w-4 mr-2" />
                    )}
                    {syncing ? 'Syncing...' : 'Sync to HubSpot'}
                  </button>
                )}
              </div>
            </div>

            {/* Delete Section */}
            <div className="flex gap-2">
              <button
                onClick={handleDeleteSelected}
                disabled={selectedContacts.size === 0 || verifying || syncing || deleting || enriching}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4 mr-2" />
                )}
                {deleting ? 'Deleting...' : `Delete Selected (${selectedContacts.size})`}
              </button>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">
                Contacts ({contacts.length})
              </h3>
              <button
                onClick={() => fetchContacts()}
                className="text-gray-600 hover:text-gray-900"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedContacts.size === contacts.length && contacts.length > 0}
                        onChange={handleSelectAll}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Verification Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {contacts.map((contact) => (
                    <tr key={contact.id}>
                      <td className="px-6 py-4">
                        <input
                          type="checkbox"
                          checked={selectedContacts.has(contact.id)}
                          onChange={() => handleSelectContact(contact.id)}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {contact.firstname} {contact.lastname}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {contact.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {contact.email_verification_status ? (
                          <StatusBadge status={contact.email_verification_status} />
                        ) : (
                          <span className="text-sm text-gray-400">Not verified</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {hasMore && (
              <div className="px-6 py-4 border-t">
                <button
                  onClick={loadMore}
                  disabled={loadingMore}
                  className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  {loadingMore ? 'Loading...' : 'Load More Contacts'}
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
