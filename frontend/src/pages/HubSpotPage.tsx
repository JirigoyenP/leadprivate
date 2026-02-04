import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { RefreshCw, ChevronRight } from 'lucide-react';
import {
  getHubSpotStatus,
  getHubSpotAuthUrl,
  disconnectHubSpot,
  getHubSpotContacts,
  getHubSpotListContacts,
  verifyHubSpotContacts,
  syncHubSpotResults,
  getBatchStatus,
  deleteHubSpotContacts,
  verifyAndEnrichHubSpotContacts,
  syncHubSpotEnrichment,
  HubSpotContact,
} from '../services/api';
import HubSpotConnectionCard from '../components/hubspot/HubSpotConnectionCard';
import HubSpotListSelector from '../components/hubspot/HubSpotListSelector';
import HubSpotContactStats from '../components/hubspot/HubSpotContactStats';
import HubSpotActionsPanel from '../components/hubspot/HubSpotActionsPanel';
import HubSpotContactTable from '../components/hubspot/HubSpotContactTable';
import HubSpotProgressBar from '../components/hubspot/HubSpotProgressBar';

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

  // List selection state
  const [selectedListId, setSelectedListId] = useState<string | null | undefined>(undefined);
  const [selectedListName, setSelectedListName] = useState('');
  const [loadingContacts, setLoadingContacts] = useState(false);

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
      setSelectedListId(undefined);
      setSelectedListName('');
    } catch (err) {
      console.error('Failed to disconnect:', err);
    }
  };

  const handleSelectList = async (listId: string | null, listName: string) => {
    setSelectedListId(listId);
    setSelectedListName(listName);
    setContacts([]);
    setSelectedContacts(new Set());
    setHasMore(false);
    setNextCursor(undefined);
    setMessage('');
    setCurrentBatchId(null);

    setLoadingContacts(true);
    try {
      if (listId) {
        // Fetch contacts from list
        const response = await getHubSpotListContacts(listId);
        setContacts(response.data.contacts);
        setHasMore(false);
      } else {
        // Fetch all contacts
        const response = await getHubSpotContacts({ limit: 100 });
        setContacts(response.data.contacts);
        setHasMore(response.data.has_more);
        setNextCursor(response.data.next_cursor);
      }
    } catch (err) {
      console.error('Failed to fetch contacts:', err);
      setMessage('Failed to load contacts');
    } finally {
      setLoadingContacts(false);
    }
  };

  const handleChangeList = () => {
    setSelectedListId(undefined);
    setSelectedListName('');
    setContacts([]);
    setSelectedContacts(new Set());
    setMessage('');
    setCurrentBatchId(null);
  };

  const fetchContacts = async (cursor?: string) => {
    try {
      if (cursor) {
        setLoadingMore(true);
      }

      if (selectedListId) {
        const response = await getHubSpotListContacts(selectedListId);
        setContacts(response.data.contacts);
        setHasMore(false);
      } else {
        const response = await getHubSpotContacts({ limit: 100, after: cursor });
        if (cursor) {
          setContacts(prev => [...prev, ...response.data.contacts]);
        } else {
          setContacts(response.data.contacts);
        }
        setHasMore(response.data.has_more);
        setNextCursor(response.data.next_cursor);
      }
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
      setSelectedContacts(new Set(contacts.map(c => c.id)));
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

  // Polling
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
        setMessage(`Verifying... ${batch.processed_emails}/${batch.total_emails} emails processed`);
        setTimeout(() => pollBatchStatus(batchId), 2000);
      }
    } catch (err) {
      console.error('Failed to poll batch status:', err);
      setBatchProgress(null);
      setVerifying(false);
    }
  };

  const pollEnrichBatchStatus = async (batchId: number) => {
    try {
      const response = await getBatchStatus(batchId);
      const batch = response.data;
      setBatchProgress({ processed: batch.processed_emails, total: batch.total_emails });

      if (batch.status === 'completed') {
        setMessage(`Verify & Enrich completed! ${batch.valid_count} valid emails enriched. Click "Sync to HubSpot" to update.`);
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

  // Actions
  const handleVerifyAndEnrichSelected = async () => {
    if (selectedContacts.size === 0) { setMessage('Please select contacts first'); return; }
    setEnriching(true);
    setCurrentPhase('verification');
    setMessage('Starting verification & enrichment...');
    try {
      const contactsToProcess = contacts.filter(c => selectedContacts.has(c.id)).map(c => ({ id: c.id, email: c.email }));
      const response = await verifyAndEnrichHubSpotContacts(contactsToProcess);
      setCurrentBatchId(response.data.batch_id);
      setMessage(`Processing ${response.data.contacts_queued} contacts (verify + enrich)...`);
      setTimeout(() => pollEnrichBatchStatus(response.data.batch_id), 1000);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setMessage(error.response?.data?.detail || error.message || 'Failed to start process');
      setEnriching(false);
      setCurrentPhase(null);
    }
  };

  const handleVerifyAndEnrichAll = async () => {
    setEnriching(true);
    setCurrentPhase('verification');
    setMessage('Fetching unverified contacts...');
    try {
      const response = await verifyAndEnrichHubSpotContacts();
      if (response.data.batch_id === 0) { setMessage('No unverified contacts found'); setEnriching(false); setCurrentPhase(null); return; }
      setCurrentBatchId(response.data.batch_id);
      setMessage(`Processing ${response.data.contacts_queued} contacts (verify + enrich)...`);
      setTimeout(() => pollEnrichBatchStatus(response.data.batch_id), 1000);
    } catch (err) {
      setMessage('Failed to start process');
      setEnriching(false);
      setCurrentPhase(null);
    }
  };

  const handleVerifySelected = async () => {
    if (selectedContacts.size === 0) { setMessage('Please select contacts first'); return; }
    setVerifying(true);
    setMessage('Starting verification...');
    try {
      const contactsToVerify = contacts.filter(c => selectedContacts.has(c.id)).map(c => ({ id: c.id, email: c.email }));
      const response = await verifyHubSpotContacts(contactsToVerify);
      setCurrentBatchId(response.data.batch_id);
      setMessage(`Verification started for ${response.data.contacts_queued} contacts...`);
      setTimeout(() => pollBatchStatus(response.data.batch_id), 1000);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } }; message?: string };
      setMessage(error.response?.data?.detail || error.message || 'Failed to start verification');
      setVerifying(false);
    }
  };

  const handleVerifyAll = async () => {
    setVerifying(true);
    setMessage('Fetching unverified contacts...');
    try {
      const response = await verifyHubSpotContacts();
      if (response.data.batch_id === 0) { setMessage('No unverified contacts found'); setVerifying(false); return; }
      setCurrentBatchId(response.data.batch_id);
      setMessage(`Verification started for ${response.data.contacts_queued} contacts...`);
      setTimeout(() => pollBatchStatus(response.data.batch_id), 1000);
    } catch (err) {
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

  const handleSyncEnrichment = async () => {
    if (!currentBatchId) return;
    setSyncing(true);
    setMessage('Syncing verification results to HubSpot...');
    try {
      await syncHubSpotResults(currentBatchId);
      setMessage('Syncing enrichment data to HubSpot...');
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
    if (selectedContacts.size === 0) { setMessage('Please select contacts first'); return; }
    const confirmDelete = window.confirm(`Are you sure you want to permanently delete ${selectedContacts.size} contact(s) from HubSpot? This cannot be undone.`);
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
      const error = err as { response?: { data?: { detail?: string } } };
      setMessage(`Delete failed: ${error.response?.data?.detail || 'Unknown error'}`);
    } finally {
      setDeleting(false);
    }
  };

  // Determine progress bar variant
  const progressVariant = deleting ? 'deleting' : enriching ? 'enriching' : 'default';
  const showProgress = message && (verifying || syncing || deleting || enriching || batchProgress || currentBatchId || message.startsWith('Successfully') || message.startsWith('Done'));
  const listSelected = selectedListId !== undefined;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header + Breadcrumb */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">HubSpot Integration</h2>
        {listSelected ? (
          <div className="mt-1 flex items-center gap-1 text-sm text-gray-600">
            <button onClick={handleChangeList} className="text-indigo-600 hover:text-indigo-800">
              HubSpot
            </button>
            <ChevronRight className="h-3 w-3 text-gray-400" />
            <span className="font-medium text-gray-900">
              {selectedListName} ({contacts.length} contacts)
            </span>
            <button
              onClick={handleChangeList}
              className="ml-2 text-xs text-indigo-600 hover:text-indigo-800 underline"
            >
              Change List
            </button>
          </div>
        ) : (
          <p className="mt-1 text-sm text-gray-600">
            Connect to HubSpot to verify and sync contact emails
          </p>
        )}
      </div>

      {/* Progress / Messages */}
      {showProgress && (
        <HubSpotProgressBar
          message={message}
          batchProgress={batchProgress}
          currentPhase={currentPhase}
          variant={progressVariant}
        />
      )}

      {/* Connection Card */}
      <HubSpotConnectionCard
        connected={connected}
        onConnect={handleConnect}
        onDisconnect={handleDisconnect}
      />

      {connected && !listSelected && (
        <HubSpotListSelector
          onSelectList={handleSelectList}
          selectedListId={selectedListId ?? null}
        />
      )}

      {connected && listSelected && (
        <>
          {loadingContacts ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-6 w-6 text-indigo-600 animate-spin" />
              <span className="ml-2 text-sm text-gray-600">Loading contacts...</span>
            </div>
          ) : (
            <>
              <HubSpotContactStats
                contacts={contacts}
                selectedListName={selectedListName}
                selectedCount={selectedContacts.size}
              />

              <HubSpotActionsPanel
                selectedCount={selectedContacts.size}
                verifying={verifying}
                enriching={enriching}
                syncing={syncing}
                deleting={deleting}
                currentBatchId={currentBatchId}
                currentPhase={currentPhase}
                onVerifyAndEnrichSelected={handleVerifyAndEnrichSelected}
                onVerifyAndEnrichAll={handleVerifyAndEnrichAll}
                onVerifySelected={handleVerifySelected}
                onVerifyAll={handleVerifyAll}
                onSyncResults={handleSyncResults}
                onSyncEnrichment={handleSyncEnrichment}
                onDeleteSelected={handleDeleteSelected}
              />

              <HubSpotContactTable
                contacts={contacts}
                selectedContacts={selectedContacts}
                onSelectAll={handleSelectAll}
                onSelectContact={handleSelectContact}
                onRefresh={() => fetchContacts()}
                hasMore={hasMore}
                loadingMore={loadingMore}
                onLoadMore={loadMore}
              />
            </>
          )}
        </>
      )}
    </div>
  );
}
