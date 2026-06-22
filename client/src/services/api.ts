import axios from 'axios';
import { cachedRequest, getCacheEntry, invalidateCache } from '../lib/queryCache';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({ baseURL: API_URL });

apiClient.interceptors.request.use((config) => {
  const stored = localStorage.getItem('user');
  if (stored) {
    try {
      const user = JSON.parse(stored);
      if (user?.access_token) {
        config.headers['Authorization'] = `Bearer ${user.access_token}`;
      }
    } catch {
      /* ignore invalid stored user */
    }
  }
  return config;
});

// Expired/invalid token -> clear session and force re-login.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('user');
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  },
);

function invalidateStudentData(studentId: number) {
  invalidateCache(
    `profile:${studentId}`,
    `history:${studentId}`,
    `schedule:${studentId}`,
    'recommendations',
    'roadmap',
  );
}

async function cachedGet<T>(
  key: string,
  fetcher: () => Promise<{ data: T }>,
  options?: { force?: boolean },
): Promise<{ data: any }> {
  const data = await cachedRequest<T>(
    key,
    async () => {
      const res = await fetcher();
      return res.data;
    },
    options,
  );
  return { data };
}

export { getCacheEntry, invalidateCache };

export const api = {
  // Auth
  login: async (data: { email: string; password: string }) =>
    apiClient.post('/login', data),
  register: async (data: { email: string; password: string; name: string }) =>
    apiClient.post('/register', data),

  // Metadata
  getMetadata: async (options?: { force?: boolean }) =>
    cachedGet('metadata', () => apiClient.get('/metadata/'), options),

  // Courses
  getCourses: async (options?: { force?: boolean }) =>
    cachedGet('courses', () => apiClient.get('/courses/'), options),
  getYearlyMandatoryCourses: async (options?: { force?: boolean }) =>
    cachedGet('yearly-mandatory', () => apiClient.get('/courses/yearly-mandatory'), options),

  // Profile
  getProfile: async (studentId: number, options?: { force?: boolean }) =>
    cachedGet(`profile:${studentId}`, () => apiClient.get(`/profile/${studentId}`), options),
  updateProfile: async (studentId: number, data: unknown) => {
    const res = await apiClient.put(`/profile/${studentId}`, data);
    invalidateStudentData(studentId);
    invalidateCache('recommendations', 'roadmap');
    return res;
  },

  // History
  getHistory: async (studentId: number, options?: { force?: boolean }) =>
    cachedGet(`history:${studentId}`, () => apiClient.get(`/profile/${studentId}/history`), options),
  addHistory: async (studentId: number, data: unknown) => {
    const res = await apiClient.post(`/profile/${studentId}/history`, data);
    invalidateStudentData(studentId);
    return res;
  },
  addHistoryBulk: async (studentId: number, data: unknown) => {
    const res = await apiClient.post(`/profile/${studentId}/history/bulk`, data);
    invalidateStudentData(studentId);
    return res;
  },
  deleteHistory: async (studentId: number, courseCode: number) => {
    const res = await apiClient.delete(`/profile/${studentId}/history/${courseCode}`);
    invalidateStudentData(studentId);
    return res;
  },

  // Recommendations (student id from X-Student-Id header; may take up to ~2 min)
  getRecommendations: async (options?: { force?: boolean }) =>
    cachedGet(
      'recommendations',
      () => apiClient.post('/recommendations/get', undefined, { timeout: 120_000 }),
      options,
    ),

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
  createCourseReviewsBulk: async (
    reviews: Array<{
      course_code: number;
      rating: number;
      review_text: string;
      is_anonymous?: boolean;
    }>
  ) => apiClient.post('/reviews/bulk', { reviews }),
  seedAllCourseReviews: async () => apiClient.post('/reviews/seed-all'),
  deleteAllCourseReviews: async () => apiClient.delete('/reviews/all'),

  // Roadmap
  getRoadmap: async (options?: { force?: boolean }) =>
    cachedGet(
      'roadmap',
      () => apiClient.get('/recommendations/roadmap'),
      options,
    ),

  // Admin — curriculum & user management (admin role required)
  adminListUsers: async () => apiClient.get('/admin/users'),
  adminSetUserRole: async (userId: number, role: string) =>
    apiClient.patch(`/admin/users/${userId}/role`, { role }),
  adminCreateCourse: async (data: unknown) => {
    const res = await apiClient.post('/admin/courses', data);
    invalidateCache('courses');
    return res;
  },
  adminUpdateCourse: async (courseCode: number, data: unknown) => {
    const res = await apiClient.put(`/admin/courses/${courseCode}`, data);
    invalidateCache('courses');
    return res;
  },
  adminDeleteCourse: async (courseCode: number) => {
    const res = await apiClient.delete(`/admin/courses/${courseCode}`);
    invalidateCache('courses');
    return res;
  },

  // Schedule
  getSchedule: (studentId: number, options?: { force?: boolean }) =>
    cachedGet(`schedule:${studentId}`, () => apiClient.get(`/profile/${studentId}/schedule`), options),
  addSchedule: async (studentId: number, data: { course_code: number }) => {
    const res = await apiClient.post(`/profile/${studentId}/schedule`, data);
    invalidateCache(`schedule:${studentId}`);
    return res;
  },
  removeSchedule: async (studentId: number, courseCode: number) => {
    const res = await apiClient.delete(`/profile/${studentId}/schedule/${courseCode}`);
    invalidateCache(`schedule:${studentId}`);
    return res;
  },
};
