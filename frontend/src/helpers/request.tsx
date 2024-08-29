import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import { Config } from '@/config/config';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: Config.API_AUTH_URL,
      timeout: Config.REQUEST.TIMEOUT,
    });
  }

  public isAPIError(error: any): error is AxiosError {
    return axios.isAxiosError(error);
  }

  public getClient(): AxiosInstance {
    return this.client;
  }

  public async get(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.client.get(url, config);
  }
  public async post(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.client.post(url, data, config);
  }

  public async put(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.client.put(url, data, config);
  }

  public async delete(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.client.delete(url, config);
  }

  public async patch(url: string, data: any, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.client.patch(url, data, config);
  }

  public async postForm(url: string, data: any, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.client.postForm(url, data, config);
  }

  public async putForm(url: string, data: any, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.client.putForm(url, data, config);
  }

  public async patchForm(url: string, data: any, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.client.patchForm(url, data, config);
  }
  
}

const api = new APIClient();

export default api;