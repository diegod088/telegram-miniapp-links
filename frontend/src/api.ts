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

/**
 * Generalized feed fetching supporting trending, new, and top.
 * Handles both cursor-based (for 'new') and page-based (for others) pagination.
 */
export const getFeed = async (
  mode: 'trending' | 'new' | 'top' = 'trending',
  category?: string,
  cursor?: string,
  page?: number,
  q?: string,
  language?: string,
  limit: number = 20
) => {
  const params: any = { limit };
  if (category && category !== 'ALL') params.category = category;
  if (cursor) params.cursor = cursor;
  if (page) params.page = page;
  if (q) params.q = q;
  if (language) params.language = language;
  
  const response = await api.get(`/feed/${mode}`, { params });
  return response.data;
};

/**
 * Backward compatibility for explore feed.
 * Now routes to trending feed.
 */
export const getExploreFeed = (category?: string, cursor?: string, q?: string) => {
  return getFeed('trending', category, cursor, undefined, q);
};

export const toggleLike = async (linkId: number) => {
  const response = await api.post(`/explore/links/${linkId}/like`);
  return response.data;
};

export const toggleDislike = async (linkId: number) => {
  const response = await api.post(`/explore/links/${linkId}/dislike`);
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

export const getPublicProfile = async (slug: string) => {
  const response = await api.get(`/profiles/${slug}`);
  return response.data;
};

export const createProfile = async (data: { slug: string; display_name: string; bio?: string }) => {
  const response = await api.post('/profiles', data);
  return response.data;
};

export const updateProfile = async (data: { display_name?: string; bio?: string; theme?: any; contact_username?: string }) => {
  const response = await api.patch('/profiles/me', data);
  return response.data;
};

export const addLink = async (data: { url: string; title?: string; category: string; description?: string }) => {
  const response = await api.post('/profiles/me/links', data);
  return response.data;
};

export const updateLink = async (linkId: number, data: any) => {
  const response = await api.put(`/profiles/me/links/${linkId}`, data);
  return response.data;
};

export const deleteLink = async (linkId: number) => {
  const response = await api.delete(`/profiles/me/links/${linkId}`);
  return response.data;
};

export const boostLink = async (linkId: number) => {
  const response = await api.post(`/profiles/me/links/${linkId}/boost`);
  return response.data;
};

// --- Payments ---

export const createInvoice = async (planId: string) => {
  const response = await api.post(`/payments/create-invoice?plan_id=${planId}`);
  return response.data;
};

export const fetchMyPlan = async () => {
  const response = await api.get('/profiles/me/plan');
  return response.data;
};

// --- Ranking ---

export const getProfileRanking = async (
  sortBy: 'likes' | 'views' = 'likes',
  category?: string,
  limit: number = 20,
  offset: number = 0
) => {
  const params: any = { sort_by: sortBy, limit, offset };
  if (category && category !== 'ALL') params.category = category;
  const response = await api.get('/discovery/ranking', { params });
  return response.data;
};

export const toggleFavorite = async (linkId: number) => {
  const response = await api.post(`/social/links/${linkId}/favorite`);
  return response.data;
};

export const getFavorites = async () => {
  const response = await api.get('/social/favorites');
  return response.data;
};

export const getPulse = async () => {
  const response = await api.get('/discovery/pulse');
  return response.data;
};

export const getFeaturedProfiles = async () => {
  const response = await api.get('/discovery/featured');
  return response.data;
};

export const getLanguages = async () => {
    const response = await api.get('/discovery/languages');
    return response.data;
};

export default api;
