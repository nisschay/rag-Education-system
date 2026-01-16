import axios from 'axios';
import createLogger from '../utils/logger';

const logger = createLogger('API');
const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  logger.debug(`${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Add response/error logging
api.interceptors.response.use(
  (response) => {
    logger.info(`${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    logger.error(`API Error: ${error.config?.url}`, {
      status: error.response?.status,
      message: error.response?.data?.detail || error.message,
    });
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, name) => api.post('/api/auth/login', { email, name }),
};

export const coursesAPI = {
  getCourses: () => api.get('/api/courses/'),
  createCourse: (data) => api.post('/api/courses/', data),
  uploadDocument: (courseId, file, unitId) => {
    const formData = new FormData();
    formData.append('file', file);
    if (unitId) formData.append('unit_id', unitId);
    return api.post(`/api/courses/${courseId}/upload`, formData);
  },
  getCourseStructure: (courseId) => api.get(`/api/courses/${courseId}/structure`),
  createUnit: (courseId, data) => api.post(`/api/courses/${courseId}/units`, data),
};

export const chatAPI = {
  createSession: (courseId, teachingMode) => 
    api.post('/api/chat/session', { course_id: courseId, teaching_mode: teachingMode }),
  sendMessage: (data) => api.post('/api/chat/message', data),
  getSessions: (courseId) => api.get('/api/chat/sessions', { params: { course_id: courseId } }),
  getMessages: (sessionId) => api.get(`/api/chat/sessions/${sessionId}/messages`),
};

export default api;
