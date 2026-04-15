import { useState, useEffect } from 'react'
import {
  Table, Card, Button, Input, Space, Tag, Modal, Form,
  Select, message, Popconfirm, Drawer, Descriptions, Statistic, Row, Col
} from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { debtorApi } from '@/services/api'
import type { DebtorResponse, DebtorCreate, DebtorUpdate } from '@/types'

function DebtorsPage() {
  const [data, setData] = useState<DebtorResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [modalVisible, setModalVisible] = useState(false)
  const [detailVisible, setDetailVisible] = useState(false)
  const [selectedDebtor, setSelectedDebtor] = useState<DebtorResponse | null>(null)
  const [editingDebtor, setEditingDebtor] = useState<DebtorResponse | null>(null)
  const [form] = Form.useForm()
  const { t } = useTranslation()

  useEffect(() => {
    loadData()
  }, [page, pageSize, statusFilter])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await debtorApi.list({ skip: (page - 1) * pageSize, limit: pageSize, status: statusFilter })
      setData(res.data)
      setTotal(res.data.length)
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPage(1)
    loadData()
  }

  const handleAdd = () => {
    setEditingDebtor(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: DebtorResponse) => {
    setEditingDebtor(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleView = (record: DebtorResponse) => {
    setSelectedDebtor(record)
    setDetailVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await debtorApi.delete(id)
      message.success('删除成功')
      loadData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingDebtor) {
        await debtorApi.update(editingDebtor.id, values as DebtorUpdate)
        message.success('更新成功')
      } else {
        await debtorApi.create(values as DebtorCreate)
        message.success('创建成功')
      }
      setModalVisible(false)
      loadData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      active: { color: 'green', text: '正常' },
      overdue: { color: 'orange', text: '逾期' },
      cleared: { color: 'blue', text: '已还清' },
      blacklisted: { color: 'red', text: '黑名单' },
    }
    const config = statusMap[status] || { color: 'default', text: status }
    return <Tag color={config.color}>{config.text}</Tag>
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '债务人编号', dataIndex: 'debtor_number', key: 'debtor_number', width: 150 },
    { title: '姓名', dataIndex: 'name', key: 'name', width: 120 },
    { 
      title: '手机号', 
      dataIndex: 'phone', 
      key: 'phone', 
      width: 140,
      render: (phone: string) => phone ? phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') : '-'
    },
    { 
      title: '欠款金额', 
      dataIndex: 'overdue_amount', 
      key: 'overdue_amount', 
      width: 120,
      render: (amount: number) => amount ? `¥${amount.toLocaleString()}` : '-'
    },
    { 
      title: '逾期天数', 
      dataIndex: 'overdue_days', 
      key: 'overdue_days', 
      width: 100,
      render: (days: number) => days ? `${days}天` : '-'
    },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: getStatusTag },
    { 
      title: '创建时间', 
      dataIndex: 'created_at', 
      key: 'created_at', 
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: DebtorResponse) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
            查看
          </Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={<h2 style={{ margin: 0 }}>债务人管理</h2>}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增债务人
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        <Space style={{ marginBottom: 16 }} wrap>
          <Input.Search
            placeholder="搜索手机号/姓名/债务人编号"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 280 }}
            allowClear
          />
          <Select
            placeholder="状态筛选"
            value={statusFilter}
            onChange={(value) => { setStatusFilter(value); setPage(1); }}
            style={{ width: 120 }}
            allowClear
          >
            <Select.Option value="active">正常</Select.Option>
            <Select.Option value="overdue">逾期</Select.Option>
            <Select.Option value="cleared">已还清</Select.Option>
            <Select.Option value="blacklisted">黑名单</Select.Option>
          </Select>
          <Button icon={<SearchOutlined />} onClick={handleSearch}>搜索</Button>
        </Space>

        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps || 20); },
          }}
        />
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        title={editingDebtor ? '编辑债务人' : '新增债务人'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="debtor_number" label="债务人编号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="手机号">
            <Input />
          </Form.Item>
          <Form.Item name="id_card" label="身份证号">
            <Input />
          </Form.Item>
          <Form.Item name="overdue_amount" label="欠款金额">
            <Input type="number" />
          </Form.Item>
          <Form.Item name="overdue_days" label="逾期天数">
            <Input type="number" />
          </Form.Item>
          <Form.Item name="status" label="状态" initialValue="active">
            <Select>
              <Select.Option value="active">正常</Select.Option>
              <Select.Option value="overdue">逾期</Select.Option>
              <Select.Option value="cleared">已还清</Select.Option>
              <Select.Option value="blacklisted">黑名单</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit">保存</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Detail Drawer */}
      <Drawer
        title="债务人详情"
        open={detailVisible}
        onClose={() => setDetailVisible(false)}
        width={600}
      >
        {selectedDebtor && (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Statistic title="欠款金额" value={selectedDebtor.overdue_amount || 0} prefix="¥" />
              </Col>
              <Col span={12}>
                <Statistic title="逾期天数" value={selectedDebtor.overdue_days || 0} suffix="天" />
              </Col>
            </Row>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="ID">{selectedDebtor.id}</Descriptions.Item>
              <Descriptions.Item label="债务人编号">{selectedDebtor.debtor_number}</Descriptions.Item>
              <Descriptions.Item label="姓名">{selectedDebtor.name}</Descriptions.Item>
              <Descriptions.Item label="手机号">{selectedDebtor.phone}</Descriptions.Item>
              <Descriptions.Item label="身份证号">{selectedDebtor.id_card}</Descriptions.Item>
              <Descriptions.Item label="邮箱">{selectedDebtor.email}</Descriptions.Item>
              <Descriptions.Item label="开户行">{selectedDebtor.bank_name}</Descriptions.Item>
              <Descriptions.Item label="银行账号">{selectedDebtor.bank_account}</Descriptions.Item>
              <Descriptions.Item label="账户名">{selectedDebtor.bank_account_name}</Descriptions.Item>
              <Descriptions.Item label="地址">{selectedDebtor.address}</Descriptions.Item>
              <Descriptions.Item label="状态">{getStatusTag(selectedDebtor.status)}</Descriptions.Item>
              <Descriptions.Item label="备注">{selectedDebtor.remark}</Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {new Date(selectedDebtor.created_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {new Date(selectedDebtor.updated_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
            </Descriptions>
          </>
        )}
      </Drawer>
    </div>
  )
}

export default DebtorsPage
