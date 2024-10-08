import { client } from "@/lib/api/services.gen";
import { jwtDecode } from "jwt-decode";

export const Config = {
  API_NETLOC: "http://localhost:5000",
  API_BASE_URL: "http://localhost:5000/v1",
  API_AUTH_URL: "http://localhost:5000/v1/auth",
  REQUEST: {
    TIMEOUT: 1000,
  },
};

const isTokenExpired = (token: string) => {
  const decoded: any = jwtDecode(token);
  const expirationTime = decoded.exp * 1000; // Convert to milliseconds
  return Date.now() >= expirationTime;
};

export const initializeClient = () => {
  client.setConfig({
    baseURL: Config.API_NETLOC,
    timeout: Config.REQUEST.TIMEOUT,
  });

  client.instance.interceptors.request.use((config) => {
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

  // Response interceptor: Handle 401 responses (Unauthorized)
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
      }

      return Promise.reject(error);
    }
  );
};
initializeClient();
