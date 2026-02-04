import { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, ArrowRight, Upload, CheckCircle, Sparkles, Star, Send } from 'lucide-react';
import { getPipelineSummary } from '../services/api';

interface PipelineSummary {
  imported: number;
  verified: number;
  valid: number;
  enriched: number;
  scored: number;
  outreach: number;
  avg_score: number;
}

interface PipelineViewProps {
  onProcess?: () => void;
  processing?: boolean;
}

const stages = [
  { key: 'imported', label: 'Imported', icon: Upload, color: 'bg-slate-500' },
  { key: 'verified', label: 'Verified', icon: CheckCircle, color: 'bg-blue-500' },
  { key: 'enriched', label: 'Enriched', icon: Sparkles, color: 'bg-purple-500' },
  { key: 'scored', label: 'Scored', icon: Star, color: 'bg-yellow-500' },
  { key: 'outreach', label: 'Outreach', icon: Send, color: 'bg-green-500' },
];

export default function PipelineView({ onProcess, processing }: PipelineViewProps) {
  const [data, setData] = useState<PipelineSummary | null>(null);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    getPipelineSummary()
      .then((res) => setData(res.data))
      .catch(() => {});
  }, []);

  if (!data) return null;

  return (
    <div className="bg-white rounded-lg border border-slate-200">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-slate-900">Lead Pipeline</h3>
          <span className="text-xs text-slate-400">Avg Score: {data.avg_score}</span>
        </div>
        {collapsed ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronUp className="w-4 h-4 text-slate-400" />}
      </button>

      {!collapsed && (
        <div className="px-5 pb-5">
          <div className="flex items-center justify-between">
            {stages.map((stage, i) => {
              const count = data[stage.key as keyof PipelineSummary] as number;
              const Icon = stage.icon;
              return (
                <div key={stage.key} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div className={`w-10 h-10 rounded-full ${stage.color} flex items-center justify-center`}>
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-lg font-semibold text-slate-900 mt-1">{count}</span>
                    <span className="text-xs text-slate-500">{stage.label}</span>
                  </div>
                  {i < stages.length - 1 && (
                    <ArrowRight className="w-5 h-5 text-slate-300 mx-3 mt-[-20px]" />
                  )}
                </div>
              );
            })}
          </div>

          {onProcess && (
            <div className="mt-4 flex justify-center">
              <button
                onClick={onProcess}
                disabled={processing || data.imported === 0}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {processing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Process All Leads
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
