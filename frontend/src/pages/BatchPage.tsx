import { useState, useEffect } from 'react';
import { Download, RefreshCw } from 'lucide-react';
import FileDropzone from '../components/FileDropzone';
import StatusBadge from '../components/StatusBadge';
import { uploadCSV, getBatches, getBatchStatus, downloadBatchResults, BatchJob } from '../services/api';

export default function BatchPage() {
  const [batches, setBatches] = useState<BatchJob[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const fetchBatches = async () => {
    try {
      const response = await getBatches();
      setBatches(response.data);
    } catch (err) {
      console.error('Failed to fetch batches:', err);
    }
  };

  useEffect(() => {
    fetchBatches();
    const interval = setInterval(fetchBatches, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleFileSelect = async (file: File) => {
    setUploading(true);
    setError('');

    try {
      await uploadCSV(file);
      await fetchBatches();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (batch: BatchJob) => {
    try {
      const response = await downloadBatchResults(batch.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `verified_${batch.filename}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Failed to download:', err);
    }
  };

  const handleRefresh = async (batchId: number) => {
    try {
      const response = await getBatchStatus(batchId);
      setBatches((prev) =>
        prev.map((b) => (b.id === batchId ? response.data : b))
      );
    } catch (err) {
      console.error('Failed to refresh status:', err);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Batch CSV Upload</h2>
        <p className="mt-1 text-sm text-gray-600">
          Upload a CSV file with emails for bulk verification
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <FileDropzone onFileSelect={handleFileSelect} isLoading={uploading} />

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </div>

      {batches.length > 0 && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-medium text-gray-900">Batch Jobs</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    File
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Results
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {batches.map((batch) => (
                  <tr key={batch.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {batch.filename}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={batch.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full transition-all"
                            style={{ width: `${batch.progress_percent}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600">
                          {batch.processed_emails}/{batch.total_emails}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="text-green-600">{batch.valid_count} valid</span>
                      {' / '}
                      <span className="text-red-600">{batch.invalid_count} invalid</span>
                      {' / '}
                      <span className="text-gray-600">{batch.unknown_count} unknown</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleRefresh(batch.id)}
                          className="text-gray-600 hover:text-gray-900"
                          title="Refresh"
                        >
                          <RefreshCw className="h-4 w-4" />
                        </button>
                        {batch.status === 'completed' && (
                          <button
                            onClick={() => handleDownload(batch)}
                            className="text-indigo-600 hover:text-indigo-900"
                            title="Download"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                        )}
                      </div>
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
