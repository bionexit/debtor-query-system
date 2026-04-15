import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, Space, Button } from 'antd'
import {
  DashboardOutlined,
  UserOutlined,
  TeamOutlined,
  SolutionOutlined,
  FileTextOutlined,
  ApiOutlined,
  ImportOutlined,
  BarChartOutlined,
  SettingOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  MessageOutlined,
  DatabaseOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '@/store/auth'
import { adminAuthApi } from '@/services/api'

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/batches', icon: <SolutionOutlined />, label: '委案批次管理' },
  { key: '/debtors', icon: <TeamOutlined />, label: '债务人管理' },
  { key: '/vouchers', icon: <FileTextOutlined />, label: '凭证审核' },
  { key: '/sms/templates', icon: <MessageOutlined />, label: '短信模板管理' },
  { key: '/sms/channels', icon: <ApiOutlined />, label: '短信渠道管理' },
  { key: '/import', icon: <ImportOutlined />, label: '数据导入' },
  { key: '/statistics', icon: <BarChartOutlined />, label: '数据报表' },
  { key: '/partners', icon: <ApiOutlined />, label: '合作方管理' },
  { key: '/configs', icon: <SettingOutlined />, label: '配置管理' },
]

function AdminLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const { user, logout } = useAuthStore()

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  const handleLogout = async () => {
    try {
      await adminAuthApi.logout()
    } catch (e) {
      // Ignore logout API errors
    }
    logout()
    navigate('/login')
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        theme="light"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          borderRight: '1px solid #f0f0f0',
        }}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? 0 : '0 16px',
          borderBottom: '1px solid #f0f0f0',
        }}>
          {collapsed ? (
            <DatabaseOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          ) : (
            <span style={{ fontSize: 16, fontWeight: 600, color: '#1890ff' }}>
              还款账号查询系统
            </span>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0, marginTop: 8 }}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }}>
        <Header style={{ 
          padding: '0 24px', 
          background: '#fff', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16, width: 64, height: 64 }}
          />
          <Space size={16}>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
                <span>{user?.username || 'Admin'}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ margin: 24, minHeight: 280, background: '#fff' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default AdminLayout
