import { ChevronUp, ChevronDown, ExternalLink } from 'lucide-react';
import LeadScoreBadge from './LeadScoreBadge';
import StatusBadge from './StatusBadge';

interface Lead {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  title?: string;
  phone?: string;
  linkedin_url?: string;
  company_name?: string;
  verification_status?: string;
  lead_score: number;
  source?: string;
  created_at?: string;
}

interface LeadsTableProps {
  leads: Lead[];
  selectedIds: Set<number>;
  onToggleSelect: (id: number) => void;
  onToggleSelectAll: () => void;
  allSelected: boolean;
  sortBy: string;
  sortOrder: string;
  onSort: (column: string) => void;
  onRowClick: (lead: Lead) => void;
}

function SortIcon({ column, sortBy, sortOrder }: { column: string; sortBy: string; sortOrder: string }) {
  if (column !== sortBy) return <ChevronUp className="w-3 h-3 text-slate-300" />;
  return sortOrder === 'asc'
    ? <ChevronUp className="w-3 h-3 text-indigo-600" />
    : <ChevronDown className="w-3 h-3 text-indigo-600" />;
}

export default function LeadsTable({
  leads,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
  allSelected,
  sortBy,
  sortOrder,
  onSort,
  onRowClick,
}: LeadsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-200 text-left">
            <th className="px-3 py-3 w-10">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={onToggleSelectAll}
                className="rounded border-slate-300"
              />
            </th>
            <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <button onClick={() => onSort('email')} className="flex items-center gap-1">
                Name / Email <SortIcon column="email" sortBy={sortBy} sortOrder={sortOrder} />
              </button>
            </th>
            <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <button onClick={() => onSort('lead_score')} className="flex items-center gap-1">
                Score <SortIcon column="lead_score" sortBy={sortBy} sortOrder={sortOrder} />
              </button>
            </th>
            <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <button onClick={() => onSort('verification_status')} className="flex items-center gap-1">
                Status <SortIcon column="verification_status" sortBy={sortBy} sortOrder={sortOrder} />
              </button>
            </th>
            <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Source</th>
            <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <button onClick={() => onSort('company_name')} className="flex items-center gap-1">
                Company <SortIcon column="company_name" sortBy={sortBy} sortOrder={sortOrder} />
              </button>
            </th>
            <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Title</th>
            <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Phone</th>
            <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">LinkedIn</th>
            <th className="px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <button onClick={() => onSort('created_at')} className="flex items-center gap-1">
                Date <SortIcon column="created_at" sortBy={sortBy} sortOrder={sortOrder} />
              </button>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {leads.map((lead) => (
            <tr
              key={lead.id}
              className={`hover:bg-slate-50 cursor-pointer transition-colors ${
                selectedIds.has(lead.id) ? 'bg-indigo-50' : ''
              }`}
            >
              <td className="px-3 py-3" onClick={(e) => e.stopPropagation()}>
                <input
                  type="checkbox"
                  checked={selectedIds.has(lead.id)}
                  onChange={() => onToggleSelect(lead.id)}
                  className="rounded border-slate-300"
                />
              </td>
              <td className="px-3 py-3" onClick={() => onRowClick(lead)}>
                <div>
                  <p className="text-sm font-medium text-slate-900 truncate max-w-[200px]">
                    {lead.full_name || `${lead.first_name || ''} ${lead.last_name || ''}`.trim() || lead.email}
                  </p>
                  <p className="text-xs text-slate-400 truncate max-w-[200px]">{lead.email}</p>
                </div>
              </td>
              <td className="px-3 py-3" onClick={() => onRowClick(lead)}>
                <LeadScoreBadge score={lead.lead_score} size="sm" />
              </td>
              <td className="px-3 py-3" onClick={() => onRowClick(lead)}>
                {lead.verification_status ? (
                  <StatusBadge status={lead.verification_status} />
                ) : (
                  <span className="text-xs text-slate-400">-</span>
                )}
              </td>
              <td className="px-3 py-3" onClick={() => onRowClick(lead)}>
                <span className="text-xs text-slate-500">{lead.source || '-'}</span>
              </td>
              <td className="px-3 py-3" onClick={() => onRowClick(lead)}>
                <span className="text-sm text-slate-700 truncate max-w-[150px] block">
                  {lead.company_name || '-'}
                </span>
              </td>
              <td className="px-3 py-3" onClick={() => onRowClick(lead)}>
                <span className="text-sm text-slate-700 truncate max-w-[150px] block">
                  {lead.title || '-'}
                </span>
              </td>
              <td className="px-3 py-3" onClick={() => onRowClick(lead)}>
                <span className="text-xs text-slate-500">{lead.phone || '-'}</span>
              </td>
              <td className="px-3 py-3">
                {lead.linkedin_url ? (
                  <a
                    href={lead.linkedin_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-indigo-500 hover:text-indigo-700"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                ) : (
                  <span className="text-xs text-slate-400">-</span>
                )}
              </td>
              <td className="px-3 py-3" onClick={() => onRowClick(lead)}>
                <span className="text-xs text-slate-400">
                  {lead.created_at ? new Date(lead.created_at).toLocaleDateString() : '-'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {leads.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          <p className="text-sm">No leads found</p>
          <p className="text-xs mt-1">Try adjusting your filters or import some leads</p>
        </div>
      )}
    </div>
  );
}
