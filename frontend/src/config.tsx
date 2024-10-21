import { client } from "@/lib/api/services.gen";
import { jwtDecode } from "jwt-decode";

const ENV = import.meta.env;
const API_NETLOC = `${ENV.VITE_BACKEND_API_HOST}:${ENV.VITE_BACKEND_API_PORT}`;
const API_BASE_URL = `http://${API_NETLOC}`;

export const Config = {
  API_AUTH_URL: `${API_BASE_URL}/v1/auth`,
  API_GPT_URL: `${API_BASE_URL}/v1/gpt`,
  REQUEST: {
    TIMEOUT: 1000,
  },
};

export const logApiResponse = (response: any) => {
  // if (response?.status > 400) {
  console.error(
    `API Error: ${response.config.method} ${response.config.url} - Status: ${response.status}, Data: ${JSON.stringify(response.data)}, Request: ${JSON.stringify(response.config.data)}
    Response: ${JSON.stringify(response)}`
  );
  // }
};

const isTokenExpired = (token: string) => {
  const decoded: any = jwtDecode(token);
  const expirationTime = decoded.exp * 1000; // seconds to milliseconds
  return Date.now() >= expirationTime;
};

export const initializeClient = () => {
  client.setConfig({
    baseURL: API_BASE_URL,
    timeout: Config.REQUEST.TIMEOUT,
  });

  client.instance.interceptors.request.use((config) => {
    // console.log("Sending request to ", config.baseURL, config.url);
    const accessToken = localStorage.getItem("access_token") || "";
    if (accessToken) {
      if (isTokenExpired(accessToken)) {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
        return Promise.reject("Token expired. Redirecting to login.");
      }

      config.headers.set("Authorization", `Bearer ${accessToken}`);
    }
    return config;
  });

  client.instance.interceptors.response.use(
    (response) => {
      return response; // Let the response pass if it's successful
    },
    (error) => {
      if (error.response) {
        if ([401, 404].includes(error.response.status)) {
          localStorage.removeItem("access_token");
          window.location.href = "/login";
        }
        logApiResponse(error.response);
      }
      return Promise.reject(error);
    }
  );
};
initializeClient();
