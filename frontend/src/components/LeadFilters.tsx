import { Search, X } from 'lucide-react';

interface LeadFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  source: string;
  onSourceChange: (value: string) => void;
  verificationStatus: string;
  onVerificationStatusChange: (value: string) => void;
  scoreMin: string;
  onScoreMinChange: (value: string) => void;
  scoreMax: string;
  onScoreMaxChange: (value: string) => void;
  onClearFilters: () => void;
}

export default function LeadFilters({
  search,
  onSearchChange,
  source,
  onSourceChange,
  verificationStatus,
  onVerificationStatusChange,
  scoreMin,
  onScoreMinChange,
  scoreMax,
  onScoreMaxChange,
  onClearFilters,
}: LeadFiltersProps) {
  const hasFilters = search || source || verificationStatus || scoreMin || scoreMax;

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Search */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search by name, email, company..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
      </div>

      {/* Source filter */}
      <select
        value={source}
        onChange={(e) => onSourceChange(e.target.value)}
        className="px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
      >
        <option value="">All Sources</option>
        <option value="csv">CSV</option>
        <option value="hubspot">HubSpot</option>
        <option value="linkedin">LinkedIn</option>
        <option value="apollo">Apollo</option>
      </select>

      {/* Verification status */}
      <select
        value={verificationStatus}
        onChange={(e) => onVerificationStatusChange(e.target.value)}
        className="px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
      >
        <option value="">All Statuses</option>
        <option value="valid">Valid</option>
        <option value="invalid">Invalid</option>
        <option value="catch-all">Catch-all</option>
        <option value="unknown">Unknown</option>
      </select>

      {/* Score range */}
      <div className="flex items-center gap-1">
        <input
          type="number"
          placeholder="Min"
          value={scoreMin}
          onChange={(e) => onScoreMinChange(e.target.value)}
          min={0}
          max={100}
          className="w-16 px-2 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <span className="text-slate-400 text-xs">-</span>
        <input
          type="number"
          placeholder="Max"
          value={scoreMax}
          onChange={(e) => onScoreMaxChange(e.target.value)}
          min={0}
          max={100}
          className="w-16 px-2 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Clear filters */}
      {hasFilters && (
        <button
          onClick={onClearFilters}
          className="inline-flex items-center gap-1 px-3 py-2 text-sm text-slate-500 hover:text-slate-700 border border-slate-200 rounded-lg hover:bg-slate-50"
        >
          <X className="w-3 h-3" />
          Clear
        </button>
      )}
    </div>
  );
}
