import axios from 'axios';
import createLogger from '../utils/logger';

const logger = createLogger('API');

// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
  login: (email, password, name) => api.post('/api/auth/login', { email, password, name }),
  register: (email, password, name) => api.post('/api/auth/register', { email, password, name }),
  googleAuth: (credential) => api.post('/api/auth/google', { credential }),
};

export const coursesAPI = {
  getCourses: () => api.get('/api/courses/'),
  getCourse: (courseId) => api.get(`/api/courses/${courseId}`),
  createCourse: (data) => api.post('/api/courses/', data),
  deleteCourse: (courseId) => api.delete(`/api/courses/${courseId}`),
  uploadDocuments: (courseId, files, unitId, topicName) => {
    const formData = new FormData();
    // Support both single file and multiple files
    const fileList = Array.isArray(files) ? files : [files];
    fileList.forEach(file => formData.append('files', file));
    if (unitId) formData.append('unit_id', unitId);
    if (topicName) formData.append('topic_name', topicName);
    return api.post(`/api/courses/${courseId}/upload`, formData);
  },
  getCourseStructure: (courseId) => api.get(`/api/courses/${courseId}/structure`),
  getCourseDocuments: (courseId) => api.get(`/api/courses/${courseId}/documents`),
  deleteDocument: (courseId, documentId) => api.delete(`/api/courses/${courseId}/documents/${documentId}`),
  createUnit: (courseId, data) => api.post(`/api/courses/${courseId}/units`, data),
};

export const chatAPI = {
  createSession: (courseId, teachingMode) => 
    api.post('/api/chat/session', { course_id: courseId, teaching_mode: teachingMode }),
  sendMessage: (courseId, message, sessionId = null) => 
    api.post('/api/chat/message', { course_id: courseId, message, session_id: sessionId }),
  getSessions: (courseId) => api.get('/api/chat/sessions', { params: { course_id: courseId } }),
  getMessages: (sessionId) => api.get(`/api/chat/sessions/${sessionId}/messages`),
  getChatHistory: async (courseId) => {
    const sessionsRes = await api.get('/api/chat/sessions', { params: { course_id: courseId } });
    const sessions = sessionsRes.data || [];
    if (sessions.length === 0) {
      return { data: { messages: [], session_id: null } };
    }
    // Get the most recent session's messages
    const latestSession = sessions[sessions.length - 1];
    const messagesRes = await api.get(`/api/chat/sessions/${latestSession.id}/messages`);
    return { data: { messages: messagesRes.data || [], session_id: latestSession.id } };
  },
};

export default api;
