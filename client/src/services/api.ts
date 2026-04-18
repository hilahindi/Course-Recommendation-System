import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const api = {
  // Auth
  login: async (data: any) => axios.post(`${API_URL}/login`, data),
  register: async (data: any) => axios.post(`${API_URL}/register`, data),

  // Metadata
  getMetadata: async () => axios.get(`${API_URL}/metadata/`),

  // Courses
  getCourses: async () => axios.get(`${API_URL}/courses/`),

  // Profile
  getProfile: async (studentId: number) => axios.get(`${API_URL}/profile/${studentId}`),
  updateProfile: async (studentId: number, data: any) => axios.put(`${API_URL}/profile/${studentId}`, data),

  // History
  getHistory: async (studentId: number) => axios.get(`${API_URL}/profile/${studentId}/history`),
  addHistory: async (studentId: number, data: any) => axios.post(`${API_URL}/profile/${studentId}/history`, data),
  addHistoryBulk: async (studentId: number, data: any) => axios.post(`${API_URL}/profile/${studentId}/history/bulk`, data),

  // Recommendations
  getRecommendations: async (studentId: number) => axios.get(`${API_URL}/recommendations/${studentId}`),

  // Reviews
  getCourseReviews: async (courseCode: number) => axios.get(`${API_URL}/courses/${courseCode}/reviews`),
  createCourseReview: async (courseCode: number, studentId: number, data: any) => axios.post(`${API_URL}/courses/${courseCode}/reviews?student_id=${studentId}`, data)
};
