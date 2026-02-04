import { useState } from 'react';
import { Search, RefreshCw, Download, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';
import {
  searchApolloLeads,
  ApolloSearchPerson,
  ApolloSearchRequest,
} from '../services/api';

const SENIORITY_OPTIONS = [
  { value: 'owner', label: 'Owner' },
  { value: 'founder', label: 'Founder' },
  { value: 'c_suite', label: 'C-Suite' },
  { value: 'partner', label: 'Partner' },
  { value: 'vp', label: 'VP' },
  { value: 'head', label: 'Head' },
  { value: 'director', label: 'Director' },
  { value: 'manager', label: 'Manager' },
  { value: 'senior', label: 'Senior' },
  { value: 'entry', label: 'Entry' },
  { value: 'intern', label: 'Intern' },
];

const EMPLOYEE_RANGE_OPTIONS = [
  { value: '1,10', label: '1-10' },
  { value: '11,20', label: '11-20' },
  { value: '21,50', label: '21-50' },
  { value: '51,100', label: '51-100' },
  { value: '101,200', label: '101-200' },
  { value: '201,500', label: '201-500' },
  { value: '501,1000', label: '501-1K' },
  { value: '1001,5000', label: '1K-5K' },
  { value: '5001,10000', label: '5K-10K' },
  { value: '10001,', label: '10K+' },
];

export default function ApolloPage() {
  // Search form state
  const [titles, setTitles] = useState('');
  const [keywords, setKeywords] = useState('');
  const [personLocations, setPersonLocations] = useState('');
  const [orgDomains, setOrgDomains] = useState('');
  const [orgLocations, setOrgLocations] = useState('');
  const [selectedSeniorities, setSelectedSeniorities] = useState<Set<string>>(new Set());
  const [selectedRanges, setSelectedRanges] = useState<Set<string>>(new Set());

  // Results state
  const [results, setResults] = useState<ApolloSearchPerson[]>([]);
  const [selectedLeads, setSelectedLeads] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [hasSearched, setHasSearched] = useState(false);

  const splitComma = (s: string) => s.split(',').map(v => v.trim()).filter(Boolean);

  const toggleSeniority = (val: string) => {
    const next = new Set(selectedSeniorities);
    next.has(val) ? next.delete(val) : next.add(val);
    setSelectedSeniorities(next);
  };

  const toggleRange = (val: string) => {
    const next = new Set(selectedRanges);
    next.has(val) ? next.delete(val) : next.add(val);
    setSelectedRanges(next);
  };

  const buildRequest = (page: number): ApolloSearchRequest => {
    const req: ApolloSearchRequest = { page, per_page: 25 };
    if (titles.trim()) req.person_titles = splitComma(titles);
    if (keywords.trim()) req.q_keywords = keywords.trim();
    if (personLocations.trim()) req.person_locations = splitComma(personLocations);
    if (orgDomains.trim()) req.organization_domains = splitComma(orgDomains);
    if (orgLocations.trim()) req.organization_locations = splitComma(orgLocations);
    if (selectedSeniorities.size > 0) req.person_seniorities = Array.from(selectedSeniorities);
    if (selectedRanges.size > 0) req.organization_num_employees_ranges = Array.from(selectedRanges);
    return req;
  };

  const handleSearch = async (page = 1) => {
    setLoading(true);
    setError('');
    setHasSearched(true);
    try {
      const response = await searchApolloLeads(buildRequest(page));
      setResults(response.data.people);
      setTotalResults(response.data.total);
      setCurrentPage(response.data.page);
      setTotalPages(response.data.total_pages);
      setSelectedLeads(new Set());
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(e.response?.data?.detail || e.message || 'Search failed');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = () => {
    if (selectedLeads.size === results.length) {
      setSelectedLeads(new Set());
    } else {
      setSelectedLeads(new Set(results.map((_, i) => String(i))));
    }
  };

  const toggleLead = (idx: string) => {
    const next = new Set(selectedLeads);
    next.has(idx) ? next.delete(idx) : next.add(idx);
    setSelectedLeads(next);
  };

  const handleExportCSV = () => {
    const leadsToExport = selectedLeads.size > 0
      ? results.filter((_, i) => selectedLeads.has(String(i)))
      : results;

    if (leadsToExport.length === 0) return;

    const headers = ['First Name', 'Last Name', 'Email', 'Title', 'Seniority', 'Company', 'Industry', 'Company Size', 'LinkedIn', 'Phone', 'City', 'Country'];
    const rows = leadsToExport.map(p => [
      p.first_name || '', p.last_name || '', p.email || '', p.title || '',
      p.seniority || '', p.company_name || '', p.company_industry || '',
      p.company_size?.toString() || '', p.linkedin_url || '',
      (p.phone_numbers || []).join('; '), p.city || '', p.country || '',
    ]);

    const csv = [headers, ...rows].map(r => r.map(c => `"${c.replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `apollo_leads_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Apollo Prospecting</h2>
        <p className="mt-1 text-sm text-gray-600">
          Search for leads by job title, company, location, and more
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Search Criteria</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Job Titles</label>
            <input
              type="text"
              value={titles}
              onChange={(e) => setTitles(e.target.value)}
              placeholder="CEO, CTO, VP Sales (comma-separated)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Keywords</label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="Free-text search (e.g. marketing automation)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Person Locations</label>
            <input
              type="text"
              value={personLocations}
              onChange={(e) => setPersonLocations(e.target.value)}
              placeholder="United States, United Kingdom (comma-separated)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Company Domains</label>
            <input
              type="text"
              value={orgDomains}
              onChange={(e) => setOrgDomains(e.target.value)}
              placeholder="google.com, meta.com (comma-separated)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Company Locations</label>
            <input
              type="text"
              value={orgLocations}
              onChange={(e) => setOrgLocations(e.target.value)}
              placeholder="California, New York (comma-separated)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Seniority checkboxes */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Seniority</label>
          <div className="flex flex-wrap gap-2">
            {SENIORITY_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => toggleSeniority(opt.value)}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  selectedSeniorities.has(opt.value)
                    ? 'bg-indigo-100 border-indigo-300 text-indigo-800'
                    : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Employee range checkboxes */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Company Size (Employees)</label>
          <div className="flex flex-wrap gap-2">
            {EMPLOYEE_RANGE_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => toggleRange(opt.value)}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  selectedRanges.has(opt.value)
                    ? 'bg-indigo-100 border-indigo-300 text-indigo-800'
                    : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={() => handleSearch(1)}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Search className="h-4 w-4 mr-2" />
          )}
          {loading ? 'Searching...' : 'Search Leads'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 rounded-md bg-red-50 border border-red-200">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Results */}
      {hasSearched && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-medium text-gray-900">
                Results ({totalResults.toLocaleString()})
              </h3>
              {selectedLeads.size > 0 && (
                <span className="text-sm text-indigo-600">{selectedLeads.size} selected</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleExportCSV}
                disabled={results.length === 0}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                <Download className="h-4 w-4 mr-1" />
                Export CSV
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedLeads.size === results.length && results.length > 0}
                      onChange={handleSelectAll}
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Links</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.map((person, idx) => (
                  <tr key={person.apollo_id || idx} className={idx % 2 === 1 ? 'bg-gray-50' : ''}>
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedLeads.has(String(idx))}
                        onChange={() => toggleLead(String(idx))}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {person.first_name} {person.last_name}
                      </div>
                      {person.seniority && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-indigo-100 text-indigo-700">
                          {person.seniority}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {person.title || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{person.company_name || '-'}</div>
                      {person.company_industry && (
                        <div className="text-xs text-gray-500">{person.company_industry}</div>
                      )}
                      {person.company_size && (
                        <div className="text-xs text-gray-400">{person.company_size.toLocaleString()} employees</div>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {person.email || <span className="text-gray-400 italic">Hidden</span>}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {[person.city, person.country].filter(Boolean).join(', ') || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {person.linkedin_url && (
                        <a
                          href={person.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-800"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
                {results.length === 0 && !loading && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">
                      No results found. Try broadening your search criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Page {currentPage} of {totalPages} ({totalResults.toLocaleString()} total)
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => handleSearch(currentPage - 1)}
                  disabled={currentPage <= 1 || loading}
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </button>
                <button
                  onClick={() => handleSearch(currentPage + 1)}
                  disabled={currentPage >= totalPages || loading}
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
