import axios from 'axios';

// Use environment variable for production, fallback to /api for dev (proxy)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export interface VerifyResponse {
  email: string;
  status: string;
  sub_status?: string;
  score?: number;
  free_email?: boolean;
  did_you_mean?: string;
  domain?: string;
  verified_at: string;
}

export interface BatchJob {
  id: number;
  filename: string;
  status: string;
  total_emails: number;
  processed_emails: number;
  valid_count: number;
  invalid_count: number;
  unknown_count: number;
  progress_percent: number;
  error_message?: string;
  created_at: string;
}

export interface HubSpotContact {
  id: string;
  email: string;
  firstname?: string;
  lastname?: string;
  email_verification_status?: string;
}

export interface HubSpotContactList {
  contacts: HubSpotContact[];
  total: number;
  has_more: boolean;
  next_cursor?: string;
}

// Verification endpoints
export const verifySingle = (email: string) =>
  api.post<VerifyResponse>('/verify/single', { email });

export const verifyBatch = (emails: string[]) =>
  api.post('/verify/batch', { emails });

// Batch endpoints
export const uploadCSV = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post<{ id: number; message: string }>('/batch/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getBatchStatus = (id: number) =>
  api.get<BatchJob>(`/batch/${id}`);

export const getBatches = () =>
  api.get<BatchJob[]>('/batch/');

export const downloadBatchResults = (id: number) =>
  api.get(`/batch/${id}/download`, { responseType: 'blob' });

// HubSpot endpoints
export const getHubSpotAuthUrl = () =>
  api.get<{ auth_url: string }>('/hubspot/auth');

export const getHubSpotStatus = () =>
  api.get<{ connected: boolean; portal_id?: string }>('/hubspot/status');

export const disconnectHubSpot = () =>
  api.delete('/hubspot/disconnect');

export const getHubSpotContacts = (params?: { limit?: number; after?: string; only_unverified?: boolean }) =>
  api.get<HubSpotContactList>('/hubspot/contacts', { params });

export const verifyHubSpotContacts = (contacts?: { id: string; email: string }[], forceReverify = false) =>
  api.post('/hubspot/verify', { contacts, force_reverify: forceReverify });

export const syncHubSpotResults = (batchId: number) =>
  api.post(`/hubspot/sync?batch_id=${batchId}`);

export interface HubSpotDeleteResponse {
  deleted_count: number;
  failed_count: number;
  deleted: string[];
  failed: { id: string; error: string }[];
}

export const deleteHubSpotContacts = (contactIds: string[]) =>
  api.post<HubSpotDeleteResponse>('/hubspot/delete', { contact_ids: contactIds });

// Verify + Enrich workflow (HubSpot -> ZeroBounce -> Apollo)
export interface VerifyAndEnrichResponse {
  batch_id: number;
  status: string;
  contacts_queued: number;
  message: string;
  will_enrich: boolean;
}

export const verifyAndEnrichHubSpotContacts = (
  contacts?: { id: string; email: string }[],
  forceReverify = false,
  enrichValidOnly = true
) =>
  api.post<VerifyAndEnrichResponse>('/hubspot/verify-and-enrich', {
    contacts,
    force_reverify: forceReverify,
    enrich_valid_only: enrichValidOnly,
  });

export const syncHubSpotEnrichment = (batchId: number) =>
  api.post(`/hubspot/sync-enrichment?batch_id=${batchId}`);

// HubSpot Lists
export interface HubSpotList {
  list_id: string;
  name: string;
  size: number;
  processing_type?: string;
  created_at?: string;
  updated_at?: string;
}

export interface HubSpotListsResponse {
  lists: HubSpotList[];
  total: number;
}

export interface HubSpotListContactsResponse {
  contacts: HubSpotContact[];
  total: number;
  list_id: string;
}

export const getHubSpotLists = (search?: string) =>
  api.get<HubSpotListsResponse>('/hubspot/lists', { params: search ? { search } : {} });

export const getHubSpotListContacts = (listId: string) =>
  api.get<HubSpotListContactsResponse>(`/hubspot/lists/${listId}/contacts`);

// Apollo direct endpoints
export interface ApolloEnrichResponse {
  email: string;
  enriched: boolean;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  title?: string;
  headline?: string;
  linkedin_url?: string;
  phone_numbers?: string[];
  company_name?: string;
  company_domain?: string;
  company_industry?: string;
  company_size?: number;
  seniority?: string;
  enriched_at?: string;
  error?: string;
}

export const enrichSingle = (email: string) =>
  api.post<ApolloEnrichResponse>('/apollo/enrich', { email });

export const enrichBulk = (emails: string[]) =>
  api.post<{ results: ApolloEnrichResponse[]; total: number; enriched_count: number }>('/apollo/enrich/bulk', { emails });

// Apollo People Search (Prospecting)
export interface ApolloSearchPerson {
  apollo_id?: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  email?: string;
  title?: string;
  headline?: string;
  linkedin_url?: string;
  seniority?: string;
  city?: string;
  state?: string;
  country?: string;
  company_name?: string;
  company_domain?: string;
  company_industry?: string;
  company_size?: number;
  company_linkedin_url?: string;
  phone_numbers?: string[];
}

export interface ApolloSearchRequest {
  person_titles?: string[];
  person_locations?: string[];
  person_seniorities?: string[];
  organization_domains?: string[];
  organization_locations?: string[];
  organization_num_employees_ranges?: string[];
  q_keywords?: string;
  page?: number;
  per_page?: number;
}

export interface ApolloSearchResponse {
  people: ApolloSearchPerson[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export const searchApolloLeads = (params: ApolloSearchRequest) =>
  api.post<ApolloSearchResponse>('/apollo/search', params);

// LinkedIn endpoints
export interface LinkedInKeyword {
  id: number;
  keyword: string;
  is_active: boolean;
  created_at: string;
}

export interface LinkedInPost {
  id: number;
  author_name?: string;
  author_profile_url?: string;
  author_country?: string;
  post_text?: string;
  post_date?: string;
  comments_count: number;
  keywords_matched?: string[];
  scraped_at: string;
  is_processed: boolean;
}

export interface LinkedInScrapeJob {
  id: number;
  search_type: string;
  status: string;
  keywords_used?: string[];
  posts_found: number;
  posts_saved: number;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  is_scheduled: boolean;
}

export const getLinkedInKeywords = () =>
  api.get<{ keywords: LinkedInKeyword[]; total: number }>('/linkedin/keywords');

export const addLinkedInKeyword = (keyword: string) =>
  api.post<LinkedInKeyword>('/linkedin/keywords', { keyword });

export const deleteLinkedInKeyword = (id: number) =>
  api.delete(`/linkedin/keywords/${id}`);

export const startLinkedInScrape = (
  searchType: 'feed' | 'search' = 'feed',
  keywords?: string[],
  maxScrolls: number = 10
) =>
  api.post<LinkedInScrapeJob>('/linkedin/scrape', {
    search_type: searchType,
    keywords,
    max_scrolls: maxScrolls,
  });

export const getLinkedInScrapeJob = (jobId: number) =>
  api.get<LinkedInScrapeJob>(`/linkedin/scrape/${jobId}`);

export const getLinkedInScrapeJobs = (limit: number = 20) =>
  api.get<{ jobs: LinkedInScrapeJob[]; total: number }>(`/linkedin/scrape?limit=${limit}`);

export const getLinkedInPosts = (limit: number = 50, offset: number = 0, unprocessedOnly: boolean = false) =>
  api.get<{ posts: LinkedInPost[]; total: number; unprocessed_count: number }>(
    `/linkedin/posts?limit=${limit}&offset=${offset}&unprocessed_only=${unprocessedOnly}`
  );

export const deleteLinkedInPost = (id: number) =>
  api.delete(`/linkedin/posts/${id}`);

export const processLinkedInLeads = (postIds?: number[], enrichWithApollo: boolean = true) =>
  api.post<{ batch_id: number; status: string; leads_queued: number; message: string }>(
    '/linkedin/process-leads',
    { post_ids: postIds, enrich_with_apollo: enrichWithApollo }
  );

export const getLinkedInStats = () =>
  api.get<{
    posts: { total: number; unprocessed: number; processed: number };
    jobs: { total: number; completed: number };
    keywords_count: number;
  }>('/linkedin/stats');

export default api;
