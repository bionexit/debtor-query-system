import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { message } from 'antd'
import { useAuthStore } from '@/store/auth'

const BASE_URL = '/api'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status
      const data = error.response.data as any
      
      if (status === 401) {
        // Unauthorized - clear auth and redirect to login
        useAuthStore.getState().logout()
        window.location.href = '/login'
        message.error('登录已过期，请重新登录')
      } else if (status === 403) {
        message.error(data?.detail || '没有权限访问')
      } else if (status === 404) {
        message.error(data?.detail || '资源不存在')
      } else if (status === 400) {
        message.error(data?.detail || '请求参数错误')
      } else if (status >= 500) {
        message.error('服务器错误，请稍后重试')
      }
    } else if (error.request) {
      message.error('网络连接失败，请检查网络')
    } else {
      message.error('请求失败，请稍后重试')
    }
    return Promise.reject(error)
  }
)

export default api

// ============ Auth API ============
export const authApi = {
  login: (data: { username: string; password: string; captcha_key?: string; captcha_value?: string }) =>
    api.post('/auth/login', data),
  
  logout: () => api.post('/auth/logout'),
  
  getMe: () => api.get('/auth/me'),
  
  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post('/auth/change-password', data),
  
  getH5Token: (data: { phone: string; sms_code: string }) =>
    api.post('/auth/h5/token', data),
  
  resetPasswordRequest: (phone: string) =>
    api.post('/auth/password/reset', null, { params: { phone } }),
  
  resetPasswordConfirm: (data: { phone: string; sms_code: string; new_password: string }) =>
    api.post('/auth/password/reset/confirm', data),
}

// ============ Admin Auth API ============
export const adminAuthApi = {
  login: (data: { username: string; password: string }) =>
    api.post('/admin/auth/login', data),
  
  logout: () => api.post('/admin/auth/logout'),
  
  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post('/admin/auth/change-password', data),
  
  unlockUser: (userId: number) => api.post(`/admin/auth/unlock/${userId}`),
  
  listUsers: (params?: { skip?: number; limit?: number }) =>
    api.get('/admin/auth/users', { params }),
  
  getUser: (userId: number) => api.get(`/admin/auth/users/${userId}`),
  
  createUser: (data: { username: string; email: string; password: string; role?: string }) =>
    api.post('/admin/auth/users', data),
  
  updateUser: (userId: number, data: { email?: string; role?: string; is_active?: boolean }) =>
    api.put(`/admin/auth/users/${userId}`, data),
  
  deleteUser: (userId: number) => api.delete(`/admin/auth/users/${userId}`),
}

// ============ Captcha API ============
export const captchaApi = {
  generate: () => api.get('/captcha/generate'),
  
  verify: (data: { captcha_key: string; captcha_value: string }) =>
    api.post('/captcha/verify', data),
}

// ============ Debtor API ============
export const debtorApi = {
  list: (params?: { skip?: number; limit?: number; status?: string }) =>
    api.get('/debtors/', { params }),
  
  get: (debtorId: number) => api.get(`/debtors/${debtorId}`),
  
  create: (data: any) => api.post('/debtors/', data),
  
  update: (debtorId: number, data: any) => api.put(`/debtors/${debtorId}`, data),
  
  delete: (debtorId: number) => api.delete(`/debtors/${debtorId}`),
  
  getPhone: (debtorId: number) => api.get(`/debtors/${debtorId}/phone`),
  
  getStats: () => api.get('/debtors/stats'),
  
  getQueryLogs: (debtorId: number, params?: { skip?: number; limit?: number }) =>
    api.get(`/debtors/${debtorId}/query-logs`, { params }),
  
  import: (formData: FormData) =>
    api.post('/debtors/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  getImportHistory: (params?: { skip?: number; limit?: number }) =>
    api.get('/debtors/imports/history', { params }),
}

// ============ Batch API ============
export const batchApi = {
  list: (params?: { skip?: number; limit?: number; status?: string; created_by?: number }) =>
    api.get('/batches/', { params }),
  
  get: (batchId: number) => api.get(`/batches/${batchId}`),
  
  create: (data: { name: string; description?: string }) =>
    api.post('/batches/', data),
  
  update: (batchId: number, data: { name?: string; description?: string; status?: string }) =>
    api.put(`/batches/${batchId}`, data),
  
  delete: (batchId: number) => api.delete(`/batches/${batchId}`),
}

// ============ Voucher API ============
export const voucherApi = {
  list: (params?: { skip?: number; limit?: number; status?: string; uploaded_by?: number }) =>
    api.get('/vouchers/', { params }),
  
  get: (voucherId: number) => api.get(`/vouchers/${voucherId}`),
  
  upload: (formData: FormData) =>
    api.post('/vouchers/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  approve: (voucherId: number, data?: { comment?: string }) =>
    api.post(`/vouchers/${voucherId}/approve`, data),
  
  reject: (voucherId: number, data?: { comment?: string }) =>
    api.post(`/vouchers/${voucherId}/reject`, data),
  
  delete: (voucherId: number) => api.delete(`/vouchers/${voucherId}`),
}

// ============ SMS API ============
export const smsApi = {
  send: (data: { phone: string; message: string; sms_type?: string }) =>
    api.post('/sms/send', data),
  
  get: (smsId: number) => api.get(`/sms/${smsId}`),
  
  getStatus: (smsId: number) => api.get(`/sms/${smsId}/status`),
  
  list: (params?: { skip?: number; limit?: number; status?: string; sms_type?: string }) =>
    api.get('/sms/', { params }),
  
  callback: (data: any) => api.post('/sms/callback', data),
}

// ============ SMS Template API ============
export const smsTemplateApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get('/sms/templates/', { params }),
  
  get: (templateId: number) => api.get(`/sms/templates/${templateId}`),
  
  create: (data: { name: string; content: string; variables?: string }) =>
    api.post('/sms/templates/', data),
  
  update: (templateId: number, data: { name?: string; content?: string; variables?: string; is_active?: boolean }) =>
    api.put(`/sms/templates/${templateId}`, data),
  
  delete: (templateId: number) => api.delete(`/sms/templates/${templateId}`),
}

// ============ Channel API ============
export const channelApi = {
  list: (params?: { skip?: number; limit?: number; status?: string; is_active?: boolean }) =>
    api.get('/channels/', { params }),
  
  get: (channelId: number) => api.get(`/channels/${channelId}`),
  
  create: (data: { name: string; provider: string; endpoint?: string; api_key?: string; priority?: number }) =>
    api.post('/channels/', data),
  
  update: (channelId: number, data: { name?: string; endpoint?: string; api_key?: string; status?: string; priority?: number; is_active?: boolean }) =>
    api.put(`/channels/${channelId}`, data),
  
  test: (channelId: number, data: { phone: string }) =>
    api.post(`/channels/${channelId}/test`, data),
  
  enable: (channelId: number) => api.post(`/channels/${channelId}/enable`),
  
  disable: (channelId: number) => api.post(`/channels/${channelId}/disable`),
  
  delete: (channelId: number) => api.delete(`/channels/${channelId}`),
}

// ============ Partner API ============
export const partnerApi = {
  list: (params?: { skip?: number; limit?: number; status?: string }) =>
    api.get('/partners/', { params }),
  
  get: (partnerId: number) => api.get(`/partners/${partnerId}`),
  
  create: (data: { partner_code: string; partner_name: string; description?: string; daily_query_limit?: number; monthly_query_limit?: number; allowed_ips?: string[] }) =>
    api.post('/partners/', data),
  
  update: (partnerId: number, data: { partner_name?: string; description?: string; daily_query_limit?: number; monthly_query_limit?: number; allowed_ips?: string[]; status?: string }) =>
    api.put(`/partners/${partnerId}`, data),
  
  regenerateKey: (partnerId: number) => api.post(`/partners/${partnerId}/regenerate-key`),
  
  delete: (partnerId: number) => api.delete(`/partners/${partnerId}`),
}

// ============ Config API ============
export const configApi = {
  list: (params?: { skip?: number; limit?: number; is_active?: boolean }) =>
    api.get('/configs/', { params }),
  
  get: (configId: number) => api.get(`/configs/${configId}`),
  
  create: (data: { config_key: string; config_value: string; description?: string }) =>
    api.post('/configs/', data),
  
  update: (configId: number, data: { config_value?: string; description?: string; is_active?: boolean }) =>
    api.put(`/configs/${configId}`, data),
  
  delete: (configId: number) => api.delete(`/configs/${configId}`),
  
  getChangeLogs: (configId: number, params?: { skip?: number; limit?: number }) =>
    api.get(`/configs/${configId}/change-logs`, { params }),
}

// ============ Import API ============
export const importApi = {
  importExcel: (batchId: number, formData: FormData) =>
    api.post(`/import/excel?batch_id=${batchId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  validateExcel: (formData: FormData) =>
    api.post('/import/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ============ H5 API ============
export const h5Api = {
  queryDebtors: (params: { debtor_number?: string; name?: string; id_card?: string; page?: number; page_size?: number }) =>
    api.get('/h5/query', { params }),
  
  getDebtor: (debtorNumber: string) => api.get(`/h5/debtor/${debtorNumber}`),
  
  getStats: () => api.get('/h5/stats'),
}

// ============ Statistics API ============
export const statisticsApi = {
  getDebtStats: (params?: { start_date?: string; end_date?: string; batch_id?: number; partner_id?: number }) =>
    api.get('/statistics/debt', { params }),
  
  getRepaymentStats: (params?: { start_date?: string; end_date?: string; batch_id?: number; partner_id?: number }) =>
    api.get('/statistics/repayment', { params }),
  
  getSMSStats: (params?: { start_date?: string; end_date?: string; batch_id?: number; partner_id?: number }) =>
    api.get('/statistics/sms', { params }),
  
  exportDebtReport: (params: { start_date?: string; end_date?: string; batch_id?: number; format?: string }) =>
    api.get('/statistics/export/debt', { params, responseType: 'blob' }),
  
  exportRepaymentReport: (params: { start_date?: string; end_date?: string; batch_id?: number; format?: string }) =>
    api.get('/statistics/export/repayment', { params, responseType: 'blob' }),
  
  exportSMSReport: (params: { start_date?: string; end_date?: string; batch_id?: number; format?: string }) =>
    api.get('/statistics/export/sms', { params, responseType: 'blob' }),
}

// ============ Dashboard API ============
export const dashboardApi = {
  getOverview: () => api.get('/dashboard/overview'),
  
  getRecentVouchers: (params?: { limit?: number }) =>
    api.get('/dashboard/recent-vouchers', { params }),
  
  getRecentImports: (params?: { limit?: number }) =>
    api.get('/dashboard/recent-imports', { params }),
}
