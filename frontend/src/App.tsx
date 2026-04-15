import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import AdminLayout from '@/layouts/AdminLayout'
import LoginPage from '@/pages/admin/Login'
import DashboardPage from '@/pages/admin/Dashboard'
import DebtorsPage from '@/pages/admin/Debtors'
import BatchesPage from '@/pages/admin/Batches'
import VouchersPage from '@/pages/admin/Vouchers'
import SMSTemplatesPage from '@/pages/admin/SMSTemplates'
import SMSChannelsPage from '@/pages/admin/SMSChannels'
import ImportPage from '@/pages/admin/Import'
import ImportResultPage from '@/pages/admin/ImportResult'
import StatisticsPage from '@/pages/admin/Statistics'
import PartnersPage from '@/pages/admin/Partners'
import ConfigsPage from '@/pages/admin/Configs'
import H5Layout from '@/layouts/H5Layout'
import H5VerifyPage from '@/pages/h5/Verify'
import H5DebtInfoPage from '@/pages/h5/DebtInfo'
import H5VoucherUploadPage from '@/pages/h5/VoucherUpload'
import H5VoucherResultPage from '@/pages/h5/VoucherResult'

// Protected route wrapper for admin
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

// H5 Route wrapper (no auth required for verify page)
function H5Route({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}

function App() {
  return (
    <Routes>
      {/* Admin Routes */}
      <Route path="/login" element={<LoginPage />} />
      
      <Route path="/" element={
        <ProtectedRoute>
          <AdminLayout />
        </ProtectedRoute>
      }>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="debtors" element={<DebtorsPage />} />
        <Route path="batches" element={<BatchesPage />} />
        <Route path="vouchers" element={<VouchersPage />} />
        <Route path="sms/templates" element={<SMSTemplatesPage />} />
        <Route path="sms/channels" element={<SMSChannelsPage />} />
        <Route path="import" element={<ImportPage />} />
        <Route path="import/result" element={<ImportResultPage />} />
        <Route path="statistics" element={<StatisticsPage />} />
        <Route path="partners" element={<PartnersPage />} />
        <Route path="configs" element={<ConfigsPage />} />
      </Route>
      
      {/* H5 Routes */}
      <Route path="/h5" element={<H5Layout />}>
        <Route path="verify" element={<H5VerifyPage />} />
        <Route path="debt-info" element={<H5DebtInfoPage />} />
        <Route path="voucher/upload" element={<H5VoucherUploadPage />} />
        <Route path="voucher/result" element={<H5VoucherResultPage />} />
      </Route>
    </Routes>
  )
}

export default App
