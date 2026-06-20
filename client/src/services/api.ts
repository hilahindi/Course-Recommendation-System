import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({ baseURL: API_URL });

apiClient.interceptors.request.use((config) => {
  const stored = localStorage.getItem('user');
  if (stored) {
    try {
      const user = JSON.parse(stored);
      if (user?.user_id != null) {
        config.headers['X-Student-Id'] = String(user.user_id);
      }
    } catch {
      /* ignore invalid stored user */
    }
  }
  return config;
});

export const api = {
  // Auth
  login: async (data: { email: string; password: string }) =>
    apiClient.post('/login', data),
  register: async (data: { email: string; password: string; name: string }) =>
    apiClient.post('/register', data),

  // Metadata
  getMetadata: async () => apiClient.get('/metadata/'),

  // Courses
  getCourses: async () => apiClient.get('/courses/'),
  getYearlyMandatoryCourses: async () => apiClient.get('/courses/yearly-mandatory'),

  // Profile
  getProfile: async (studentId: number) => apiClient.get(`/profile/${studentId}`),
  updateProfile: async (studentId: number, data: unknown) =>
    apiClient.put(`/profile/${studentId}`, data),

  // History
  getHistory: async (studentId: number) =>
    apiClient.get(`/profile/${studentId}/history`),
  addHistory: async (studentId: number, data: unknown) =>
    apiClient.post(`/profile/${studentId}/history`, data),
  addHistoryBulk: async (studentId: number, data: unknown) =>
    apiClient.post(`/profile/${studentId}/history/bulk`, data),
  deleteHistory: async (studentId: number, courseCode: number) =>
    apiClient.delete(`/profile/${studentId}/history/${courseCode}`),

  // Recommendations (student id from X-Student-Id header; may take up to ~2 min)
  getRecommendations: async () =>
    apiClient.post('/recommendations/get', undefined, { timeout: 120_000 }),

  // Reviews
  getCourseReviews: async (courseCode: number) =>
    apiClient.get(`/courses/${courseCode}/reviews`),
  createCourseReview: async (
    courseCode: number,
    _studentId: number,
    data: {
      rating: number;
      review_text: string;
      is_anonymous?: boolean;
    }
  ) =>
    apiClient.post('/reviews/submit', {
      course_code: courseCode,
      rating: data.rating,
      review_text: data.review_text,
      is_anonymous: data.is_anonymous ?? false,
    }),

  // Roadmap
  getRoadmap: async () => apiClient.get('/recommendations/roadmap'),

  // Schedule
  getSchedule: (studentId: number) =>
    apiClient.get(`/profile/${studentId}/schedule`),
  addSchedule: (studentId: number, data: { course_code: number }) =>
    apiClient.post(`/profile/${studentId}/schedule`, data),
  removeSchedule: (studentId: number, courseCode: number) =>
    apiClient.delete(`/profile/${studentId}/schedule/${courseCode}`),
};
