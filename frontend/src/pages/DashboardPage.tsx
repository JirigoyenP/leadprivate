import { useEffect, useState } from 'react';
import {
  Mail, CheckCircle, Users, CreditCard,
  Upload, Database, Linkedin, ArrowRight, Zap, Send
} from 'lucide-react';
import { Link } from 'react-router-dom';
import StatCard from '../components/StatCard';
import ActivityFeed from '../components/ActivityFeed';
import { getDashboardStats, getDashboardActivity, getDashboardCredits, getPipelineSummary } from '../services/api';

interface Stats {
  total_verified: number;
  unique_verified: number;
  verification_breakdown: Record<string, number>;
  total_enrichments: number;
  enriched_count: number;
  unique_enriched: number;
  enrichment_coverage: Record<string, number>;
  total_batches: number;
  completed_batches: number;
}

interface Activity {
  type: string;
  id: number;
  title: string;
  status: string;
  detail: string;
  source?: string;
  timestamp: string | null;
}

interface Credits {
  zerobounce: { credits: number | null; status: string; error?: string };
  apollo: { credits: number | null; status: string; plan?: string; error?: string };
}

interface PipelineSummary {
  imported: number;
  verified: number;
  valid: number;
  enriched: number;
  scored: number;
  outreach: number;
  avg_score: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [credits, setCredits] = useState<Credits | null>(null);
  const [pipeline, setPipeline] = useState<PipelineSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, activityRes, creditsRes, pipelineRes] = await Promise.all([
          getDashboardStats(),
          getDashboardActivity(),
          getDashboardCredits(),
          getPipelineSummary().catch(() => ({ data: null })),
        ]);
        setStats(statsRes.data);
        setActivities(activityRes.data.activities);
        setCredits(creditsRes.data);
        if (pipelineRes.data) setPipeline(pipelineRes.data);
      } catch (err) {
        console.error('Failed to load dashboard:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const verificationRate = stats && stats.unique_verified > 0
    ? Math.round(((stats.verification_breakdown.valid || 0) / stats.total_verified) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Dashboard</h2>
        <p className="text-sm text-slate-500 mt-1">Overview of your lead management pipeline</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Emails Verified"
          value={stats?.unique_verified ?? '-'}
          subtitle={`${stats?.total_verified ?? 0} total verifications`}
          icon={Mail}
          color="blue"
        />
        <StatCard
          title="Valid Emails"
          value={stats?.verification_breakdown?.valid ?? '-'}
          subtitle={`${verificationRate}% validation rate`}
          icon={CheckCircle}
          color="green"
        />
        <StatCard
          title="Contacts Enriched"
          value={stats?.unique_enriched ?? '-'}
          subtitle={`${stats?.enriched_count ?? 0} enrichments`}
          icon={Users}
          color="purple"
        />
        <StatCard
          title="Batches Completed"
          value={stats?.completed_batches ?? '-'}
          subtitle={`${stats?.total_batches ?? 0} total batches`}
          icon={Upload}
          color="indigo"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Verification Breakdown */}
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Verification Breakdown</h3>
          {stats ? (
            <div className="space-y-3">
              {[
                { label: 'Valid', value: stats.verification_breakdown.valid || 0, color: 'bg-green-500' },
                { label: 'Invalid', value: stats.verification_breakdown.invalid || 0, color: 'bg-red-500' },
                { label: 'Catch-all', value: stats.verification_breakdown['catch-all'] || 0, color: 'bg-yellow-500' },
                { label: 'Unknown', value: stats.verification_breakdown.unknown || 0, color: 'bg-gray-400' },
              ].map(({ label, value, color }) => {
                const pct = stats.total_verified > 0 ? (value / stats.total_verified) * 100 : 0;
                return (
                  <div key={label}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">{label}</span>
                      <span className="text-slate-900 font-medium">{value} ({Math.round(pct)}%)</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full">
                      <div className={`h-2 ${color} rounded-full`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="animate-pulse space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i}>
                  <div className="h-3 bg-slate-200 rounded w-1/3 mb-2" />
                  <div className="h-2 bg-slate-100 rounded-full" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Enrichment Coverage */}
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Enrichment Coverage</h3>
          {stats ? (
            <div className="space-y-3">
              {[
                { label: 'Phone Number', key: 'phone' },
                { label: 'LinkedIn URL', key: 'linkedin' },
                { label: 'Company Name', key: 'company' },
                { label: 'Job Title', key: 'title' },
              ].map(({ label, key }) => {
                const value = stats.enrichment_coverage[key] || 0;
                const pct = stats.total_enrichments > 0 ? (value / stats.total_enrichments) * 100 : 0;
                return (
                  <div key={key}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">{label}</span>
                      <span className="text-slate-900 font-medium">{value} ({Math.round(pct)}%)</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full">
                      <div className="h-2 bg-indigo-500 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="animate-pulse space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i}>
                  <div className="h-3 bg-slate-200 rounded w-1/3 mb-2" />
                  <div className="h-2 bg-slate-100 rounded-full" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Credit Balances */}
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">API Credits</h3>
          {credits ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CreditCard className="w-4 h-4 text-blue-500" />
                  <span className="text-sm font-medium text-slate-700">ZeroBounce</span>
                </div>
                <span className={`text-sm font-semibold ${
                  credits.zerobounce.status === 'connected' ? 'text-slate-900' : 'text-red-500'
                }`}>
                  {credits.zerobounce.credits !== null
                    ? credits.zerobounce.credits.toLocaleString()
                    : credits.zerobounce.status === 'error' ? 'Error' : 'N/A'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-purple-500" />
                  <div>
                    <span className="text-sm font-medium text-slate-700">Apollo</span>
                    {credits.apollo.plan && (
                      <span className="text-xs text-slate-400 ml-1">({credits.apollo.plan})</span>
                    )}
                  </div>
                </div>
                <span className={`text-sm font-semibold ${
                  credits.apollo.status === 'connected' ? 'text-slate-900' : 'text-red-500'
                }`}>
                  {credits.apollo.credits !== null
                    ? credits.apollo.credits.toLocaleString()
                    : credits.apollo.status === 'error' ? 'Error' : 'N/A'}
                </span>
              </div>
            </div>
          ) : (
            <div className="animate-pulse space-y-4">
              <div className="h-12 bg-slate-100 rounded-lg" />
              <div className="h-12 bg-slate-100 rounded-lg" />
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Feed */}
        <div className="lg:col-span-2">
          <ActivityFeed activities={activities} loading={loading} />
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">Quick Actions</h3>
          <div className="space-y-2">
            {pipeline && (
              <div className="mb-3 p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-slate-500">Total Leads</span>
                  <span className="text-sm font-semibold text-slate-900">{pipeline.imported}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-500">Avg Score</span>
                  <span className="text-sm font-semibold text-slate-900">{pipeline.avg_score}</span>
                </div>
              </div>
            )}
            {[
              { label: 'View All Leads', path: '/leads', icon: Users, color: 'text-purple-600' },
              { label: 'Verify Emails', path: '/verify', icon: Mail, color: 'text-blue-600' },
              { label: 'Upload CSV Batch', path: '/batch', icon: Upload, color: 'text-indigo-600' },
              { label: 'HubSpot Sync', path: '/hubspot', icon: Database, color: 'text-orange-600' },
              { label: 'LinkedIn Scrape', path: '/linkedin', icon: Linkedin, color: 'text-blue-700' },
              { label: 'Outreach', path: '/outreach', icon: Send, color: 'text-green-600' },
            ].map(({ label, path, icon: Icon, color }) => (
              <Link
                key={path}
                to={path}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${color}`} />
                  <span className="text-sm font-medium text-slate-700">{label}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition-colors" />
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
