import { useState, useEffect } from 'react'
import { Table, Card, Button, Space, Tag, Modal, Input, message, Image, Drawer } from 'antd'
import { EyeOutlined, CheckOutlined, CloseOutlined, UploadOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { voucherApi } from '@/services/api'
import type { VoucherResponse } from '@/types'

const { TextArea } = Input

function VouchersPage() {
  const [data, setData] = useState<VoucherResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [statusTab, setStatusTab] = useState<'pending' | 'approved' | 'rejected'>('pending')
  const [selectedVoucher, setSelectedVoucher] = useState<VoucherResponse | null>(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [reviewComment, setReviewComment] = useState('')
  const [reviewModalVisible, setReviewModalVisible] = useState(false)
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject'>('approve')
  const { t } = useTranslation()

  useEffect(() => {
    loadData()
  }, [statusTab])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await voucherApi.list({ status: statusTab })
      setData(res.data)
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleView = (record: VoucherResponse) => {
    setSelectedVoucher(record)
    setDetailVisible(true)
  }

  const handleReview = (record: VoucherResponse, action: 'approve' | 'reject') => {
    setSelectedVoucher(record)
    setReviewAction(action)
    setReviewComment('')
    setReviewModalVisible(true)
  }

  const submitReview = async () => {
    if (!selectedVoucher) return
    try {
      if (reviewAction === 'approve') {
        await voucherApi.approve(selectedVoucher.id, { comment: reviewComment })
        message.success('审核通过')
      } else {
        await voucherApi.reject(selectedVoucher.id, { comment: reviewComment })
        message.success('已拒绝')
      }
      setReviewModalVisible(false)
      loadData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'orange', text: '待审核' },
      approved: { color: 'green', text: '已通过' },
      rejected: { color: 'red', text: '已拒绝' },
    }
    const config = statusMap[status] || { color: 'default', text: status }
    return <Tag color={config.color}>{config.text}</Tag>
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '文件名', dataIndex: 'file_name', key: 'file_name', ellipsis: true },
    { 
      title: '文件大小', 
      dataIndex: 'file_size', 
      key: 'file_size', 
      width: 100,
      render: (size: number) => size ? `${(size / 1024).toFixed(2)} KB` : '-'
    },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: getStatusTag },
    { 
      title: '成功数/总数', 
      key: 'count',
      width: 120,
      render: (_: any, record: VoucherResponse) => `${record.success_count}/${record.total_count}`
    },
    { 
      title: '提交时间', 
      dataIndex: 'created_at', 
      key: 'created_at', 
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: VoucherResponse) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
            详情
          </Button>
          {statusTab === 'pending' && (
            <>
              <Button type="link" size="small" icon={<CheckOutlined />} onClick={() => handleReview(record, 'approve')} style={{ color: '#52c41a' }}>
                通过
              </Button>
              <Button type="link" size="small" icon={<CloseOutlined />} onClick={() => handleReview(record, 'reject')} danger>
                拒绝
              </Button>
            </>
          )}
        </Space>
      )
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={<h2 style={{ margin: 0 }}>凭证审核</h2>}
        extra={<Button type="primary" icon={<UploadOutlined />}>上传凭证</Button>}
      >
        <Space style={{ marginBottom: 16 }}>
          <Button type={statusTab === 'pending' ? 'primary' : 'default'} onClick={() => setStatusTab('pending')}>
            待审核
          </Button>
          <Button type={statusTab === 'approved' ? 'primary' : 'default'} onClick={() => setStatusTab('approved')}>
            已通过
          </Button>
          <Button type={statusTab === 'rejected' ? 'primary' : 'default'} onClick={() => setStatusTab('rejected')}>
            已拒绝
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* Detail Drawer */}
      <Drawer
        title="凭证详情"
        open={detailVisible}
        onClose={() => setDetailVisible(false)}
        width={600}
      >
        {selectedVoucher && (
          <>
            <h4>基本信息</h4>
            <p><strong>凭证ID:</strong> {selectedVoucher.id}</p>
            <p><strong>文件名:</strong> {selectedVoucher.file_name}</p>
            <p><strong>文件大小:</strong> {selectedVoucher.file_size ? `${(selectedVoucher.file_size / 1024).toFixed(2)} KB` : '-'}</p>
            <p><strong>状态:</strong> {getStatusTag(selectedVoucher.status)}</p>
            <p><strong>提交时间:</strong> {new Date(selectedVoucher.created_at).toLocaleString('zh-CN')}</p>
            {selectedVoucher.review_comment && (
              <p><strong>审核备注:</strong> {selectedVoucher.review_comment}</p>
            )}
            {selectedVoucher.reviewed_at && (
              <p><strong>审核时间:</strong> {new Date(selectedVoucher.reviewed_at).toLocaleString('zh-CN')}</p>
            )}
          </>
        )}
      </Drawer>

      {/* Review Modal */}
      <Modal
        title={reviewAction === 'approve' ? '审核通过' : '审核拒绝'}
        open={reviewModalVisible}
        onCancel={() => setReviewModalVisible(false)}
        onOk={submitReview}
        okText="确认"
        cancelText="取消"
        okButtonProps={{ danger: reviewAction === 'reject' }}
      >
        <div style={{ marginBottom: 16 }}>
          <label>审核备注:</label>
          <TextArea 
            rows={4} 
            value={reviewComment} 
            onChange={(e) => setReviewComment(e.target.value)}
            placeholder="请输入审核备注（选填）"
          />
        </div>
      </Modal>
    </div>
  )
}

export default VouchersPage
