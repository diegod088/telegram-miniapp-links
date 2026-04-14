import axios from 'axios';
import WebApp from '@twa-dev/sdk';

const api = axios.create({
  baseURL: '/api',
});

// Inject Telegram Init Data in every request
api.interceptors.request.use((config) => {
  const initData = WebApp.initData;
  if (initData) {
    config.headers['X-Telegram-Init-Data'] = initData;
  }
  return config;
});

export const getExploreFeed = async (category?: string, cursor?: string, q?: string) => {
  const params: any = {};
  if (category && category !== 'ALL') params.category = category;
  if (cursor) params.cursor = cursor;
  if (q) params.q = q;
  
  const response = await api.get('/explore/feed', { params });
  return response.data;
};

export const upvoteLink = async (linkId: number) => {
  const response = await api.post(`/explore/links/${linkId}/upvote`);
  return response.data;
};

export const getRedirectInfo = async (linkId: number) => {
  const response = await api.get(`/explore/links/${linkId}/redirect`);
  return response.data;
};

// --- Profile & Link Management ---

export const getMyProfile = async () => {
  const response = await api.get('/profiles/me');
  return response.data;
};

export const createProfile = async (data: { slug: string; display_name: string }) => {
  const response = await api.post('/profiles', data);
  return response.data;
};

export const addLink = async (data: { url: string; title?: string; category: string; description?: string }) => {
  const response = await api.post('/profiles/me/links', data);
  return response.data;
};

export const deleteLink = async (linkId: number) => {
  const response = await api.delete(`/profiles/me/links/${linkId}`);
  return response.data;
};

export default api;
