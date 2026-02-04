import { Upload, Database, Linkedin, Clock } from 'lucide-react';
import StatusBadge from './StatusBadge';

interface Activity {
  type: string;
  id: number;
  title: string;
  status: string;
  detail: string;
  source?: string;
  timestamp: string | null;
}

interface ActivityFeedProps {
  activities: Activity[];
  loading?: boolean;
}

const typeIcons: Record<string, typeof Upload> = {
  batch: Upload,
  hubspot_sync: Database,
  linkedin_scrape: Linkedin,
};

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDays = Math.floor(diffHr / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export default function ActivityFeed({ activities, loading }: ActivityFeedProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="text-sm font-semibold text-slate-900 mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse flex items-center gap-3">
              <div className="w-8 h-8 bg-slate-200 rounded-lg" />
              <div className="flex-1">
                <div className="h-4 bg-slate-200 rounded w-3/4 mb-1" />
                <div className="h-3 bg-slate-100 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6">
      <h3 className="text-sm font-semibold text-slate-900 mb-4">Recent Activity</h3>
      {activities.length === 0 ? (
        <p className="text-sm text-slate-400">No recent activity</p>
      ) : (
        <div className="space-y-3">
          {activities.map((activity) => {
            const Icon = typeIcons[activity.type] || Clock;
            return (
              <div key={`${activity.type}-${activity.id}`} className="flex items-start gap-3">
                <div className="p-1.5 rounded-md bg-slate-100 text-slate-500 mt-0.5">
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-700 truncate">
                      {activity.title}
                    </span>
                    <StatusBadge status={activity.status} />
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{activity.detail}</p>
                </div>
                <span className="text-xs text-slate-400 whitespace-nowrap">
                  {timeAgo(activity.timestamp)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
