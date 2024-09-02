import { createClient } from "@hey-api/client-axios";

export const Config = {
  API_NETLOC: "http://localhost:5000",
  API_BASE_URL: "http://localhost:5000/v1",
  API_AUTH_URL: "http://localhost:5000/v1/auth",
  REQUEST: {
    TIMEOUT: 1000,
  },
};

const client = createClient({
  baseURL: Config.API_NETLOC, 
  timeout: Config.REQUEST.TIMEOUT,
});
