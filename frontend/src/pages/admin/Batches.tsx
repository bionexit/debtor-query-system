import { useState, useEffect } from 'react'
import { Table, Card, Button, Input, Space, Tag, Modal, Form, Select, message, Popconfirm } from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { batchApi } from '@/services/api'
import type { BatchResponse, BatchCreate, BatchUpdate } from '@/types'

function BatchesPage() {
  const [data, setData] = useState<BatchResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingBatch, setEditingBatch] = useState<BatchResponse | null>(null)
  const [form] = Form.useForm()
  const { t } = useTranslation()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await batchApi.list()
      setData(res.data)
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingBatch(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: BatchResponse) => {
    setEditingBatch(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await batchApi.delete(id)
      message.success('删除成功')
      loadData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingBatch) {
        await batchApi.update(editingBatch.id, values as BatchUpdate)
        message.success('更新成功')
      } else {
        await batchApi.create(values as BatchCreate)
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
      pending: { color: 'default', text: '待处理' },
      processing: { color: 'processing', text: '处理中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' },
    }
    const config = statusMap[status] || { color: 'default', text: status }
    return <Tag color={config.color}>{config.text}</Tag>
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '批次编号', dataIndex: 'batch_no', key: 'batch_no', width: 150 },
    { title: '批次名称', dataIndex: 'name', key: 'name', width: 200 },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '债务人数', dataIndex: 'total_count', key: 'total_count', width: 100 },
    { title: '成功数', dataIndex: 'success_count', key: 'success_count', width: 100 },
    { title: '失败数', dataIndex: 'fail_count', key: 'fail_count', width: 100 },
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
      width: 150,
      render: (_: any, record: BatchResponse) => (
        <Space>
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
        title={<h2 style={{ margin: 0 }}>委案批次管理</h2>}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新建批次
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={editingBatch ? '编辑批次' : '新建批次'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="批次名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
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
    </div>
  )
}

export default BatchesPage
