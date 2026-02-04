import { useState, useEffect, useRef } from 'react';
import { Search, CheckCircle, Upload, Play, Eye, Loader2, XCircle, AlertCircle } from 'lucide-react';
import {
  previewApolloSearch,
  startOneClickPipeline,
  getPipelineResults,
  getProgress,
  getHubSpotLists,
  ApolloSearchCriteria,
  PipelinePreviewContact,
  PipelineResultContact,
  HubSpotListItem,
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
];

type PipelinePhase = 'idle' | 'search' | 'verification' | 'hubspot_push' | 'completed' | 'failed';

interface ProgressData {
  phase?: string;
  phase_label?: string;
  current?: number;
  total?: number;
  percent?: number;
  status?: string;
  valid_count?: number;
  invalid_count?: number;
  unknown_count?: number;
}

export default function PipelinePage() {
  // HubSpot lists state
  const [hubspotLists, setHubspotLists] = useState<HubSpotListItem[]>([]);
  const [listsLoading, setListsLoading] = useState(true);

  // Search form state
  const [titles, setTitles] = useState('');
  const [domains, setDomains] = useState('');
  const [locations, setLocations] = useState('');
  const [seniorities, setSeniorities] = useState<string[]>([]);
  const [maxResults, setMaxResults] = useState(25);

  // Preview state
  const [previewing, setPreviewing] = useState(false);
  const [previewContacts, setPreviewContacts] = useState<PipelinePreviewContact[]>([]);
  const [previewTotal, setPreviewTotal] = useState(0);
  const [previewError, setPreviewError] = useState('');

  // Pipeline execution state
  const [running, setRunning] = useState(false);
  const [, setBatchId] = useState<number | null>(null);
  const [phase, setPhase] = useState<PipelinePhase>('idle');
  const [progress, setProgress] = useState<ProgressData>({});
  const [results, setResults] = useState<PipelineResultContact[]>([]);
  const [resultStats, setResultStats] = useState<{ search: Record<string, number>; verification: Record<string, number>; hubspot: Record<string, number> } | null>(null);
  const [error, setError] = useState('');

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  useEffect(() => {
    getHubSpotLists()
      .then(res => setHubspotLists(res.data.lists))
      .catch(() => {})
      .finally(() => setListsLoading(false));
  }, []);

  const buildCriteria = (): ApolloSearchCriteria => ({
    person_titles: titles ? titles.split(',').map(t => t.trim()).filter(Boolean) : [],
    q_organization_domains: domains ? domains.split(',').map(d => d.trim()).filter(Boolean) : [],
    person_locations: locations ? locations.split(',').map(l => l.trim()).filter(Boolean) : [],
    person_seniorities: seniorities,
    max_results: maxResults,
  });

  const handlePreview = async () => {
    setPreviewing(true);
    setPreviewError('');
    setPreviewContacts([]);
    try {
      const resp = await previewApolloSearch(buildCriteria());
      setPreviewContacts(resp.data.contacts);
      setPreviewTotal(resp.data.total_available);
    } catch (err: any) {
      setPreviewError(err.response?.data?.detail || 'Preview failed');
    } finally {
      setPreviewing(false);
    }
  };

  const handleRun = async () => {
    setRunning(true);
    setError('');
    setPhase('search');
    setProgress({});
    setResults([]);
    setResultStats(null);

    try {
      const resp = await startOneClickPipeline(buildCriteria());
      const id = resp.data.batch_id;
      setBatchId(id);

      // Start polling
      pollRef.current = setInterval(async () => {
        try {
          const prog = await getProgress(id);
          const data = prog.data as ProgressData;
          setProgress(data);

          // Map phase from progress
          if (data.phase) {
            setPhase(data.phase as PipelinePhase);
          }

          if (data.status === 'completed' || data.status === 'failed') {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;

            if (data.status === 'completed') {
              setPhase('completed');
              // Fetch final results
              try {
                const res = await getPipelineResults(id);
                setResults(res.data.contacts || []);
                setResultStats({
                  search: res.data.search,
                  verification: res.data.verification,
                  hubspot: res.data.hubspot,
                });
              } catch {
                // Results endpoint may not have full data; use progress data
              }
            } else {
              setPhase('failed');
              setError('Pipeline failed. Check server logs for details.');
            }
            setRunning(false);
          }
        } catch {
          // Polling error — keep trying
        }
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start pipeline');
      setPhase('failed');
      setRunning(false);
    }
  };

  const toggleSeniority = (value: string) => {
    setSeniorities(prev =>
      prev.includes(value) ? prev.filter(s => s !== value) : [...prev, value]
    );
  };

  const phaseSteps: { key: PipelinePhase; label: string; icon: typeof Search }[] = [
    { key: 'search', label: 'Apollo Search', icon: Search },
    { key: 'verification', label: 'ZeroBounce Verify', icon: CheckCircle },
    { key: 'hubspot_push', label: 'HubSpot Push', icon: Upload },
  ];

  const getStepStatus = (stepKey: PipelinePhase) => {
    const order: PipelinePhase[] = ['search', 'verification', 'hubspot_push'];
    const currentIdx = order.indexOf(phase);
    const stepIdx = order.indexOf(stepKey);

    if (phase === 'completed') return 'completed';
    if (phase === 'failed') return currentIdx >= stepIdx ? 'failed' : 'pending';
    if (stepIdx < currentIdx) return 'completed';
    if (stepIdx === currentIdx) return 'active';
    return 'pending';
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">One-Click Pipeline</h2>
        <p className="text-slate-500 mt-1">
          Search Apollo for contacts, verify emails with ZeroBounce, and push valid contacts to HubSpot — all in one click.
        </p>
      </div>

      {/* Current HubSpot Lists */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-3">Current HubSpot Lists</h3>
        {listsLoading ? (
          <div className="flex items-center gap-2 text-slate-500 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading lists...
          </div>
        ) : hubspotLists.length === 0 ? (
          <p className="text-sm text-slate-500">No contact lists found.</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {hubspotLists.map(list => (
              <div key={list.id} className="flex items-center justify-between py-2">
                <span className="text-sm text-slate-700">{list.name}</span>
                <span className="text-xs text-slate-500">{list.size.toLocaleString()} contacts</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">Search Criteria</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Job Titles <span className="text-slate-400">(comma-separated)</span>
            </label>
            <input
              type="text"
              value={titles}
              onChange={e => setTitles(e.target.value)}
              placeholder="CTO, VP Engineering, Head of Product"
              className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={running}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Company Domains <span className="text-slate-400">(comma-separated)</span>
            </label>
            <input
              type="text"
              value={domains}
              onChange={e => setDomains(e.target.value)}
              placeholder="google.com, meta.com, stripe.com"
              className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={running}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Locations <span className="text-slate-400">(comma-separated)</span>
            </label>
            <input
              type="text"
              value={locations}
              onChange={e => setLocations(e.target.value)}
              placeholder="United States, United Kingdom"
              className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={running}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Max Results
            </label>
            <input
              type="number"
              value={maxResults}
              onChange={e => setMaxResults(Math.max(1, Math.min(500, parseInt(e.target.value) || 25)))}
              min={1}
              max={500}
              className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={running}
            />
          </div>
        </div>

        {/* Seniority Checkboxes */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-slate-700 mb-2">Seniority Levels</label>
          <div className="flex flex-wrap gap-2">
            {SENIORITY_OPTIONS.map(opt => (
              <label
                key={opt.value}
                className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm cursor-pointer transition-colors ${
                  seniorities.includes(opt.value)
                    ? 'bg-indigo-100 text-indigo-700 border border-indigo-300'
                    : 'bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200'
                }`}
              >
                <input
                  type="checkbox"
                  checked={seniorities.includes(opt.value)}
                  onChange={() => toggleSeniority(opt.value)}
                  className="sr-only"
                  disabled={running}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex gap-3">
          <button
            onClick={handlePreview}
            disabled={previewing || running}
            className="inline-flex items-center px-4 py-2 bg-slate-100 text-slate-700 rounded-md text-sm font-medium hover:bg-slate-200 disabled:opacity-50 transition-colors"
          >
            {previewing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Eye className="w-4 h-4 mr-2" />}
            Preview Search
          </button>
          <button
            onClick={handleRun}
            disabled={running}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {running ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
            Run Pipeline
          </button>
        </div>
      </div>

      {/* Preview Results */}
      {(previewContacts.length > 0 || previewError) && phase === 'idle' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-2">
            Preview Results
            {previewTotal > 0 && (
              <span className="text-sm font-normal text-slate-500 ml-2">
                ({previewTotal.toLocaleString()} total available)
              </span>
            )}
          </h3>
          {previewError && (
            <div className="text-red-600 text-sm flex items-center gap-2">
              <XCircle className="w-4 h-4" />
              {previewError}
            </div>
          )}
          {previewContacts.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2 px-3 font-medium text-slate-600">Email</th>
                    <th className="text-left py-2 px-3 font-medium text-slate-600">Name</th>
                    <th className="text-left py-2 px-3 font-medium text-slate-600">Title</th>
                    <th className="text-left py-2 px-3 font-medium text-slate-600">Company</th>
                    <th className="text-left py-2 px-3 font-medium text-slate-600">Seniority</th>
                  </tr>
                </thead>
                <tbody>
                  {previewContacts.map((c, i) => (
                    <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-2 px-3 text-slate-800">{c.email}</td>
                      <td className="py-2 px-3 text-slate-600">{[c.first_name, c.last_name].filter(Boolean).join(' ') || '-'}</td>
                      <td className="py-2 px-3 text-slate-600">{c.title || '-'}</td>
                      <td className="py-2 px-3 text-slate-600">{c.company_name || '-'}</td>
                      <td className="py-2 px-3 text-slate-600">{c.seniority || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Progress Stepper */}
      {phase !== 'idle' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Pipeline Progress</h3>

          {/* 3-Step Stepper */}
          <div className="flex items-center justify-between mb-6">
            {phaseSteps.map((step, idx) => {
              const status = getStepStatus(step.key);
              const Icon = step.icon;
              return (
                <div key={step.key} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        status === 'completed'
                          ? 'bg-green-100 text-green-600'
                          : status === 'active'
                          ? 'bg-indigo-100 text-indigo-600'
                          : status === 'failed'
                          ? 'bg-red-100 text-red-600'
                          : 'bg-slate-100 text-slate-400'
                      }`}
                    >
                      {status === 'completed' ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : status === 'active' ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : status === 'failed' ? (
                        <XCircle className="w-5 h-5" />
                      ) : (
                        <Icon className="w-5 h-5" />
                      )}
                    </div>
                    <span className={`text-xs mt-1 font-medium ${
                      status === 'active' ? 'text-indigo-600' :
                      status === 'completed' ? 'text-green-600' :
                      status === 'failed' ? 'text-red-600' :
                      'text-slate-400'
                    }`}>
                      {step.label}
                    </span>
                  </div>
                  {idx < phaseSteps.length - 1 && (
                    <div className={`h-0.5 flex-1 mx-2 ${
                      getStepStatus(phaseSteps[idx + 1].key) !== 'pending' ? 'bg-green-300' : 'bg-slate-200'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>

          {/* Progress Bar */}
          {running && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-slate-600">
                <span>{progress.phase_label || progress.phase || 'Working...'}</span>
                <span>{progress.percent || 0}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2.5">
                <div
                  className="bg-indigo-600 h-2.5 rounded-full transition-all duration-500"
                  style={{ width: `${progress.percent || 0}%` }}
                />
              </div>
              {progress.current !== undefined && progress.total !== undefined && (
                <p className="text-xs text-slate-500">
                  {progress.current} / {progress.total} processed
                </p>
              )}
            </div>
          )}

          {/* Stats during/after run */}
          {(progress.valid_count !== undefined || resultStats) && (
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div className="bg-green-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-green-700">
                  {resultStats?.verification?.valid ?? progress.valid_count ?? 0}
                </div>
                <div className="text-xs text-green-600 font-medium">Valid</div>
              </div>
              <div className="bg-red-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-red-700">
                  {resultStats?.verification?.invalid ?? progress.invalid_count ?? 0}
                </div>
                <div className="text-xs text-red-600 font-medium">Invalid</div>
              </div>
              <div className="bg-amber-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-amber-700">
                  {resultStats?.hubspot?.pushed ?? 0}
                </div>
                <div className="text-xs text-amber-600 font-medium">Pushed to HubSpot</div>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}
        </div>
      )}

      {/* Final Results Table */}
      {phase === 'completed' && results.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">
            Pipeline Results
            <span className="text-sm font-normal text-slate-500 ml-2">
              ({results.length} contacts)
            </span>
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Email</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Name</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Title</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Company</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Verification</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">HubSpot</th>
                </tr>
              </thead>
              <tbody>
                {results.map((c, i) => (
                  <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-2 px-3 text-slate-800">{c.email}</td>
                    <td className="py-2 px-3 text-slate-600">{[c.first_name, c.last_name].filter(Boolean).join(' ') || '-'}</td>
                    <td className="py-2 px-3 text-slate-600">{c.title || '-'}</td>
                    <td className="py-2 px-3 text-slate-600">{c.company_name || '-'}</td>
                    <td className="py-2 px-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        c.verification_status === 'valid' ? 'bg-green-100 text-green-700' :
                        c.verification_status === 'invalid' ? 'bg-red-100 text-red-700' :
                        'bg-slate-100 text-slate-600'
                      }`}>
                        {c.verification_status || 'unknown'}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        c.hubspot_status === 'created' ? 'bg-green-100 text-green-700' :
                        c.hubspot_status === 'updated' ? 'bg-blue-100 text-blue-700' :
                        c.hubspot_status === null ? 'bg-slate-100 text-slate-500' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {c.hubspot_status || '-'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
