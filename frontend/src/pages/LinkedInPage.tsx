import { useState, useEffect } from 'react';
import { RefreshCw, Play, Trash2, Search, Plus, X, ExternalLink } from 'lucide-react';
import {
  getLinkedInStats,
  getLinkedInKeywords,
  addLinkedInKeyword,
  deleteLinkedInKeyword,
  getLinkedInPosts,
  deleteLinkedInPost,
  getLinkedInScrapeJobs,
  getLinkedInScrapeJob,
  startLinkedInScrape,
  processLinkedInLeads,
  LinkedInKeyword,
  LinkedInPost,
  LinkedInScrapeJob,
} from '../services/api';

export default function LinkedInPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<{
    posts: { total: number; unprocessed: number; processed: number };
    jobs: { total: number; completed: number };
    keywords_count: number;
  } | null>(null);

  const [keywords, setKeywords] = useState<LinkedInKeyword[]>([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [posts, setPosts] = useState<LinkedInPost[]>([]);
  const [jobs, setJobs] = useState<LinkedInScrapeJob[]>([]);
  const [selectedPosts, setSelectedPosts] = useState<Set<number>>(new Set());

  const [scraping, setScraping] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [_currentJobId, setCurrentJobId] = useState<number | null>(null);
  const [message, setMessage] = useState('');

  const [showUnprocessedOnly, setShowUnprocessedOnly] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, keywordsRes, postsRes, jobsRes] = await Promise.all([
        getLinkedInStats(),
        getLinkedInKeywords(),
        getLinkedInPosts(50, 0, showUnprocessedOnly),
        getLinkedInScrapeJobs(10),
      ]);
      setStats(statsRes.data);
      setKeywords(keywordsRes.data.keywords);
      setPosts(postsRes.data.posts);
      setJobs(jobsRes.data.jobs);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) return;
    try {
      await addLinkedInKeyword(newKeyword.trim());
      setNewKeyword('');
      const res = await getLinkedInKeywords();
      setKeywords(res.data.keywords);
    } catch (err) {
      console.error('Failed to add keyword:', err);
    }
  };

  const handleDeleteKeyword = async (id: number) => {
    try {
      await deleteLinkedInKeyword(id);
      setKeywords(keywords.filter(k => k.id !== id));
    } catch (err) {
      console.error('Failed to delete keyword:', err);
    }
  };

  const pollJobStatus = async (jobId: number) => {
    try {
      const res = await getLinkedInScrapeJob(jobId);
      const job = res.data;

      if (job.status === 'completed') {
        setMessage(`Scraping completed! Found ${job.posts_found} posts, saved ${job.posts_saved} new leads.`);
        setScraping(false);
        setCurrentJobId(null);
        await loadData();
      } else if (job.status === 'failed') {
        setMessage(`Scraping failed: ${job.error_message || 'Unknown error'}`);
        setScraping(false);
        setCurrentJobId(null);
      } else {
        setMessage(`Scraping in progress... (${job.status})`);
        setTimeout(() => pollJobStatus(jobId), 3000);
      }
    } catch (err) {
      console.error('Failed to poll job status:', err);
      setScraping(false);
    }
  };

  const handleStartScrape = async (searchType: 'feed' | 'search') => {
    setScraping(true);
    setMessage(`Starting LinkedIn ${searchType === 'feed' ? 'feed' : 'keyword search'} scrape...`);

    try {
      const res = await startLinkedInScrape(searchType, undefined, 10);
      setCurrentJobId(res.data.id);
      setTimeout(() => pollJobStatus(res.data.id), 2000);
    } catch (err: unknown) {
      console.error('Failed to start scrape:', err);
      const error = err as { response?: { data?: { detail?: string } } };
      setMessage(`Failed to start scrape: ${error.response?.data?.detail || 'Unknown error'}`);
      setScraping(false);
    }
  };

  const handleProcessLeads = async () => {
    const postIds = selectedPosts.size > 0 ? Array.from(selectedPosts) : undefined;
    setProcessing(true);
    setMessage('Processing leads...');

    try {
      const res = await processLinkedInLeads(postIds, true);
      setMessage(res.data.message);
      setSelectedPosts(new Set());
      await loadData();
    } catch (err: unknown) {
      console.error('Failed to process leads:', err);
      const error = err as { response?: { data?: { detail?: string } } };
      setMessage(`Failed to process: ${error.response?.data?.detail || 'Unknown error'}`);
    } finally {
      setProcessing(false);
    }
  };

  const handleDeletePost = async (id: number) => {
    try {
      await deleteLinkedInPost(id);
      setPosts(posts.filter(p => p.id !== id));
      selectedPosts.delete(id);
      setSelectedPosts(new Set(selectedPosts));
    } catch (err) {
      console.error('Failed to delete post:', err);
    }
  };

  const handleSelectPost = (id: number) => {
    const newSelected = new Set(selectedPosts);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedPosts(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedPosts.size === posts.length) {
      setSelectedPosts(new Set());
    } else {
      setSelectedPosts(new Set(posts.map(p => p.id)));
    }
  };

  const toggleUnprocessedFilter = async () => {
    const newValue = !showUnprocessedOnly;
    setShowUnprocessedOnly(newValue);
    try {
      const res = await getLinkedInPosts(50, 0, newValue);
      setPosts(res.data.posts);
    } catch (err) {
      console.error('Failed to filter posts:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">LinkedIn Lead Scraper</h2>
        <p className="mt-1 text-sm text-gray-600">
          Scrape LinkedIn for leads based on keywords, then enrich with Apollo
        </p>
      </div>

      {message && (
        <div className={`p-4 rounded-md ${scraping || processing ? 'bg-blue-50 border border-blue-200' : 'bg-green-50 border border-green-200'}`}>
          <div className="flex items-center gap-2">
            {(scraping || processing) && <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />}
            <p className={`text-sm ${scraping || processing ? 'text-blue-700' : 'text-green-700'}`}>{message}</p>
          </div>
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-gray-900">{stats.posts.total}</div>
            <div className="text-sm text-gray-500">Total Posts</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-blue-600">{stats.posts.unprocessed}</div>
            <div className="text-sm text-gray-500">Unprocessed</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-green-600">{stats.posts.processed}</div>
            <div className="text-sm text-gray-500">Processed</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-purple-600">{stats.keywords_count}</div>
            <div className="text-sm text-gray-500">Keywords</div>
          </div>
        </div>
      )}

      {/* Keywords Management */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Keywords</h3>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
            placeholder="Add new keyword..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            onClick={handleAddKeyword}
            disabled={!newKeyword.trim()}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            <Plus className="h-4 w-4 mr-1" /> Add
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {keywords.filter(k => k.is_active).map((keyword) => (
            <span
              key={keyword.id}
              className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
            >
              {keyword.keyword}
              <button
                onClick={() => handleDeleteKeyword(keyword.id)}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
          {keywords.filter(k => k.is_active).length === 0 && (
            <span className="text-sm text-gray-500">No keywords yet. Add some to start scraping.</span>
          )}
        </div>
      </div>

      {/* Scraping Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Scrape LinkedIn</h3>
        <div className="flex gap-3">
          <button
            onClick={() => handleStartScrape('feed')}
            disabled={scraping || processing}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {scraping ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            {scraping ? 'Scraping...' : 'Scrape Feed'}
          </button>
          <button
            onClick={() => handleStartScrape('search')}
            disabled={scraping || processing || keywords.filter(k => k.is_active).length === 0}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Search className="h-4 w-4 mr-2" />
            Search by Keywords
          </button>
        </div>
        <p className="mt-2 text-xs text-gray-500">
          Feed scraping checks your LinkedIn feed. Keyword search searches for posts containing your keywords.
        </p>
      </div>

      {/* Posts List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h3 className="text-lg font-medium text-gray-900">
              Scraped Posts ({posts.length})
            </h3>
            <label className="inline-flex items-center">
              <input
                type="checkbox"
                checked={showUnprocessedOnly}
                onChange={toggleUnprocessedFilter}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-600">Unprocessed only</span>
            </label>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleProcessLeads}
              disabled={processing || scraping || (stats?.posts.unprocessed === 0 && selectedPosts.size === 0)}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {processing ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              {selectedPosts.size > 0 ? `Process Selected (${selectedPosts.size})` : 'Process All Unprocessed'}
            </button>
            <button onClick={loadData} className="text-gray-600 hover:text-gray-900">
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedPosts.size === posts.length && posts.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Author</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Post Preview</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Keywords</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {posts.map((post) => (
                <tr key={post.id} className={post.is_processed ? 'bg-gray-50' : ''}>
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedPosts.has(post.id)}
                      onChange={() => handleSelectPost(post.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{post.author_name || 'Unknown'}</div>
                    {post.author_profile_url && (
                      <a
                        href={post.author_profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline inline-flex items-center"
                      >
                        Profile <ExternalLink className="h-3 w-3 ml-1" />
                      </a>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-600 max-w-md truncate">
                      {post.post_text?.substring(0, 100)}...
                    </div>
                    <div className="text-xs text-gray-400">
                      {post.comments_count} comments
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {post.keywords_matched?.map((kw, i) => (
                        <span key={i} className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {post.is_processed ? (
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Processed</span>
                    ) : (
                      <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">Pending</span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <button
                      onClick={() => handleDeletePost(post.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {posts.length === 0 && (
          <div className="px-6 py-8 text-center text-gray-500">
            No posts scraped yet. Start a scrape to find leads.
          </div>
        )}
      </div>

      {/* Recent Jobs */}
      {jobs.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Scrape Jobs</h3>
          <div className="space-y-2">
            {jobs.slice(0, 5).map((job) => (
              <div key={job.id} className="flex items-center justify-between py-2 border-b last:border-0">
                <div>
                  <span className="text-sm font-medium">{job.search_type === 'feed' ? 'Feed Scrape' : 'Keyword Search'}</span>
                  {job.is_scheduled && <span className="ml-2 text-xs text-gray-500">(Scheduled)</span>}
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-600">{job.posts_saved} posts saved</span>
                  <span className={`px-2 py-1 text-xs rounded ${
                    job.status === 'completed' ? 'bg-green-100 text-green-800' :
                    job.status === 'failed' ? 'bg-red-100 text-red-800' :
                    job.status === 'running' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {job.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
