import { useState, useEffect } from 'react'
import { Table, Card, Button, Space, Tag, Modal, Form, Input, Switch, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { smsTemplateApi } from '@/services/api'
import type { SMSTemplateResponse } from '@/types'

function SMSTemplatesPage() {
  const [data, setData] = useState<SMSTemplateResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<SMSTemplateResponse | null>(null)
  const [form] = Form.useForm()
  const { t } = useTranslation()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await smsTemplateApi.list()
      setData(res.data)
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingTemplate(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: SMSTemplateResponse) => {
    setEditingTemplate(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await smsTemplateApi.delete(id)
      message.success('删除成功')
      loadData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingTemplate) {
        await smsTemplateApi.update(editingTemplate.id, values)
        message.success('更新成功')
      } else {
        await smsTemplateApi.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      loadData()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '模板名称', dataIndex: 'name', key: 'name', width: 200 },
    { title: '模板内容', dataIndex: 'content', key: 'content', ellipsis: true },
    { title: '变量', dataIndex: 'variables', key: 'variables', width: 150 },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'default'}>{isActive ? '启用' : '禁用'}</Tag>
      )
    },
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
      render: (_: any, record: SMSTemplateResponse) => (
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
        title={<h2 style={{ margin: 0 }}>短信模板管理</h2>}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新建模板
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
        title={editingTemplate ? '编辑模板' : '新建模板'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="模板名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="content" label="模板内容" rules={[{ required: true }]}>
            <Input.TextArea rows={4} placeholder="支持变量：{姓名}、{链接}、{金额}等" />
          </Form.Item>
          <Form.Item name="variables" label="变量说明">
            <Input placeholder="如: 姓名,链接,金额" />
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
    </div>
  )
}

export default SMSTemplatesPage
