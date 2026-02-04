import { useState, useEffect, useCallback } from 'react';
import { getLeads } from '../services/api';

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
  enriched: boolean;
  seniority?: string;
  lead_score: number;
  score_breakdown?: Record<string, number>;
  source?: string;
  outreach_status?: string;
  created_at?: string;
  updated_at?: string;
}

interface LeadsState {
  leads: Lead[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  loading: boolean;
  error: string | null;

  // Filters
  search: string;
  source: string;
  verificationStatus: string;
  scoreMin: string;
  scoreMax: string;

  // Sort
  sortBy: string;
  sortOrder: string;

  // Selection
  selectedIds: Set<number>;
}

export function useLeads() {
  const [state, setState] = useState<LeadsState>({
    leads: [],
    total: 0,
    page: 1,
    pageSize: 50,
    totalPages: 0,
    loading: true,
    error: null,
    search: '',
    source: '',
    verificationStatus: '',
    scoreMin: '',
    scoreMax: '',
    sortBy: 'created_at',
    sortOrder: 'desc',
    selectedIds: new Set(),
  });

  const fetchLeads = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const params: Record<string, string | number | boolean> = {
        page: state.page,
        page_size: state.pageSize,
        sort_by: state.sortBy,
        sort_order: state.sortOrder,
      };
      if (state.search) params.search = state.search;
      if (state.source) params.source = state.source;
      if (state.verificationStatus) params.verification_status = state.verificationStatus;
      if (state.scoreMin) params.score_min = parseInt(state.scoreMin);
      if (state.scoreMax) params.score_max = parseInt(state.scoreMax);

      const res = await getLeads(params);
      setState((prev) => ({
        ...prev,
        leads: res.data.leads,
        total: res.data.total,
        totalPages: res.data.total_pages,
        loading: false,
      }));
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: err.message || 'Failed to load leads',
      }));
    }
  }, [state.page, state.pageSize, state.sortBy, state.sortOrder, state.search, state.source, state.verificationStatus, state.scoreMin, state.scoreMax]);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  const setSearch = (search: string) => setState((prev) => ({ ...prev, search, page: 1 }));
  const setSource = (source: string) => setState((prev) => ({ ...prev, source, page: 1 }));
  const setVerificationStatus = (verificationStatus: string) => setState((prev) => ({ ...prev, verificationStatus, page: 1 }));
  const setScoreMin = (scoreMin: string) => setState((prev) => ({ ...prev, scoreMin, page: 1 }));
  const setScoreMax = (scoreMax: string) => setState((prev) => ({ ...prev, scoreMax, page: 1 }));
  const setPage = (page: number) => setState((prev) => ({ ...prev, page }));

  const setSort = (column: string) => {
    setState((prev) => ({
      ...prev,
      sortBy: column,
      sortOrder: prev.sortBy === column && prev.sortOrder === 'desc' ? 'asc' : 'desc',
      page: 1,
    }));
  };

  const toggleSelect = (id: number) => {
    setState((prev) => {
      const next = new Set(prev.selectedIds);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { ...prev, selectedIds: next };
    });
  };

  const toggleSelectAll = () => {
    setState((prev) => {
      if (prev.selectedIds.size === prev.leads.length) {
        return { ...prev, selectedIds: new Set() };
      }
      return { ...prev, selectedIds: new Set(prev.leads.map((l) => l.id)) };
    });
  };

  const clearSelection = () => setState((prev) => ({ ...prev, selectedIds: new Set() }));

  const clearFilters = () =>
    setState((prev) => ({
      ...prev,
      search: '',
      source: '',
      verificationStatus: '',
      scoreMin: '',
      scoreMax: '',
      page: 1,
    }));

  return {
    ...state,
    setSearch,
    setSource,
    setVerificationStatus,
    setScoreMin,
    setScoreMax,
    setPage,
    setSort,
    toggleSelect,
    toggleSelectAll,
    clearSelection,
    clearFilters,
    refresh: fetchLeads,
  };
}
