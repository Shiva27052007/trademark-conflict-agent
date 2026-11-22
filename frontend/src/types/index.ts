// API types matching backend schemas

export interface ScreeningRequest {
  brand_name: string;
  goods: string;
  nice_class?: number;
  nice_classes?: number[];
  jurisdiction: string;
}

export interface MatchResult {
  trademark_id: string;
  mark_name: string;
  textual_similarity: number;
  phonetic_similarity: number;
  goods_overlap: number;
  combined_score: number;
  priority: 'high' | 'medium' | 'low' | 'insufficient';
  requires_human_review: boolean;
  explanation: string;
  evidence: Record<string, unknown>;
  nice_classes: number[];
  jurisdiction: string;
}

export interface ScreeningResponse {
  screening_id: string;
  proposed_mark: string;
  jurisdiction: string;
  status: string;
  search_completeness: string;
  total_candidates: number;
  matches: MatchResult[];
  report_available: boolean;
  created_at?: string;
  completed_at?: string;
}

export interface ScreeningListItem {
  screening_id: string;
  proposed_mark: string;
  jurisdiction: string;
  status: string;
  total_candidates: number;
  created_at?: string;
}

export interface HistoryResponse {
  items: ScreeningListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface NiceClass {
  class_number: number;
  title: string;
  description: string;
  example_goods: string[];
  related_classes: number[];
}

export interface ReviewRequest {
  reviewer: string;
  decision: 'approved' | 'rejected' | 'needs_more_info' | 'escalated';
  notes?: string;
}

export interface ReviewResponse {
  id: string;
  screening_id: string;
  reviewer: string;
  decision: string;
  notes?: string;
  reviewed_at?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  timestamp: string;
}
