import { useState, useEffect } from 'react'
import { Table, Card, Button, Space, Tag, Modal, Form, Input, Select, Switch, message, Popconfirm, Statistic, Row, Col } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, StopOutlined, ExperimentOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { channelApi } from '@/services/api'
import type { ChannelResponse } from '@/types'

function SMSChannelsPage() {
  const [data, setData] = useState<ChannelResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [testModalVisible, setTestModalVisible] = useState(false)
  const [editingChannel, setEditingChannel] = useState<ChannelResponse | null>(null)
  const [testingChannel, setTestingChannel] = useState<ChannelResponse | null>(null)
  const [form] = Form.useForm()
  const [testForm] = Form.useForm()
  const [testPhone, setTestPhone] = useState('')
  const { t } = useTranslation()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await channelApi.list()
      setData(res.data)
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingChannel(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: ChannelResponse) => {
    setEditingChannel(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await channelApi.delete(id)
      message.success('删除成功')
      loadData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleTest = (record: ChannelResponse) => {
    setTestingChannel(record)
    setTestPhone('')
    setTestModalVisible(true)
  }

  const handleToggleStatus = async (record: ChannelResponse) => {
    try {
      if (record.status === 'active') {
        await channelApi.disable(record.id)
        message.success('已禁用')
      } else {
        await channelApi.enable(record.id)
        message.success('已启用')
      }
      loadData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const submitTest = async () => {
    if (!testingChannel || !testPhone) return
    try {
      await channelApi.test(testingChannel.id, { phone: testPhone })
      message.success('测试短信发送成功')
      setTestModalVisible(false)
    } catch (error: any) {
      message.error(error.response?.data?.detail || '测试发送失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingChannel) {
        await channelApi.update(editingChannel.id, values)
        message.success('更新成功')
      } else {
        await channelApi.create(values)
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
      active: { color: 'green', text: '启用' },
      inactive: { color: 'default', text: '禁用' },
      testing: { color: 'processing', text: '测试中' },
    }
    const config = statusMap[status] || { color: 'default', text: status }
    return <Tag color={config.color}>{config.text}</Tag>
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '渠道名称', dataIndex: 'name', key: 'name', width: 150 },
    { title: '提供商', dataIndex: 'provider', key: 'provider', width: 120 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: getStatusTag },
    { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 },
    { 
      title: '成功率', 
      dataIndex: 'success_rate', 
      key: 'success_rate', 
      width: 100,
      render: (rate: number) => `${(rate * 100).toFixed(1)}%`
    },
    { 
      title: '平均响应时间', 
      dataIndex: 'avg_response_time', 
      key: 'avg_response_time', 
      width: 120,
      render: (time: number) => `${time.toFixed(0)}ms`
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: ChannelResponse) => (
        <Space>
          <Button type="link" size="small" icon={<ExperimentOutlined />} onClick={() => handleTest(record)}>
            测试
          </Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            配置
          </Button>
          <Button 
            type="link" 
            size="small" 
            icon={record.status === 'active' ? <StopOutlined /> : <PlayCircleOutlined />} 
            onClick={() => handleToggleStatus(record)}
            style={{ color: record.status === 'active' ? '#ff4d4f' : '#52c41a' }}
          >
            {record.status === 'active' ? '禁用' : '启用'}
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
        title={<h2 style={{ margin: 0 }}>短信渠道管理</h2>}
        extra={
          <Space>
            <Button>扫描目录</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              添加渠道
            </Button>
          </Space>
        }
      >
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic title="渠道总数" value={data.length} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="启用中" value={data.filter(d => d.status === 'active').length} valueStyle={{ color: '#52c41a' }} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="禁用中" value={data.filter(d => d.status === 'inactive').length} valueStyle={{ color: '#ff4d4f' }} />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic title="平均成功率" value={data.length > 0 ? (data.reduce((acc, d) => acc + d.success_rate, 0) / data.length * 100).toFixed(1) : 0} suffix="%" valueStyle={{ color: '#1890ff' }} />
            </Card>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        title={editingChannel ? '编辑渠道' : '添加渠道'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="渠道名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="provider" label="提供商" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="aliyun">阿里云</Select.Option>
              <Select.Option value="tencent">腾讯云</Select.Option>
              <Select.Option value="huawei">华为云</Select.Option>
              <Select.Option value="yunpian">云片</Select.Option>
              <Select.Option value="custom">自定义</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="endpoint" label="接口地址">
            <Input placeholder="https://api.example.com/sms/send" />
          </Form.Item>
          <Form.Item name="api_key" label="API Key">
            <Input.Password />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue={1}>
            <Input type="number" min={1} />
          </Form.Item>
          <Form.Item name="is_active" label="是否启用" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit">保存</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Test Modal */}
      <Modal
        title="测试短信渠道"
        open={testModalVisible}
        onCancel={() => setTestModalVisible(false)}
        onOk={submitTest}
        okText="发送测试"
        cancelText="取消"
      >
        <p>测试渠道: {testingChannel?.name}</p>
        <Form layout="vertical">
          <Form.Item label="测试手机号" required>
            <Input 
              value={testPhone} 
              onChange={(e) => setTestPhone(e.target.value)}
              placeholder="请输入手机号"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SMSChannelsPage
