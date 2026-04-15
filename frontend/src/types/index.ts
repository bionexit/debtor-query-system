// ============ Enums ============
export enum UserRole {
  ADMIN = 'admin',
  OPERATOR = 'operator',
  VIEWER = 'viewer',
}

export enum DebtorStatus {
  ACTIVE = 'active',
  BLACKLISTED = 'blacklisted',
  CLEARED = 'cleared',
  OVERDUE = 'overdue',
  LEGAL = 'legal',
}

export enum BatchStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum VoucherStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

export enum SMSTaskStatus {
  PENDING = 'pending',
  SENT = 'sent',
  FAILED = 'failed',
  DELIVERED = 'delivered',
}

export enum ChannelStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  TESTING = 'testing',
}

// ============ Auth Types ============
export interface LoginRequest {
  username: string
  password: string
  captcha_key?: string
  captcha_value?: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

export interface UserInfo {
  id: number
  username: string
  email: string
  role: UserRole
  is_active: boolean
  is_superadmin?: boolean
  created_at?: string
}

export interface H5TokenRequest {
  phone: string
  sms_code: string
}

export interface H5TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  expires_days?: number
}

// ============ Debtor Types ============
export interface DebtorBase {
  debtor_number: string
  name: string
  id_card?: string
  phone?: string
  email?: string
  bank_name?: string
  bank_account?: string
  bank_account_name?: string
  address?: string
  remark?: string
  status: DebtorStatus
  overdue_amount?: number
  overdue_days?: number
}

export interface DebtorCreate extends DebtorBase {
  batch_id?: number
}

export interface DebtorUpdate {
  name?: string
  id_card?: string
  phone?: string
  email?: string
  bank_name?: string
  bank_account?: string
  bank_account_name?: string
  address?: string
  remark?: string
  status?: DebtorStatus
  overdue_amount?: number
  overdue_days?: number
}

export interface DebtorResponse extends DebtorBase {
  id: number
  query_count: number
  last_query_at?: string
  created_at: string
  updated_at: string
  created_by_id?: number
  updated_by_id?: number
}

export interface DebtorQueryRequest {
  debtor_number?: string
  name?: string
  id_card?: string
  phone?: string
}

export interface DebtorQueryResponse {
  debtor_number: string
  name: string
  id_card?: string
  phone?: string
  email?: string
  bank_name?: string
  bank_account?: string
  bank_account_name?: string
  address?: string
  status: DebtorStatus
  overdue_amount: number
  overdue_days: number
}

export interface DebtorStats {
  total_debtors: number
  active_debtors: number
  cleared_debtors: number
  total_overdue_amount: number
  new_debtors_today: number
  new_debtors_this_month: number
}

export interface ImportBatchResponse {
  id: number
  filename: string
  total_count: number
  success_count: number
  fail_count: number
  status: string
  created_at: string
  completed_at?: string
}

export interface QueryLogResponse {
  id: number
  debtor_id: number
  query_type: string
  query_channel: string
  query_ip?: string
  success: boolean
  error_message?: string
  created_at: string
}

// ============ Batch Types ============
export interface BatchBase {
  name: string
  description?: string
}

export interface BatchCreate extends BatchBase {}

export interface BatchUpdate {
  name?: string
  description?: string
  status?: BatchStatus
}

export interface BatchResponse extends BatchBase {
  id: number
  batch_no: string
  status: BatchStatus
  total_count: number
  success_count: number
  fail_count: number
  created_by?: number
  created_at: string
  updated_at: string
}

// ============ Voucher Types ============
export interface VoucherBase {
  file_name: string
  file_path: string
}

export interface VoucherUploadResponse {
  id: number
  file_name: string
  total_count: number
  status: VoucherStatus
  message: string
}

export interface VoucherReviewRequest {
  comment?: string
}

export interface VoucherResponse extends VoucherBase {
  id: number
  file_size?: number
  status: VoucherStatus
  total_count: number
  success_count: number
  fail_count: number
  uploaded_by?: number
  reviewed_by?: number
  reviewed_at?: string
  review_comment?: string
  created_at: string
}

// ============ SMS Types ============
export interface SMSTemplateBase {
  name: string
  content: string
  variables?: string
}

export interface SMSTemplateCreate extends SMSTemplateBase {}

export interface SMSTemplateUpdate {
  name?: string
  content?: string
  variables?: string
  is_active?: boolean
}

export interface SMSTemplateResponse extends SMSTemplateBase {
  id: number
  is_active: boolean
  created_by?: number
  created_at: string
}

export interface SMSTaskCreate {
  template_id: number
  channel_id: number
  phones: string[]
  scheduled_at?: string
}

export interface SMSTaskResponse extends SMSTaskBase {
  id: number
  task_no: string
  status: SMSTaskStatus
  success_count: number
  fail_count: number
  created_by?: number
  created_at: string
}

export interface SMSTaskBase {
  template_id: number
  channel_id: number
  recipient_count: number
  scheduled_at?: string
}

export interface SMSRequest {
  phone: string
  message: string
  sms_type?: string
}

export interface SMSResponse {
  id: number
  phone: string
  message: string
  status: SMSTaskStatus
  provider_message_id?: string
  sent_at: string
  delivered_at?: string
  error_code?: string
  error_message?: string
}

// ============ Partner Types ============
export interface PartnerBase {
  partner_code: string
  partner_name: string
  description?: string
  daily_query_limit?: number
  monthly_query_limit?: number
  allowed_ips?: string[]
}

export interface PartnerCreate extends PartnerBase {}

export interface PartnerUpdate {
  partner_name?: string
  description?: string
  daily_query_limit?: number
  monthly_query_limit?: number
  allowed_ips?: string[]
  status?: string
}

export interface PartnerResponse extends PartnerBase {
  id: number
  status: string
  api_key?: string
  created_at: string
  updated_at: string
  created_by_id?: number
}

// ============ Config Types ============
export interface ConfigBase {
  config_key: string
  config_value: string
  description?: string
}

export interface ConfigCreate extends ConfigBase {}

export interface ConfigUpdate {
  config_value?: string
  description?: string
  is_active?: boolean
}

export interface ConfigChangeLogResponse {
  id: number
  config_id: number
  old_value?: string
  new_value?: string
  changed_by?: number
  change_reason?: string
  created_at: string
}

export interface ConfigResponse extends ConfigBase {
  id: number
  is_active: boolean
  changed_by?: number
  created_at: string
}

// ============ Channel Types ============
export interface ChannelBase {
  name: string
  provider: string
  endpoint?: string
  api_key?: string
}

export interface ChannelCreate extends ChannelBase {
  priority?: number
}

export interface ChannelUpdate {
  name?: string
  endpoint?: string
  api_key?: string
  status?: ChannelStatus
  priority?: number
  is_active?: boolean
}

export interface ChannelTestRequest {
  phone: string
}

export interface ChannelResponse extends ChannelBase {
  id: number
  status: ChannelStatus
  priority: number
  success_rate: number
  avg_response_time: number
  is_active: boolean
  created_at: string
}

// ============ Import Types ============
export interface ImportRequest {
  batch_id: number
  file_path: string
}

export interface ImportResponse {
  batch_id: number
  total_count: number
  success_count: number
  fail_count: number
  errors: string[]
}

// ============ Captcha Types ============
export interface CaptchaResponse {
  captcha_key: string
  image: string
}

export interface CaptchaVerifyRequest {
  captcha_key: string
  captcha_value: string
}

// ============ H5 Types ============
export interface H5DebtInfoRequest {
  debtor_id_card: string
}

export interface DebtInfoResponse {
  debtor_id: number
  name: string
  id_card: string
  phone: string
  debt_amount: number
  status: string
  query_time: string
}

export interface PaymentAccountResponse {
  bank_name: string
  account_no: string
  account_name: string
  bank_code?: string
}

// ============ Statistics Types ============
export interface StatisticsQuery {
  start_date?: string
  end_date?: string
  batch_id?: number
  partner_id?: number
}

export interface DebtStatistics {
  total_debtors: number
  total_cases: number
  total_amount: number
  new_debtors_this_month: number
  new_amount_this_month: number
  debt_distribution_by_batch: Array<{
    batch_name: string
    debtor_count: number
    case_count: number
    total_amount: number
  }>
  debt_distribution_by_range: Array<{
    range: string
    count: number
    amount: number
  }>
}

export interface RepaymentStatistics {
  total_repaid_count: number
  total_repaid_amount: number
  repayment_rate: number
  distribution_by_batch: Array<{
    batch_name: string
    repaid_count: number
    repaid_amount: number
  }>
}

export interface SMSStatistics {
  total_sent: number
  success_count: number
  fail_count: number
  success_rate: number
  distribution_by_batch: Array<{
    batch_name: string
    sent_count: number
    success_count: number
  }>
}

// ============ API Response Types ============
export interface ApiResponse<T> {
  data: T
  message?: string
  code?: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}

export interface ApiError {
  detail: string
  message?: string
  code?: string
}

// ============ Form Types ============
export interface PaginationParams {
  page?: number
  page_size?: number
  skip?: number
  limit?: number
}

export interface ListQueryParams extends PaginationParams {
  status?: string
  keyword?: string
  start_date?: string
  end_date?: string
}
