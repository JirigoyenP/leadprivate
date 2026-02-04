import { Link2, Link2Off } from 'lucide-react';

interface HubSpotConnectionCardProps {
  connected: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

export default function HubSpotConnectionCard({ connected, onConnect, onDisconnect }: HubSpotConnectionCardProps) {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {connected ? (
            <>
              <div className="h-3 w-3 bg-green-500 rounded-full" />
              <span className="text-sm font-medium text-gray-900">Connected to HubSpot</span>
            </>
          ) : (
            <>
              <div className="h-3 w-3 bg-gray-300 rounded-full" />
              <span className="text-sm font-medium text-gray-600">Not connected</span>
            </>
          )}
        </div>

        {connected ? (
          <button
            onClick={onDisconnect}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <Link2Off className="h-4 w-4 mr-2" />
            Disconnect
          </button>
        ) : (
          <button
            onClick={onConnect}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-orange-500 hover:bg-orange-600"
          >
            <Link2 className="h-4 w-4 mr-2" />
            Connect HubSpot
          </button>
        )}
      </div>
    </div>
  );
}
