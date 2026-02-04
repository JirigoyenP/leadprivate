import { RefreshCw } from 'lucide-react';

interface HubSpotProgressBarProps {
  message: string;
  batchProgress: { processed: number; total: number } | null;
  currentPhase: 'verification' | 'enrichment' | null;
  variant: 'default' | 'enriching' | 'deleting';
}

export default function HubSpotProgressBar({ message, batchProgress, currentPhase, variant }: HubSpotProgressBarProps) {
  if (!message) return null;

  const bgColors = {
    default: 'bg-indigo-50 border-indigo-200',
    enriching: 'bg-purple-50 border-purple-200',
    deleting: 'bg-red-50 border-red-200',
  };

  const textColors = {
    default: 'text-indigo-700',
    enriching: 'text-purple-700',
    deleting: 'text-red-700',
  };

  const spinnerColors = {
    default: 'text-indigo-600',
    enriching: 'text-purple-600',
    deleting: 'text-red-600',
  };

  const isActive = variant !== 'default' || batchProgress !== null;

  return (
    <div className={`p-4 rounded-md border ${bgColors[variant]}`}>
      <div className="flex items-center gap-2">
        {isActive && <RefreshCw className={`h-4 w-4 animate-spin ${spinnerColors[variant]}`} />}
        <p className={`text-sm ${textColors[variant]}`}>{message}</p>
      </div>
      {batchProgress && (
        <div className="mt-2">
          {currentPhase && (
            <div className="flex gap-2 mb-1 text-xs">
              <span className={currentPhase === 'verification' ? 'text-purple-700 font-medium' : 'text-gray-400'}>
                1. Verification
              </span>
              <span className="text-gray-400">&rarr;</span>
              <span className={currentPhase === 'enrichment' ? 'text-purple-700 font-medium' : 'text-gray-400'}>
                2. Enrichment
              </span>
            </div>
          )}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${variant === 'enriching' ? 'bg-purple-600' : 'bg-indigo-600'}`}
              style={{ width: `${(batchProgress.processed / batchProgress.total) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
