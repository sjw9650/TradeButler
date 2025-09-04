const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export { API_BASE_URL };

export interface NewsSummary {
  id: number;
  title: string;
  author?: string;
  url: string;
  source: string;
  published_at?: string;
  summary_bullets?: string[];
  insight?: string;
  tags?: string[];
  lang: string;
  created_at: string;
}

export interface Company {
  name: string;
  mention_count: number;
  latest_news?: {
    id: number;
    title: string;
    published_at?: string;
  };
  related_tags: string[];
}

export interface AIStats {
  total_contents: number;
  ai_summarized: number;
  ai_summary_rate: number;
  source_stats: Record<string, {
    total: number;
    ai_summarized: number;
  }>;
  language_stats: Record<string, number>;
  last_updated: string;
}

export const api = {
  // AI 요약 관련
  getSummaries: async (params?: {
    limit?: number;
    offset?: number;
    source?: string;
    keyword?: string;
    has_ai_summary?: boolean;
  }) => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const response = await fetch(`${API_BASE_URL}/v1/ai/summaries?${searchParams}`);
    return response.json();
  },

  getSummary: async (contentId: number) => {
    const response = await fetch(`${API_BASE_URL}/v1/ai/summaries/${contentId}`);
    return response.json();
  },

  regenerateSummary: async (contentId: number) => {
    const response = await fetch(`${API_BASE_URL}/v1/ai/summaries/${contentId}/regenerate`, {
      method: 'POST',
    });
    return response.json();
  },

  // 기업 정보 관련
  getCompanies: async (params?: {
    limit?: number;
    offset?: number;
    keyword?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const response = await fetch(`${API_BASE_URL}/v1/ai/companies?${searchParams}`);
    return response.json();
  },

  getCompanyNews: async (companyName: string, params?: {
    limit?: number;
    offset?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const response = await fetch(`${API_BASE_URL}/v1/ai/companies/${encodeURIComponent(companyName)}/news?${searchParams}`);
    return response.json();
  },

  // 통계 관련
  getStats: async (): Promise<AIStats> => {
    const response = await fetch(`${API_BASE_URL}/v1/ai/stats`);
    return response.json();
  },

  // 스케줄 관련
  getSchedules: async () => {
    const response = await fetch(`${API_BASE_URL}/v1/schedule/schedules`);
    return response.json();
  },

  triggerKoreanNews: async () => {
    const response = await fetch(`${API_BASE_URL}/v1/schedule/trigger/korean`, {
      method: 'POST',
    });
    return response.json();
  },

  triggerUSNews: async () => {
    const response = await fetch(`${API_BASE_URL}/v1/schedule/trigger/us`, {
      method: 'POST',
    });
    return response.json();
  },

  triggerAllNews: async () => {
    const response = await fetch(`${API_BASE_URL}/v1/schedule/trigger/all`, {
      method: 'POST',
    });
    return response.json();
  },
};
