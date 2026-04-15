import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, Checkbox, message } from 'antd'
import { UserOutlined, LockOutlined, SafetyOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { adminAuthApi, captchaApi } from '@/services/api'
import { useAuthStore } from '@/store/auth'

interface LoginForm {
  username: string
  password: string
  captcha_key?: string
  captcha_value?: string
}

function LoginPage() {
  const [form] = Form.useForm<LoginForm>()
  const [loading, setLoading] = useState(false)
  const [captchaLoading, setCaptchaLoading] = useState(false)
  const [captchaImage, setCaptchaImage] = useState('')
  const [captchaKey, setCaptchaKey] = useState('')
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { setAuth } = useAuthStore()

  const loadCaptcha = async () => {
    setCaptchaLoading(true)
    try {
      const res = await captchaApi.generate()
      setCaptchaImage(res.data.image)
      setCaptchaKey(res.data.captcha_key)
    } catch (error) {
      console.error('Failed to load captcha:', error)
    } finally {
      setCaptchaLoading(false)
    }
  }

  const handleSubmit = async (values: LoginForm) => {
    setLoading(true)
    try {
      const res = await adminAuthApi.login({
        username: values.username,
        password: values.password,
      })
      
      // Check if captcha is required
      if (res.data.access_token) {
        setAuth({
          access_token: res.data.access_token,
          token_type: res.data.token_type || 'bearer',
          expires_in: res.data.expires_in || 3600,
          user: res.data.user,
        })
        message.success(t('login.loginSuccess'))
        navigate('/dashboard')
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || t('login.loginFailed')
      message.error(errorMsg)
      if (captchaKey) {
        loadCaptcha()
        form.setFieldValue('captcha_value', '')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    }}>
      <Card
        style={{
          width: 400,
          borderRadius: 12,
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
        }}
        styles={{ body: { padding: '40px 32px' } }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 8, color: '#333' }}>
            {t('common.appName')}
          </h1>
          <p style={{ color: '#666', fontSize: 14 }}>{t('login.subtitle')}</p>
        </div>

        <Form
          form={form}
          onFinish={handleSubmit}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: t('login.usernameRequired') },
            ]}
          >
            <Input
              prefix={<UserOutlined style={{ color: '#bfbfbf' }} />}
              placeholder={t('login.username')}
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: t('login.passwordRequired') },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#bfbfbf' }} />}
              placeholder={t('login.password')}
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item
            name="captcha_value"
            rules={[
              { required: true, message: t('login.captchaRequired') },
            ]}
          >
            <div style={{ display: 'flex', gap: 8 }}>
              <Input
                prefix={<SafetyOutlined style={{ color: '#bfbfbf' }} />}
                placeholder={t('login.captchaPlaceholder')}
                style={{ flex: 1 }}
                maxLength={10}
              />
              {captchaImage ? (
                <img
                  src={captchaImage}
                  alt="captcha"
                  onClick={loadCaptcha}
                  style={{
                    height: 40,
                    cursor: 'pointer',
                    borderRadius: 4,
                    border: '1px solid #d9d9d9',
                  }}
                />
              ) : (
                <Button onClick={loadCaptcha} loading={captchaLoading}>
                  获取验证码
                </Button>
              )}
            </div>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ height: 48, fontSize: 16, borderRadius: 8 }}
            >
              {t('login.loginButton')}
            </Button>
          </Form.Item>

          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <a style={{ marginRight: 16 }}>{t('login.forgotPassword')}</a>
            <span>|</span>
            <a style={{ marginLeft: 16 }}>{t('login.contactUs')}</a>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default LoginPage
