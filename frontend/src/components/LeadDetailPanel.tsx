import { X, Mail, Phone, Linkedin, Building2, MapPin, Briefcase, User } from 'lucide-react';
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
  company_domain?: string;
  company_industry?: string;
  company_size?: number;
  company_location?: string;
  verification_status?: string;
  verification_sub_status?: string;
  verification_score?: number;
  enriched: boolean;
  seniority?: string;
  headline?: string;
  city?: string;
  state?: string;
  country?: string;
  lead_score: number;
  score_breakdown?: Record<string, number>;
  source?: string;
  outreach_status?: string;
  created_at?: string;
}

interface LeadDetailPanelProps {
  lead: Lead;
  onClose: () => void;
}

export default function LeadDetailPanel({ lead, onClose }: LeadDetailPanelProps) {
  const location = [lead.city, lead.state, lead.country].filter(Boolean).join(', ');

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl border-l border-slate-200 z-50 overflow-y-auto">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              {lead.full_name || lead.email}
            </h3>
            {lead.title && (
              <p className="text-sm text-slate-500 mt-0.5">{lead.title}</p>
            )}
          </div>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Score */}
        <div className="flex items-center gap-3 mb-6">
          <LeadScoreBadge score={lead.lead_score} />
          {lead.verification_status && (
            <StatusBadge status={lead.verification_status} />
          )}
          {lead.source && (
            <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
              {lead.source}
            </span>
          )}
        </div>

        {/* Contact Info */}
        <div className="space-y-3 mb-6">
          <div className="flex items-center gap-2 text-sm">
            <Mail className="w-4 h-4 text-slate-400" />
            <span className="text-slate-700">{lead.email}</span>
          </div>
          {lead.phone && (
            <div className="flex items-center gap-2 text-sm">
              <Phone className="w-4 h-4 text-slate-400" />
              <span className="text-slate-700">{lead.phone}</span>
            </div>
          )}
          {lead.linkedin_url && (
            <div className="flex items-center gap-2 text-sm">
              <Linkedin className="w-4 h-4 text-slate-400" />
              <a href={lead.linkedin_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline truncate">
                {lead.linkedin_url}
              </a>
            </div>
          )}
          {location && (
            <div className="flex items-center gap-2 text-sm">
              <MapPin className="w-4 h-4 text-slate-400" />
              <span className="text-slate-700">{location}</span>
            </div>
          )}
        </div>

        {/* Company Info */}
        {lead.company_name && (
          <div className="border-t border-slate-100 pt-4 mb-6">
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Company</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <Building2 className="w-4 h-4 text-slate-400" />
                <span className="text-slate-700">{lead.company_name}</span>
              </div>
              {lead.company_industry && (
                <div className="flex items-center gap-2 text-sm">
                  <Briefcase className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-700">{lead.company_industry}</span>
                </div>
              )}
              {lead.company_size && (
                <div className="flex items-center gap-2 text-sm">
                  <User className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-700">{lead.company_size.toLocaleString()} employees</span>
                </div>
              )}
              {lead.company_location && (
                <div className="flex items-center gap-2 text-sm">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-700">{lead.company_location}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Score Breakdown */}
        {lead.score_breakdown && (
          <div className="border-t border-slate-100 pt-4 mb-6">
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Score Breakdown</h4>
            <div className="space-y-2">
              {Object.entries(lead.score_breakdown).map(([key, value]) => {
                const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                const maxValue = 25;
                const pct = (value / maxValue) * 100;
                return (
                  <div key={key}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">{label}</span>
                      <span className="text-slate-900 font-medium">{value}/{maxValue}</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full">
                      <div
                        className={`h-1.5 rounded-full ${pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-400'}`}
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Verification Details */}
        <div className="border-t border-slate-100 pt-4">
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Verification</h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-slate-500">Status</div>
            <div className="text-slate-700">{lead.verification_status || 'Not verified'}</div>
            {lead.verification_sub_status && (
              <>
                <div className="text-slate-500">Sub-status</div>
                <div className="text-slate-700">{lead.verification_sub_status}</div>
              </>
            )}
            {lead.seniority && (
              <>
                <div className="text-slate-500">Seniority</div>
                <div className="text-slate-700">{lead.seniority}</div>
              </>
            )}
            <div className="text-slate-500">Enriched</div>
            <div className="text-slate-700">{lead.enriched ? 'Yes' : 'No'}</div>
            {lead.outreach_status && (
              <>
                <div className="text-slate-500">Outreach</div>
                <div className="text-slate-700">{lead.outreach_status}</div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
