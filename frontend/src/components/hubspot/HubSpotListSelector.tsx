import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Search, List, Users } from 'lucide-react';
import { getHubSpotLists, HubSpotList } from '../../services/api';

interface HubSpotListSelectorProps {
  onSelectList: (listId: string | null, listName: string) => void;
  selectedListId: string | null;
}

export default function HubSpotListSelector({ onSelectList, selectedListId }: HubSpotListSelectorProps) {
  const [lists, setLists] = useState<HubSpotList[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [scopeError, setScopeError] = useState(false);

  const fetchLists = useCallback(async (search?: string) => {
    setLoading(true);
    setScopeError(false);
    try {
      const response = await getHubSpotLists(search);
      setLists(response.data.lists);
    } catch (err: unknown) {
      const error = err as { response?: { status?: number } };
      if (error.response?.status === 403) {
        setScopeError(true);
      }
      console.error('Failed to fetch lists:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLists();
  }, [fetchLists]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(searchInput);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    fetchLists(searchQuery || undefined);
  }, [searchQuery, fetchLists]);

  if (scopeError) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
        <p className="text-sm text-yellow-800 mb-2">
          The Lists permission is missing. Please reconnect HubSpot to grant the required scope.
        </p>
        <button
          onClick={() => onSelectList(null, 'All Contacts')}
          className="inline-flex items-center px-4 py-2 border border-yellow-300 text-sm font-medium rounded-md text-yellow-800 bg-white hover:bg-yellow-50"
        >
          <Users className="h-4 w-4 mr-2" />
          Continue with All Contacts
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Select a List</h3>
        <button onClick={() => fetchLists(searchQuery || undefined)} className="text-gray-600 hover:text-gray-900">
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search lists..."
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="h-6 w-6 text-indigo-600 animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {/* All Contacts option */}
          <button
            onClick={() => onSelectList(null, 'All Contacts')}
            className={`text-left p-4 rounded-lg border-2 transition-colors ${
              selectedListId === null
                ? 'border-indigo-500 bg-indigo-50'
                : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Users className="h-4 w-4 text-indigo-600" />
              <span className="text-sm font-medium text-gray-900">All Contacts</span>
            </div>
            <p className="text-xs text-gray-500">Load all contacts from HubSpot</p>
          </button>

          {/* List cards */}
          {lists.map(list => (
            <button
              key={list.list_id}
              onClick={() => onSelectList(list.list_id, list.name)}
              className={`text-left p-4 rounded-lg border-2 transition-colors ${
                selectedListId === list.list_id
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <List className="h-4 w-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-900 truncate">{list.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">{list.size} contacts</span>
                {list.processing_type && (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
                    {list.processing_type}
                  </span>
                )}
              </div>
            </button>
          ))}

          {lists.length === 0 && (
            <div className="col-span-full text-center py-4 text-sm text-gray-500">
              No lists found{searchQuery ? ` matching "${searchQuery}"` : ''}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
