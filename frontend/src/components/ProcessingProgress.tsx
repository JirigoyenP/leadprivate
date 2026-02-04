import { useEffect, useState } from 'react';
import { X, CheckCircle, Loader2 } from 'lucide-react';
import { getProgress } from '../services/api';

interface ProgressData {
  batch_id: number;
  status: string;
  total: number;
  processed: number;
  percent: number;
  phase?: string;
  valid_count?: number;
  invalid_count?: number;
}

interface ProcessingProgressProps {
  batchId: number;
  onClose: () => void;
  onComplete?: () => void;
}

const phaseLabels: Record<string, string> = {
  verification: 'Verifying emails',
  enrichment: 'Enriching contacts',
  scoring: 'Scoring leads',
};

export default function ProcessingProgress({ batchId, onClose, onComplete }: ProcessingProgressProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    const poll = async () => {
      try {
        const res = await getProgress(batchId);
        setProgress(res.data);

        if (res.data.status === 'completed' || res.data.status === 'failed') {
          setCompleted(true);
          clearInterval(interval);
          if (res.data.status === 'completed' && onComplete) {
            onComplete();
          }
        }
      } catch {
        // Ignore polling errors
      }
    };

    poll();
    interval = setInterval(poll, 2000);

    return () => clearInterval(interval);
  }, [batchId, onComplete]);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900">
            {completed ? 'Processing Complete' : 'Processing Leads'}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {progress ? (
          <div className="space-y-4">
            {/* Phase indicator */}
            {progress.phase && !completed && (
              <div className="flex items-center gap-2 text-sm text-indigo-600">
                <Loader2 className="w-4 h-4 animate-spin" />
                {phaseLabels[progress.phase] || progress.phase}
              </div>
            )}

            {completed && progress.status === 'completed' && (
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle className="w-4 h-4" />
                All done
              </div>
            )}

            {completed && progress.status === 'failed' && (
              <div className="text-sm text-red-600">
                Processing failed. Check batch logs for details.
              </div>
            )}

            {/* Progress bar */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600">Progress</span>
                <span className="text-slate-900 font-medium">{progress.percent}%</span>
              </div>
              <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-3 rounded-full transition-all duration-500 ${
                    completed
                      ? progress.status === 'completed'
                        ? 'bg-green-500'
                        : 'bg-red-500'
                      : 'bg-indigo-500'
                  }`}
                  style={{ width: `${progress.percent}%` }}
                />
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-2 bg-slate-50 rounded-lg">
                <div className="text-lg font-semibold text-slate-900">{progress.processed}</div>
                <div className="text-xs text-slate-500">Processed</div>
              </div>
              {progress.valid_count !== undefined && (
                <div className="text-center p-2 bg-green-50 rounded-lg">
                  <div className="text-lg font-semibold text-green-700">{progress.valid_count}</div>
                  <div className="text-xs text-green-600">Valid</div>
                </div>
              )}
              {progress.invalid_count !== undefined && (
                <div className="text-center p-2 bg-red-50 rounded-lg">
                  <div className="text-lg font-semibold text-red-700">{progress.invalid_count}</div>
                  <div className="text-xs text-red-600">Invalid</div>
                </div>
              )}
            </div>

            {/* Close button */}
            {completed && (
              <button
                onClick={onClose}
                className="w-full py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Close
              </button>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center py-8">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>
    </div>
  );
}
