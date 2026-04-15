# 债务人付款账户查询系统 - 操作手册

## 目录

1. [系统概述](#系统概述)
2. [系统架构](#系统架构)
3. [环境要求](#环境要求)
4. [安装部署](#安装部署)
5. [配置说明](#配置说明)
6. [模块使用指南](#模块使用指南)
7. [API接口文档](#api接口文档)
8. [安全说明](#安全说明)
9. [故障排除](#故障排除)
10. [常见问题](#常见问题)

---

## 1. 系统概述

### 1.1 系统简介

债务人付款账户查询系统是一个基于FastAPI构建的后端服务系统，用于管理债务人信息和查询付款账户数据。系统支持多渠道访问，包括管理后台API、H5移动端API和第三方合作伙伴API。

### 1.2 主要功能

| 功能模块 | 描述 |
|---------|------|
| 用户管理 | 用户注册、登录、角色权限管理 |
| 债务人管理 | 债务人CRUD操作、批量导入、查询统计 |
| H5 API | 移动端债务查询接口 |
| 合作伙伴API | 第三方系统对接接口 |
| 短信服务 | 验证码发送、通知短信 |
| 渠道管理 | SMS渠道配置和管理 |
| 凭证管理 | 凭证文件上传和审核 |
| 批次管理 | 批量操作任务管理 |

### 1.3 技术栈

- **框架**: FastAPI >= 0.100.0
- **数据库**: SQLAlchemy >= 2.0.0 (默认SQLite)
- **认证**: JWT (python-jose)
- **密码加密**: passlib[bcrypt]
- **Excel处理**: openpyxl >= 3.1.0
- **HTTP客户端**: httpx >= 0.25.0
- **服务器**: Uvicorn

---

## 2. 系统架构

### 2.1 目录结构

```
debtor-query-system/
├── backend/
│   ├── app/
│   │   ├── api/                    # API路由
│   │   │   ├── auth.py             # 认证接口
│   │   │   ├── users.py            # 用户管理接口
│   │   │   ├── debtors.py          # 债务人管理接口
│   │   │   ├── h5.py               # H5移动端接口
│   │   │   ├── h5_auth.py          # H5认证接口
│   │   │   ├── partner.py          # 合作伙伴接口
│   │   │   ├── partner_api.py      # 合作伙伴API
│   │   │   ├── partners.py         # 合作伙伴管理
│   │   │   ├── captcha.py          # 验证码接口
│   │   │   ├── sms.py              # 短信接口
│   │   │   ├── channels.py         # 渠道管理
│   │   │   ├── vouchers.py         # 凭证管理
│   │   │   ├── batches.py          # 批次管理
│   │   │   ├── admin_auth.py       # 管理员认证
│   │   │   ├── import_endpoints.py # 导入接口
│   │   │   └── config_endpoints.py # 配置接口
│   │   ├── core/                   # 核心配置
│   │   │   ├── config.py           # 系统配置
│   │   │   ├── database.py         # 数据库连接
│   │   │   └── security.py         # 安全工具
│   │   ├── models/                 # 数据模型
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── services/               # 业务逻辑服务
│   │   └── plugins/                # 插件(SMS等)
│   ├── tests/                      # 单元测试
│   ├── requirements.txt            # Python依赖
│   └── main.py                     # 应用入口
├── sms_mock_server/                # 短信模拟服务器
└── README.md                       # 本文档
```

### 2.2 数据流架构

```
客户端请求
    ↓
[认证层] → JWT Token验证 / API Key验证
    ↓
[业务逻辑层] → Service层处理业务规则
    ↓
[数据访问层] → SQLAlchemy ORM
    ↓
[数据库] → SQLite/PostgreSQL/MySQL
```

---

## 3. 环境要求

### 3.1 硬件要求

- CPU: 2核以上
- 内存: 4GB以上
- 磁盘: 10GB以上可用空间

### 3.2 软件要求

- Python: 3.9+
- pip: 最新版本
- 操作系统: Linux/macOS/Windows

### 3.3 推荐的Python版本

- Python 3.9
- Python 3.10
- Python 3.11

---

## 4. 安装部署

### 4.1 本地开发环境安装

#### 步骤1: 克隆项目

```bash
cd /Users/bion/Documents/Development/xingyun_sms/debtor-query-system
```

#### 步骤2: 创建虚拟环境

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
```

#### 步骤3: 安装依赖

```bash
pip install -r requirements.txt
```

#### 步骤4: 配置环境变量

创建 `.env` 文件：

```env
# 应用配置
APP_NAME=Debtor Query System
VERSION=1.0.0
DEBUG=true

# 数据库配置
DATABASE_URL=sqlite:///./debtor.db

# JWT配置
SECRET_KEY=your-secret-key-change-in-production-use-strong-random-value
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# SMS网关配置
SMS_GATEWAY_URL=http://localhost:8001
SMS_GATEWAY_API_KEY=mock-sms-api-key

# 限流配置
RATE_LIMIT_PER_MINUTE=60

# 验证码配置
CAPTCHA_EXPIRE_SECONDS=300
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# H5 API配置
H5_TOKEN_EXPIRE_DAYS=7
H5_DAILY_QUERY_LIMIT=100

# AES加密密钥 (32字节)
AES_KEY=your-32-byte-aes-encryption-key-h
```

#### 步骤5: 启动开发服务器

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.2 生产环境部署

#### 方案一: 使用Gunicorn

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 方案二: 使用Docker

创建 `Dockerfile`:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行:

```bash
docker build -t debtor-query-system .
docker run -d -p 8000:8000 --env-file .env debtor-query-system
```

#### 方案三: 使用systemd服务 (Linux)

创建服务文件 `/etc/systemd/system/debtor-query.service`:

```ini
[Unit]
Description=Debtor Query System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/backend/venv/bin"
ExecStart=/path/to/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启用服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable debtor-query
sudo systemctl start debtor-query
```

### 4.3 短信模拟服务器部署

系统包含一个短信模拟服务器用于开发和测试:

```bash
cd backend/sms_mock_server
pip install -r requirements.txt
python main.py
```

服务器默认运行在 `http://localhost:8001`

---

## 5. 配置说明

### 5.1 核心配置项

| 配置项 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| APP_NAME | 应用名称 | Debtor Query System | 是 |
| VERSION | 版本号 | 1.0.0 | 是 |
| DEBUG | 调试模式 | true | 是 |
| DATABASE_URL | 数据库连接URL | sqlite:///./debtor.db | 是 |
| SECRET_KEY | JWT密钥 | - | **是** |
| ALGORITHM | JWT算法 | HS256 | 是 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token过期时间(分钟) | 30 | 是 |
| SMS_GATEWAY_URL | 短信网关地址 | http://localhost:8001 | 是 |
| SMS_GATEWAY_API_KEY | 短信网关API密钥 | - | 是 |
| RATE_LIMIT_PER_MINUTE | 每分钟限流次数 | 60 | 是 |
| CAPTCHA_EXPIRE_SECONDS | 验证码有效期(秒) | 300 | 是 |
| MAX_LOGIN_ATTEMPTS | 最大登录尝试次数 | 5 | 是 |
| LOCKOUT_DURATION_MINUTES | 账户锁定时长(分钟) | 15 | 是 |
| H5_TOKEN_EXPIRE_DAYS | H5 Token过期天数 | 7 | 是 |
| H5_DAILY_QUERY_LIMIT | H5每日查询限制 | 100 | 是 |
| AES_KEY | AES加密密钥(32字节) | - | **是** |

### 5.2 数据库配置

#### SQLite (默认/开发环境)

```env
DATABASE_URL=sqlite:///./debtor.db
```

#### PostgreSQL (生产环境)

```env
DATABASE_URL=postgresql://username:password@localhost:5432/debtor_db
```

#### MySQL (生产环境)

```env
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/debtor_db
```

### 5.3 JWT配置说明

SECRET_KEY是用于签名JWT令牌的关键密钥。在生产环境中：

1. 使用强随机值生成器创建密钥
2. 密钥长度至少为32字节
3. 定期更换密钥

生成强随机密钥的方法:

```python
import secrets
print(secrets.token_hex(32))  # 生成64字符的十六进制字符串
```

### 5.4 AES加密配置

AES_KEY必须正好是32字节（用于AES-256加密），用于加密债务人的敏感信息如电话号码:

```python
import os
print(os.urandom(32).hex())  # 生成32字节的十六进制字符串
```

---

## 6. 模块使用指南

### 6.1 用户认证模块

#### 6.1.1 用户登录

**请求示例**:

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password123",
    "captcha_key": "xxx",
    "captcha_value": "1234"
  }'
```

**响应示例**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "superadmin"
  }
}
```

#### 6.1.2 获取当前用户信息

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer <token>"
```

#### 6.1.3 密码重置

请求密码重置验证码:

```bash
curl -X POST "http://localhost:8000/api/auth/password/reset?phone=13800138000"
```

确认重置密码:

```bash
curl -X POST "http://localhost:8000/api/auth/password/reset/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "sms_code": "123456",
    "new_password": "newpassword123"
  }'
```

### 6.2 债务人管理模块

#### 6.2.1 创建债务人

```bash
curl -X POST "http://localhost:8000/api/debtors/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "debtor_number": "D20240001",
    "name": "张三",
    "id_card": "110101199001011234",
    "phone": "13800138000",
    "email": "zhangsan@example.com",
    "bank_name": "中国工商银行",
    "bank_account": "6222021234567890",
    "bank_account_name": "张三",
    "address": "北京市朝阳区xxx",
    "overdue_amount": 50000.00,
    "overdue_days": 90
  }'
```

#### 6.2.2 查询债务人列表

```bash
curl -X GET "http://localhost:8000/api/debtors/?skip=0&limit=100&status=active" \
  -H "Authorization: Bearer <token>"
```

#### 6.2.3 获取债务人详情

```bash
curl -X GET "http://localhost:8000/api/debtors/1" \
  -H "Authorization: Bearer <token>"
```

#### 6.2.4 获取解密后的电话号码

```bash
curl -X GET "http://localhost:8000/api/debtors/1/phone" \
  -H "Authorization: Bearer <token>"
```

#### 6.2.5 批量导入债务人

支持Excel格式(.xlsx, .xls):

```bash
curl -X POST "http://localhost:8000/api/debtors/import" \
  -H "Authorization: Bearer <token>" \
  -F "file=@debtors.xlsx"
```

**Excel文件格式要求**:

| 字段 | 说明 | 必填 |
|------|------|------|
| debtor_number | 债务人编号 | 是 |
| name | 姓名 | 是 |
| id_card | 身份证号 | 是 |
| phone | 电话号码 | 是 |
| email | 电子邮箱 | 否 |
| bank_name | 银行名称 | 否 |
| bank_account | 银行账号 | 否 |
| bank_account_name | 账户名 | 否 |
| address | 地址 | 否 |
| overdue_amount | 逾期金额 | 否 |
| overdue_days | 逾期天数 | 否 |
| remark | 备注 | 否 |

#### 6.2.6 查看导入历史

```bash
curl -X GET "http://localhost:8000/api/debtors/imports/history" \
  -H "Authorization: Bearer <token>"
```

#### 6.2.7 获取债务人统计信息

```bash
curl -X GET "http://localhost:8000/api/debtors/stats" \
  -H "Authorization: Bearer <token>"
```

### 6.3 H5移动端模块

#### 6.3.1 获取H5访问Token

通过短信验证码获取H5访问Token:

```bash
curl -X POST "http://localhost:8000/api/auth/h5/token" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "sms_code": "123456"
  }'
```

#### 6.3.2 H5查询债务人

```bash
curl -X GET "http://localhost:8000/api/h5/query?debtor_number=D20240001&page=1&page_size=20" \
  -H "Authorization: Bearer <h5_token>"
```

#### 6.3.3 H5获取单个债务人详情

```bash
curl -X GET "http://localhost:8000/api/h5/debtor/D20240001" \
  -H "Authorization: Bearer <h5_token>"
```

#### 6.3.4 H5获取统计数据

```bash
curl -X GET "http://localhost:8000/api/h5/stats" \
  -H "Authorization: Bearer <h5_token>"
```

### 6.4 合作伙伴API模块

#### 6.4.1 合作伙伴认证

合作伙伴API使用 `X-API-Key` 头进行认证:

```bash
curl -X GET "http://localhost:8000/api/partner/query?debtor_number=D20240001" \
  -H "X-API-Key: <partner_api_key>"
```

#### 6.4.2 合作伙伴查询债务人

```bash
curl -X GET "http://localhost:8000/api/partner/query?debtor_number=D20240001&name=张三" \
  -H "X-API-Key: <partner_api_key>"
```

#### 6.4.3 获取合作伙伴统计

```bash
curl -X GET "http://localhost:8000/api/partner/stats" \
  -H "X-API-Key: <partner_api_key>"
```

#### 6.4.4 合作伙伴管理 (管理员)

创建合作伙伴:

```bash
curl -X POST "http://localhost:8000/api/partners/" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "partner_code": "P001",
    "partner_name": "测试合作伙伴",
    "description": "测试用合作伙伴",
    "daily_query_limit": 1000,
    "monthly_query_limit": 30000,
    "allowed_ips": ["192.168.1.0/24"]
  }'
```

重新生成API密钥:

```bash
curl -X POST "http://localhost:8000/api/partners/1/regenerate-key" \
  -H "Authorization: Bearer <admin_token>"
```

### 6.5 短信模块

#### 6.5.1 发送短信

```bash
curl -X POST "http://localhost:8000/api/sms/send" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "message": "您的验证码是123456",
    "sms_type": "verification"
  }'
```

#### 6.5.2 查询短信状态

```bash
curl -X GET "http://localhost:8000/api/sms/1/status" \
  -H "Authorization: Bearer <token>"
```

#### 6.5.3 短信回调处理

短信网关回调:

```bash
curl -X POST "http://localhost:8000/api/sms/callback" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "msg_xxx",
    "status": "delivered",
    "delivered_at": "2024-01-01T12:00:00Z"
  }'
```

### 6.6 验证码模块

#### 6.6.1 生成验证码

```bash
curl -X GET "http://localhost:8000/api/captcha/generate"
```

**响应**:

```json
{
  "captcha_key": "xxx",
  "image": "data:image/png;base64,..."
}
```

#### 6.6.2 验证验证码

```bash
curl -X POST "http://localhost:8000/api/captcha/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "captcha_key": "xxx",
    "captcha_value": "1234"
  }'
```

### 6.7 渠道管理模块

#### 6.7.1 创建短信渠道

```bash
curl -X POST "http://localhost:8000/api/channels/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "主通道",
    "provider": "aliyun",
    "endpoint": "https://dysmsapi.aliyuncs.com",
    "api_key": "your-api-key",
    "priority": 1
  }'
```

#### 6.7.2 测试渠道

```bash
curl -X POST "http://localhost:8000/api/channels/1/test" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000"}'
```

#### 6.7.3 启用/禁用渠道

启用:

```bash
curl -X POST "http://localhost:8000/api/channels/1/enable" \
  -H "Authorization: Bearer <token>"
```

禁用:

```bash
curl -X POST "http://localhost:8000/api/channels/1/disable" \
  -H "Authorization: Bearer <token>"
```

### 6.8 凭证管理模块

#### 6.8.1 上传凭证

```bash
curl -X POST "http://localhost:8000/api/vouchers/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@voucher.xlsx"
```

#### 6.8.2 审核凭证

批准:

```bash
curl -X POST "http://localhost:8000/api/vouchers/1/approve" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"comment": "审核通过"}'
```

拒绝:

```bash
curl -X POST "http://localhost:8000/api/vouchers/1/reject" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"comment": "格式不正确"}'
```

### 6.9 批次管理模块

#### 6.9.1 创建批次

```bash
curl -X POST "http://localhost:8000/api/batches/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "2024年第一批",
    "description": "2024年1月债务人批次"
  }'
```

#### 6.9.2 查询批次列表

```bash
curl -X GET "http://localhost:8000/api/batches/?skip=0&limit=100" \
  -H "Authorization: Bearer <token>"
```

---

## 7. API接口文档

### 7.1 认证相关接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | /api/auth/login | 用户登录 | 否 |
| POST | /api/auth/logout | 用户登出 | 是 |
| GET | /api/auth/me | 获取当前用户信息 | 是 |
| POST | /api/auth/h5/token | 获取H5访问Token | 否 |
| POST | /api/auth/password/reset | 请求密码重置 | 否 |
| POST | /api/auth/password/reset/confirm | 确认密码重置 | 否 |

### 7.2 用户管理接口

| 方法 | 路径 | 描述 | 认证 | 权限 |
|------|------|------|------|------|
| GET | /api/users/ | 获取用户列表 | 是 | 管理员 |
| GET | /api/users/{id} | 获取用户详情 | 是 | 管理员/本人 |
| POST | /api/users/ | 创建用户 | 是 | 超级管理员 |
| PUT | /api/users/{id} | 更新用户 | 是 | 管理员/本人 |
| PUT | /api/users/{id}/password | 修改密码 | 是 | 本人 |
| POST | /api/users/{id}/password/reset | 管理员重置密码 | 是 | 超级管理员 |
| DELETE | /api/users/{id} | 删除用户 | 是 | 超级管理员 |

### 7.3 债务人管理接口

| 方法 | 路径 | 描述 | 认证 | 权限 |
|------|------|------|------|------|
| GET | /api/debtors/ | 获取债务人列表 | 是 | 用户 |
| GET | /api/debtors/stats | 获取债务人统计 | 是 | 用户 |
| GET | /api/debtors/{id} | 获取债务人详情 | 是 | 用户 |
| GET | /api/debtors/{id}/phone | 获取解密电话 | 是 | 用户 |
| POST | /api/debtors/ | 创建债务人 | 是 | 用户 |
| PUT | /api/debtors/{id} | 更新债务人 | 是 | 用户 |
| DELETE | /api/debtors/{id} | 删除债务人 | 是 | 用户 |
| POST | /api/debtors/import | 批量导入债务人 | 是 | 用户 |
| GET | /api/debtors/imports/history | 导入历史 | 是 | 用户 |
| GET | /api/debtors/{id}/query-logs | 查询日志 | 是 | 用户 |

### 7.4 H5 API接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | /api/h5/captcha | 请求H5验证码 | 否 |
| POST | /api/h5/verify | 验证H5验证码 | 否 |
| GET | /api/h5/query | H5查询债务人 | H5 Token |
| GET | /api/h5/debtor/{debtor_number} | H5获取债务人详情 | H5 Token |
| GET | /api/h5/stats | H5获取统计信息 | H5 Token |
| GET | /api/h5/query-limit | H5查询剩余限额 | H5 Token |
| POST | /api/h5/debt-info | H5查询债务信息 | H5 Token |
| GET | /api/h5/payment-accounts | 获取付款账户 | H5 Token |

### 7.5 合作伙伴API接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | /api/partner/health | 健康检查 | 否 |
| GET | /api/partner/query | 合作伙伴查询 | X-API-Key |
| GET | /api/partner/stats | 合作伙伴统计 | X-API-Key |
| GET | /api/partner/query-logs | 查询日志 | X-API-Key |

### 7.6 合作伙伴管理接口

| 方法 | 路径 | 描述 | 认证 | 权限 |
|------|------|------|------|------|
| GET | /api/partners/ | 获取合作伙伴列表 | 是 | 管理员 |
| GET | /api/partners/{id} | 获取合作伙伴详情 | 是 | 管理员 |
| POST | /api/partners/ | 创建合作伙伴 | 是 | 超级管理员 |
| PUT | /api/partners/{id} | 更新合作伙伴 | 是 | 超级管理员 |
| POST | /api/partners/{id}/regenerate-key | 重新生成API密钥 | 是 | 超级管理员 |
| DELETE | /api/partners/{id} | 删除合作伙伴 | 是 | 超级管理员 |

### 7.7 短信接口

| 方法 | 路径 | 描述 | 认证 | 权限 |
|------|------|------|------|------|
| POST | /api/sms/send | 发送短信 | 是 | 用户 |
| GET | /api/sms/{id} | 获取短信详情 | 是 | 用户 |
| GET | /api/sms/{id}/status | 查询短信状态 | 是 | 用户 |
| POST | /api/sms/callback | 短信状态回调 | 否 | 网关 |
| GET | /api/sms/ | 获取短信日志列表 | 是 | 管理员 |

### 7.8 验证码接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | /api/captcha/generate | 生成验证码 | 否 |
| POST | /api/captcha/verify | 验证验证码 | 否 |

### 7.9 渠道管理接口

| 方法 | 路径 | 描述 | 认证 | 权限 |
|------|------|------|------|------|
| POST | /api/channels/ | 创建渠道 | 是 | 操作员 |
| GET | /api/channels/ | 获取渠道列表 | 是 | 用户 |
| GET | /api/channels/{id} | 获取渠道详情 | 是 | 用户 |
| PUT | /api/channels/{id} | 更新渠道 | 是 | 操作员 |
| POST | /api/channels/{id}/test | 测试渠道 | 是 | 操作员 |
| POST | /api/channels/{id}/enable | 启用渠道 | 是 | 操作员 |
| POST | /api/channels/{id}/disable | 禁用渠道 | 是 | 操作员 |
| DELETE | /api/channels/{id} | 删除渠道 | 是 | 操作员 |

### 7.10 凭证管理接口

| 方法 | 路径 | 描述 | 认证 | 权限 |
|------|------|------|------|------|
| POST | /api/vouchers/upload | 上传凭证 | 是 | 操作员 |
| GET | /api/vouchers/ | 获取凭证列表 | 是 | 用户 |
| GET | /api/vouchers/{id} | 获取凭证详情 | 是 | 用户 |
| POST | /api/vouchers/{id}/approve | 批准凭证 | 是 | 管理员 |
| POST | /api/vouchers/{id}/reject | 拒绝凭证 | 是 | 管理员 |
| DELETE | /api/vouchers/{id} | 删除凭证 | 是 | 管理员 |

### 7.11 批次管理接口

| 方法 | 路径 | 描述 | 认证 | 权限 |
|------|------|------|------|------|
| POST | /api/batches/ | 创建批次 | 是 | 操作员 |
| GET | /api/batches/ | 获取批次列表 | 是 | 用户 |
| GET | /api/batches/{id} | 获取批次详情 | 是 | 用户 |
| PUT | /api/batches/{id} | 更新批次 | 是 | 操作员 |
| DELETE | /api/batches/{id} | 删除批次 | 是 | 操作员 |

### 7.12 导入接口

| 方法 | 路径 | 描述 | 认证 | 权限 |
|------|------|------|------|------|
| POST | /api/import/excel | 从Excel导入债务人 | 是 | 操作员 |
| POST | /api/import/validate | 验证Excel文件 | 是 | 用户 |

### 7.13 系统接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | / | 根路径，返回系统信息 | 否 |
| GET | /health | 健康检查 | 否 |
| GET | /docs | Swagger API文档 | 否 |
| GET | /redoc | ReDoc API文档 | 否 |
| GET | /openapi.json | OpenAPI规范 | 否 |

---

## 8. 安全说明

### 8.1 认证与授权

#### 8.1.1 JWT Token认证

- 访问管理后台API需要使用JWT Token
- Token在登录时获取，有效期默认为30分钟
- Token应放在HTTP头的 `Authorization: Bearer <token>` 中

#### 8.1.2 H5 Token认证

- H5移动端使用专用的H5 Token
- 通过短信验证码获取，有效期默认为7天
- 每日查询限制默认为100次

#### 8.1.3 API Key认证

- 合作伙伴使用API Key进行认证
- API Key通过 `X-API-Key` 头传递
- 每个合作伙伴有独立的API Key

### 8.2 角色权限

| 角色 | 描述 | 权限 |
|------|------|------|
| superadmin | 超级管理员 | 全部权限 |
| admin | 管理员 | 用户管理、部分系统配置 |
| operator | 操作员 | 数据操作、导入导出 |
| user | 普通用户 | 查看和查询 |

### 8.3 敏感数据加密

#### 8.3.1 电话号码加密

债务人的电话号码使用AES-256加密存储，访问时需要:

1. 用户已登录并通过认证
2. 具有相应的访问权限

#### 8.3.2 密码加密

用户密码使用bcrypt算法加密存储，不可逆向解密。

### 8.4 传输安全

- 生产环境务必使用HTTPS
- 敏感配置通过环境变量传递
- 定期更换密钥

### 8.5 限流保护

| 接口类型 | 限制 | 说明 |
|----------|------|------|
| 登录接口 | 5次/分钟 | 失败5次后锁定15分钟 |
| H5查询 | 100次/天 | 每个H5用户 |
| 合作伙伴API | 根据配置 | 每个合作伙伴不同 |

### 8.6 IP白名单

合作伙伴可以配置IP白名单，限制只有白名单内的IP可以调用API。

### 8.7 CORS配置

当前CORS配置为允许所有来源 (`allow_origins=["*"]`)，生产环境应限制为指定域名。

---

## 9. 故障排除

### 9.1 启动失败

#### 症状: 启动时报错 "ModuleNotFoundError"

**解决方案**:

```bash
pip install -r requirements.txt
```

#### 症状: 数据库连接失败

**解决方案**:

1. 检查 `DATABASE_URL` 配置是否正确
2. 确保数据库服务已启动
3. 检查数据库访问权限

### 9.2 认证问题

#### 症状: 返回 "401 Unauthorized"

**排查步骤**:

1. 检查Token是否过期
2. 检查Token格式是否正确 (`Bearer <token>`)
3. 确认请求头的拼写

#### 症状: 返回 "403 Forbidden"

**排查步骤**:

1. 确认用户具有相应权限
2. 检查用户角色是否正确
3. 超级管理员操作需要 `require_superadmin` 依赖

### 9.3 短信发送失败

**排查步骤**:

1. 检查SMS Gateway配置
2. 确认短信网关服务是否运行
3. 检查API Key是否正确
4. 查看短信日志获取详细错误信息

### 9.4 Excel导入失败

**常见原因**:

1. 文件格式不是 .xlsx 或 .xls
2. Excel表头与系统要求不匹配
3. 数据格式错误（如日期、金额格式）
4. 必填字段缺失

**解决方案**:

1. 使用 `POST /api/import/validate` 预先验证文件
2. 检查Excel文件格式
3. 确保必填字段有值

### 9.5 H5 Token获取失败

**排查步骤**:

1. 检查短信服务是否正常
2. 确认手机号格式正确
3. 检查验证码是否正确
4. 验证码有效期为300秒

### 9.6 性能问题

#### 高并发请求处理

如果系统响应变慢:

1. 启用数据库连接池
2. 添加缓存层 (Redis)
3. 使用负载均衡分散请求
4. 考虑水平扩展

#### 大文件导入

批量导入大文件时:

1. 使用后台任务处理
2. 分批导入
3. 增加Worker进程

### 9.7 日志查看

系统日志默认输出到 stdout。查看日志:

```bash
# 实时查看日志
tail -f /var/log/debtor-query-system.log

# 查看错误日志
grep ERROR /var/log/debtor-query-system.log
```

---

## 10. 常见问题

### Q1: 如何创建第一个管理员账户？

系统启动时会自动创建默认用户：
- 用户名: admin
- 密码: admin123

**首次登录后请立即修改密码！**

### Q2: 如何备份数据库？

**SQLite**:

```bash
cp debtor.db debtor.db.backup
```

**PostgreSQL**:

```bash
pg_dump -U postgres debtor_db > backup.sql
```

### Q3: 如何恢复数据库？

**SQLite**:

```bash
cp debtor.db.backup debtor.db
```

**PostgreSQL**:

```bash
psql -U postgres debtor_db < backup.sql
```

### Q4: 如何重置密码？

联系超级管理员执行密码重置:

```bash
curl -X POST "http://localhost:8000/api/users/{user_id}/password/reset" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "newpassword123"}'
```

### Q5: 如何查看API文档？

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Q6: 如何添加新的短信渠道？

1. 联系短信服务商获取API Key和接入地址
2. 在渠道管理中添加新渠道
3. 设置渠道优先级
4. 测试渠道连通性

### Q7: 忘记SECRET_KEY怎么办？

**重要**: 如果SECRET_KEY泄露，必须立即更换。

1. 生成新的SECRET_KEY
2. 更新 `.env` 文件
3. 重启服务
4. 注意：更换密钥后所有现有Token都会失效

### Q8: 如何监控系统运行状态？

1. 使用 `/health` 接口进行健康检查
2. 配置监控告警系统
3. 定期检查日志
4. 监控数据库连接和查询性能

### Q9: H5每日查询限制可以修改吗？

可以。在 `.env` 配置文件中修改 `H5_DAILY_QUERY_LIMIT` 的值，然后重启服务。

### Q10: 合作伙伴API调用返回429错误？

表示触发了限流限制:

1. 等待一段时间后重试
2. 联系管理员检查是否需要调整合作伙伴的限流配置
3. 确认IP是否在白名单内

---

## 附录

### A. 错误码说明

| 错误码 | 描述 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

### B. 日志级别

| 级别 | 描述 |
|------|------|
| DEBUG | 调试信息 |
| INFO | 一般信息 |
| WARNING | 警告信息 |
| ERROR | 错误信息 |
| CRITICAL | 严重错误 |

### C. 联系方式

如有问题，请联系系统管理员或提交Issue。

---

*本文档最后更新: 2024年*
