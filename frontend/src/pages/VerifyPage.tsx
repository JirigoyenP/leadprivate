import { useState } from 'react';
import { Search, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { verifySingle, VerifyResponse } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function VerifyPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState('');

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await verifySingle(email);
      setResult(response.data);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to verify email');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'valid':
        return <CheckCircle className="h-8 w-8 text-green-500" />;
      case 'invalid':
        return <XCircle className="h-8 w-8 text-red-500" />;
      default:
        return <AlertCircle className="h-8 w-8 text-yellow-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Single Email Verification</h2>
        <p className="mt-1 text-sm text-gray-600">
          Enter an email address to verify its validity
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <form onSubmit={handleVerify} className="flex gap-4">
          <div className="flex-1">
            <label htmlFor="email" className="sr-only">
              Email address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email address"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 px-4 py-2 border"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !email.trim()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Search className="h-4 w-4 mr-2" />
            {loading ? 'Verifying...' : 'Verify'}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {result && (
          <div className="mt-6 border-t pt-6">
            <div className="flex items-start gap-4">
              {getStatusIcon(result.status)}
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-medium text-gray-900">{result.email}</h3>
                  <StatusBadge status={result.status} />
                </div>

                {result.sub_status && (
                  <p className="mt-1 text-sm text-gray-500">
                    Sub-status: {result.sub_status}
                  </p>
                )}

                {result.did_you_mean && (
                  <p className="mt-2 text-sm text-indigo-600">
                    Did you mean: <strong>{result.did_you_mean}</strong>?
                  </p>
                )}

                <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
                  {result.domain && (
                    <div>
                      <dt className="text-gray-500">Domain</dt>
                      <dd className="font-medium">{result.domain}</dd>
                    </div>
                  )}
                  {result.free_email !== undefined && (
                    <div>
                      <dt className="text-gray-500">Free Email</dt>
                      <dd className="font-medium">{result.free_email ? 'Yes' : 'No'}</dd>
                    </div>
                  )}
                  {result.score !== undefined && (
                    <div>
                      <dt className="text-gray-500">Score</dt>
                      <dd className="font-medium">{result.score}</dd>
                    </div>
                  )}
                </dl>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
