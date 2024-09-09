import { client } from '@/lib/api/services.gen';


export const Config = {
  API_NETLOC: "http://localhost:5000",
  API_BASE_URL: "http://localhost:5000/v1",
  API_AUTH_URL: "http://localhost:5000/v1/auth",
  REQUEST: {
    TIMEOUT: 1000,
  },
};

client.setConfig({
  baseURL: Config.API_NETLOC,
  timeout: Config.REQUEST.TIMEOUT,
});

client.instance.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('access_token') || "";
  config.headers.set('Authorization', `Bearer ${accessToken}`);
  return config;
});