import { Outlet } from 'react-router-dom'
import { NavBar } from 'antd-mobile'
import { useNavigate } from 'react-router-dom'

function H5Layout() {
  const navigate = useNavigate()

  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <NavBar onBack={() => navigate(-1)} />
      <div style={{ padding: '16px' }}>
        <Outlet />
      </div>
    </div>
  )
}

export default H5Layout
