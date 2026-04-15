import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Table, Button, Space, Tag } from 'antd'
import {
  TeamOutlined,
  PlusOutlined,
  FileTextOutlined,
  DollarOutlined,
  AppstoreOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { debtorApi, voucherApi, dashboardApi } from '@/services/api'
import type { DebtorStats, VoucherResponse } from '@/types'

const { Meta } = Card

function DashboardPage() {
  const [stats, setStats] = useState<DebtorStats | null>(null)
  const [recentVouchers, setRecentVouchers] = useState<VoucherResponse[]>([])
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { t } = useTranslation()

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      const [statsRes, vouchersRes] = await Promise.all([
        debtorApi.getStats(),
        voucherApi.list({ limit: 5 }),
      ])
      setStats(statsRes.data)
      setRecentVouchers(vouchersRes.data)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const voucherColumns = [
    { title: '凭证ID', dataIndex: 'id', key: 'id' },
    { title: '文件名', dataIndex: 'file_name', key: 'file_name' },
    { title: '状态', dataIndex: 'status', key: 'status', 
      render: (status: string) => (
        <Tag color={status === 'pending' ? 'orange' : status === 'approved' ? 'green' : 'red'}>
          {status === 'pending' ? '待审核' : status === 'approved' ? '已通过' : '已拒绝'}
        </Tag>
      )
    },
    { title: '提交时间', dataIndex: 'created_at', key: 'created_at', 
      render: (date: string) => new Date(date).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: VoucherResponse) => (
        <Button type="link" size="small" onClick={() => navigate('/vouchers')}>
          审核
        </Button>
      )
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24 }}>{t('dashboard.title')}</h1>
      
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading} hoverable onClick={() => navigate('/debtors')}>
            <Statistic
              title={t('dashboard.totalDebtors')}
              value={stats?.total_debtors || 0}
              prefix={<TeamOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading} hoverable onClick={() => navigate('/debtors')}>
            <Statistic
              title={t('dashboard.newDebtorsToday')}
              value={stats?.new_debtors_today || 0}
              prefix={<PlusOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading} hoverable onClick={() => navigate('/vouchers')}>
            <Statistic
              title={t('dashboard.pendingVouchers')}
              value={stats?.active_debtors || 0}
              prefix={<FileTextOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading} hoverable onClick={() => navigate('/batches')}>
            <Statistic
              title={t('dashboard.activeBatches')}
              value={stats?.new_debtors_this_month || 0}
              prefix={<AppstoreOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card 
            title={t('dashboard.quickActions')} 
            extra={<Button type="link" onClick={() => navigate('/debtors')}>{t('dashboard.viewAll')}</Button>}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Row gutter={16}>
                <Col span={8}>
                  <Card 
                    size="small" 
                    hoverable 
                    onClick={() => navigate('/batches')}
                    style={{ textAlign: 'center' }}
                  >
                    <Meta title="批次管理" description="管理委案批次" />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card 
                    size="small" 
                    hoverable 
                    onClick={() => navigate('/debtors')}
                    style={{ textAlign: 'center' }}
                  >
                    <Meta title="债务人管理" description="查看编辑债务人" />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card 
                    size="small" 
                    hoverable 
                    onClick={() => navigate('/sms/templates')}
                    style={{ textAlign: 'center' }}
                  >
                    <Meta title="发送短信" description="管理短信模板" />
                  </Card>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Card 
                    size="small" 
                    hoverable 
                    onClick={() => navigate('/import')}
                    style={{ textAlign: 'center' }}
                  >
                    <Meta title="导入数据" description="Excel批量导入" />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card 
                    size="small" 
                    hoverable 
                    onClick={() => navigate('/statistics')}
                    style={{ textAlign: 'center' }}
                  >
                    <Meta title="导出报表" description="数据统计报表" />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card 
                    size="small" 
                    hoverable 
                    onClick={() => navigate('/vouchers')}
                    style={{ textAlign: 'center' }}
                  >
                    <Meta title="审核凭证" description="审核还款凭证" />
                  </Card>
                </Col>
              </Row>
            </Space>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card 
            title={t('dashboard.recentVouchers')} 
            extra={<Button type="link" onClick={() => navigate('/vouchers')}>{t('dashboard.viewAll')}</Button>}
          >
            <Table
              columns={voucherColumns}
              dataSource={recentVouchers}
              rowKey="id"
              pagination={false}
              size="small"
              loading={loading}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default DashboardPage
