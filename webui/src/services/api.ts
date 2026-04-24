const API_BASE = import.meta.env.VITE_API_URL || '';

function getApiKey(): string | null {
  return localStorage.getItem('synthesai_api_key');
}

export function setApiKey(key: string): void {
  localStorage.setItem('synthesai_api_key', key);
}

interface RequestOptions {
  method?: string;
  body?: object;
}

async function request(path: string, options: RequestOptions = {}) {
  const apiKey = getApiKey();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.detail?.message || error.message || 'Request failed');
  }

  return response.json();
}

// Link Learning
export interface LinkResult {
  status: string;
  url: string;
  title: string;
  source: string;
  summary: string;
  key_points: string[];
  tags: string[];
  word_count: number;
  reading_time: string;
  difficulty: string;
  qa_pairs: Array<{ question: string; answer: string; difficulty?: string }>;
  quiz: Array<{ type: string; question: string; options: string[]; correct: string }>;
  files: Record<string, string | null>;
  timestamp: string;
}

export async function processLink(url: string, options?: {
  provider?: string;
  model?: string;
  output_dir?: string;
  generate_quiz?: boolean;
}): Promise<LinkResult> {
  return request('/api/v1/link', {
    method: 'POST',
    body: { url, ...options },
  });
}

// Vocabulary
export interface VocabularyResult {
  status: string;
  content: string;
  word_count: number;
  difficulty: string;
  vocabulary_cards: Array<{
    word: string;
    phonetic: { us?: string; uk?: string };
    part_of_speech: string;
    definition: { zh: string; en?: string };
    example_sentences: Array<{ sentence: string; translation: string }>;
    difficulty: string;
    frequency: string;
  }>;
  context_story: {
    title: string;
    content: string;
    word_count: number;
    difficulty: string;
    target_words: string[];
  } | null;
  statistics: Record<string, unknown>;
  files: Record<string, string | null>;
  timestamp: string;
}

export async function extractVocabulary(options: {
  content?: string;
  url?: string;
  word_count?: number;
  difficulty?: string;
  generate_story?: boolean;
}): Promise<VocabularyResult> {
  return request('/api/v1/vocabulary', {
    method: 'POST',
    body: options,
  });
}

// Video (async)
export interface TaskSubmitResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  progress: number;
  message: string;
  error: string | null;
}

export interface VideoResult {
  status: string;
  url: string;
  title: string;
  summary: {
    content: string;
    key_points: string[];
    knowledge: string[];
  };
  transcript: string;
  files: Record<string, string | null>;
  metadata: Record<string, unknown>;
  timestamp: string;
}

export async function submitVideoTask(url: string, options?: {
  format?: string;
  language?: string;
  output_dir?: string;
  cookie_file?: string;
}): Promise<TaskSubmitResponse> {
  return request('/api/v1/video/submit', {
    method: 'POST',
    body: { url, ...options },
  });
}

export async function getVideoTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  return request(`/api/v1/video/${taskId}/status`);
}

export async function getVideoTaskResult(taskId: string): Promise<VideoResult> {
  return request(`/api/v1/video/${taskId}/result`);
}

export async function cancelVideoTask(taskId: string): Promise<{ cancelled: boolean }> {
  return request(`/api/v1/video/${taskId}`, { method: 'DELETE' });
}

// Query
export interface HistoryRecord {
  id: string;
  module: string;
  title: string;
  url: string;
  timestamp: string;
  status: string;
}

export async function getHistory(options?: {
  limit?: number;
  search?: string;
  module?: string;
}): Promise<HistoryRecord[]> {
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', String(options.limit));
  if (options?.search) params.set('search', options.search);
  if (options?.module) params.set('module', options.module);
  return request(`/api/v1/history?${params}`);
}

export interface Statistics {
  total_videos: number;
  total_duration: number;
  most_watched_platform: string | null;
  recent_activity: Array<Record<string, unknown>>;
}

export async function getStatistics(): Promise<Statistics> {
  return request('/api/v1/statistics');
}

// System
export async function healthCheck(): Promise<{ status: string }> {
  return request('/health');
}