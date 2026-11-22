import axios from 'axios';
import type {
  ScreeningRequest, ScreeningResponse, HistoryResponse,
  NiceClass, ReviewRequest, ReviewResponse, HealthResponse,
} from '../types';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export const screeningApi = {
  create: (data: ScreeningRequest) =>
    api.post<ScreeningResponse>('/screen', data).then(r => r.data),

  get: (id: string) =>
    api.get<ScreeningResponse>(`/screen/${id}`).then(r => r.data),

  history: (page = 1, pageSize = 10) =>
    api.get<HistoryResponse>('/history', { params: { page, page_size: pageSize } }).then(r => r.data),
};

export const reportApi = {
  download: (screeningId: string) =>
    api.get(`/reports/${screeningId}`, { responseType: 'blob' }).then(r => {
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `screening_report_${screeningId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    }),
};

export const classesApi = {
  getAll: () =>
    api.get<NiceClass[]>('/classes').then(r => r.data),
};

export const reviewApi = {
  submit: (screeningId: string, data: ReviewRequest) =>
    api.post<ReviewResponse>(`/reviews/${screeningId}`, data).then(r => r.data),

  getAll: (screeningId: string) =>
    api.get<ReviewResponse[]>(`/reviews/${screeningId}`).then(r => r.data),
};

export const healthApi = {
  check: () =>
    api.get<HealthResponse>('/health').then(r => r.data),
};
