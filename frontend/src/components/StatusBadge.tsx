interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const colors: Record<string, string> = {
    valid: 'bg-green-100 text-green-800',
    invalid: 'bg-red-100 text-red-800',
    'catch-all': 'bg-yellow-100 text-yellow-800',
    unknown: 'bg-gray-100 text-gray-800',
    pending: 'bg-blue-100 text-blue-800',
    processing: 'bg-indigo-100 text-indigo-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const colorClass = colors[status.toLowerCase()] || 'bg-gray-100 text-gray-800';

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {status}
    </span>
  );
}
