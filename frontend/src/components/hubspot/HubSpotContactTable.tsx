import { RefreshCw } from 'lucide-react';
import StatusBadge from '../StatusBadge';
import { HubSpotContact } from '../../services/api';

interface HubSpotContactTableProps {
  contacts: HubSpotContact[];
  selectedContacts: Set<string>;
  onSelectAll: () => void;
  onSelectContact: (id: string) => void;
  onRefresh: () => void;
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
}

export default function HubSpotContactTable({
  contacts,
  selectedContacts,
  onSelectAll,
  onSelectContact,
  onRefresh,
  hasMore,
  loadingMore,
  onLoadMore,
}: HubSpotContactTableProps) {
  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-6 py-4 border-b flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">
          Contacts ({contacts.length})
        </h3>
        <button onClick={onRefresh} className="text-gray-600 hover:text-gray-900">
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0 z-10">
            <tr>
              <th className="px-6 py-3 text-left">
                <input
                  type="checkbox"
                  checked={selectedContacts.size === contacts.length && contacts.length > 0}
                  onChange={onSelectAll}
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
            {contacts.map((contact, idx) => (
              <tr key={contact.id} className={idx % 2 === 1 ? 'bg-gray-50' : ''}>
                <td className="px-6 py-4">
                  <input
                    type="checkbox"
                    checked={selectedContacts.has(contact.id)}
                    onChange={() => onSelectContact(contact.id)}
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
            onClick={onLoadMore}
            disabled={loadingMore}
            className="w-full inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            {loadingMore ? 'Loading...' : 'Load More Contacts'}
          </button>
        </div>
      )}
    </div>
  );
}
