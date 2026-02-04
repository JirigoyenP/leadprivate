import { HubSpotContact } from '../../services/api';

interface HubSpotContactStatsProps {
  contacts: HubSpotContact[];
  selectedListName?: string;
  selectedCount: number;
}

export default function HubSpotContactStats({ contacts, selectedListName, selectedCount }: HubSpotContactStatsProps) {
  const total = contacts.length;
  const verified = contacts.filter(c => c.email_verification_status).length;
  const unverified = total - verified;
  const valid = contacts.filter(c => c.email_verification_status === 'valid').length;
  const invalid = contacts.filter(c => c.email_verification_status === 'invalid').length;
  const unknown = contacts.filter(c => c.email_verification_status === 'unknown' || c.email_verification_status === 'catch-all').length;

  const stats = [
    { label: 'Total', value: total, color: 'bg-gray-100 text-gray-800' },
    { label: 'Selected', value: selectedCount, color: 'bg-indigo-100 text-indigo-800' },
    { label: 'Verified', value: verified, color: 'bg-blue-100 text-blue-800' },
    { label: 'Unverified', value: unverified, color: 'bg-yellow-100 text-yellow-800' },
    { label: 'Valid', value: valid, color: 'bg-green-100 text-green-800' },
    { label: 'Invalid', value: invalid, color: 'bg-red-100 text-red-800' },
    { label: 'Unknown', value: unknown, color: 'bg-gray-100 text-gray-600' },
  ];

  return (
    <div className="bg-white shadow rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-700">
          {selectedListName ? `List: ${selectedListName}` : 'All Contacts'}
        </h4>
      </div>
      <div className="flex flex-wrap gap-3">
        {stats.map(stat => (
          <div key={stat.label} className={`px-3 py-1.5 rounded-md text-sm ${stat.color}`}>
            <span className="font-medium">{stat.value}</span>
            <span className="ml-1 opacity-75">{stat.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
