import { Play, Upload, Trash2, RefreshCw } from 'lucide-react';

interface HubSpotActionsPanelProps {
  selectedCount: number;
  verifying: boolean;
  enriching: boolean;
  syncing: boolean;
  deleting: boolean;
  currentBatchId: number | null;
  currentPhase: 'verification' | 'enrichment' | null;
  onVerifyAndEnrichSelected: () => void;
  onVerifyAndEnrichAll: () => void;
  onVerifySelected: () => void;
  onVerifyAll: () => void;
  onSyncResults: () => void;
  onSyncEnrichment: () => void;
  onDeleteSelected: () => void;
}

export default function HubSpotActionsPanel({
  selectedCount,
  verifying,
  enriching,
  syncing,
  deleting,
  currentBatchId,
  currentPhase,
  onVerifyAndEnrichSelected,
  onVerifyAndEnrichAll,
  onVerifySelected,
  onVerifyAll,
  onSyncResults,
  onSyncEnrichment,
  onDeleteSelected,
}: HubSpotActionsPanelProps) {
  const busy = verifying || syncing || enriching || deleting;
  const showSync = currentBatchId && !verifying && !enriching;

  return (
    <div className="bg-white shadow rounded-lg p-4">
      <div className="flex flex-wrap items-center gap-2">
        {/* Primary: Verify & Enrich */}
        <button
          onClick={onVerifyAndEnrichSelected}
          disabled={selectedCount === 0 || busy}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {enriching ? (
            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Play className="h-4 w-4 mr-2" />
          )}
          {enriching
            ? `${currentPhase === 'enrichment' ? 'Enriching' : 'Verifying'}...`
            : `Verify & Enrich (${selectedCount})`}
        </button>

        <button
          onClick={onVerifyAndEnrichAll}
          disabled={busy}
          className="inline-flex items-center px-3 py-2 border border-purple-300 text-sm font-medium rounded-md text-purple-700 bg-white hover:bg-purple-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          V&E All Unverified
        </button>

        <div className="w-px h-6 bg-gray-300 mx-1" />

        {/* Secondary: Verify Only */}
        <button
          onClick={onVerifySelected}
          disabled={selectedCount === 0 || busy}
          className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {verifying ? (
            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Play className="h-4 w-4 mr-2" />
          )}
          {verifying ? 'Verifying...' : `Verify Only (${selectedCount})`}
        </button>

        <button
          onClick={onVerifyAll}
          disabled={busy}
          className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Verify All
        </button>

        {/* Sync buttons - contextual */}
        {showSync && (
          <>
            <div className="w-px h-6 bg-gray-300 mx-1" />
            <button
              onClick={onSyncEnrichment}
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
            <button
              onClick={onSyncResults}
              disabled={syncing}
              className="inline-flex items-center px-3 py-2 border border-green-300 text-sm font-medium rounded-md text-green-700 bg-white hover:bg-green-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Sync Verification Only
            </button>
          </>
        )}

        {/* Spacer to push delete to the right */}
        <div className="flex-1" />

        {/* Delete */}
        <button
          onClick={onDeleteSelected}
          disabled={selectedCount === 0 || busy}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {deleting ? (
            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4 mr-2" />
          )}
          {deleting ? 'Deleting...' : `Delete (${selectedCount})`}
        </button>
      </div>
    </div>
  );
}
