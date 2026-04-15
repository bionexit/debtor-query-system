# 债务人付款账户查询系统 - 详细使用手册

## 目录

1. [系统概述与架构](#1-系统概述与架构)
2. [安装与部署](#2-安装与部署)
3. [管理后台使用指南](#3-管理后台使用指南)
4. [H5移动端身份验证流程](#4-h5移动端身份验证流程)
5. [合作伙伴API使用指南](#5-合作伙伴api使用指南)
6. [短信服务配置](#6-短信服务配置)
7. [批量导入操作流程](#7-批量导入操作流程)
8. [故障排除](#8-故障排除)

---

## 1. 系统概述与架构

### 1.1 系统简介

债务人付款账户查询系统是一套完整的债务人信息管理解决方案，支持管理后台、H5移动端查询和第三方合作伙伴API对接。系统采用FastAPI后端+React前端架构，支持高并发访问和数据安全加密。

### 1.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                 │
├─────────────┬─────────────┬─────────────┬─────────────┬──────────┤
│  管理后台    │   H5移动端   │  合作伙伴API │  短信网关    │  定时任务  │
│  (Web UI)   │  (手机浏览器) │  (第三方)    │  (运营商)    │          │
└──────┬──────┴──────┬──────┴──────┬──────┴─────┬──────┴──────────┘
       │             │             │            │
       └─────────────┴─────────────┴────────────┘
                           │
                    ┌──────┴──────┐
                    │   API网关    │
                    │  (Uvicorn)  │
                    └──────┬──────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
┌──────┴──────┐    ┌──────┴──────┐    ┌──────┴──────┐
│  业务逻辑层   │    │   数据访问层  │    │   安全模块   │
│  (Services) │    │  (SQLAlchemy)│    │  (JWT/AES)  │
└──────┬──────┘    └──────┬──────┘    └─────────────┘
       │                   │
       │           ┌──────┴──────┐
       │           │    数据库    │
       │           │ (SQLite/MySQL│
       │           │ /PostgreSQL) │
       │           └─────────────┘
       │
┌──────┴──────┐
│  短信服务    │
│  (插件化)   │
└─────────────┘
```

### 1.3 核心模块说明

| 模块 | 说明 | 技术栈 |
|------|------|--------|
| 后端API | RESTful API服务 | FastAPI + Uvicorn |
| 管理后台 | React + Ant Design | React 18 + TypeScript |
| 数据库 | 关系型数据库 | SQLAlchemy ORM |
| 认证模块 | JWT/AES加密 | python-jose + passlib |
| 短信服务 | 插件化架构 | httpx |
| H5验证 | 移动端身份验证 | 短信验证码机制 |

### 1.4 数据库模型概览

**核心数据表:**

- `users` - 系统用户(管理员/操作员)
- `debtors` - 债务人信息
- `partners` - 合作伙伴
- `h5_users` - H5移动端用户
- `sms_channels` - 短信渠道配置
- `sms_templates` - 短信模板
- `vouchers` - 凭证文件
- `batches` - 批次管理
- `import_tasks` - 导入任务记录
- `sms_logs` - 短信发送日志

### 1.5 角色权限说明

| 角色 | 权限范围 |
|------|----------|
| super_admin | 全部权限、用户管理、系统配置 |
| admin | 用户管理(部分)、数据查看 |
| operator | 数据操作、导入导出、渠道管理 |
| viewer | 仅查看权限 |

---

## 2. 安装与部署

### 2.1 环境要求

**硬件要求:**
- CPU: 2核以上
- 内存: 4GB以上
- 磁盘: 10GB以上可用空间

**软件要求:**
- Python 3.9+
- Node.js 16+ (前端构建)
- SQLite/MySQL/PostgreSQL

### 2.2 本地开发环境安装

#### 步骤1: 克隆项目

```bash
cd /Users/bion/Documents/Development/xingyun_sms/debtor-query-system
```

#### 步骤2: 后端安装

```bash
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

#### 步骤3: 配置环境变量

创建 `backend/.env` 文件:

```env
# 应用配置
APP_NAME=Debtor Query System
VERSION=1.0.0
DEBUG=true

# 数据库配置
DATABASE_URL=sqlite:///./debtor.db

# JWT配置
SECRET_KEY=your-64-char-hex-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 短信网关配置
SMS_GATEWAY_URL=http://localhost:8001
SMS_GATEWAY_API_KEY=mock-sms-api-key

# 限流配置
RATE_LIMIT_PER_MINUTE=60
CAPTCHA_EXPIRE_SECONDS=300
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# H5配置
H5_TOKEN_EXPIRE_DAYS=7
H5_DAILY_QUERY_LIMIT=100

# AES加密密钥 (32字节)
AES_KEY=your-32-byte-hex-aes-key-here
```

#### 步骤4: 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 步骤5: 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 2.3 Docker部署

#### 使用docker-compose一键启动

```bash
cd /Users/bion/Documents/Development/xingyun_sms/debtor-query-system

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

#### 手动Docker构建

```bash
# 构建后端镜像
cd backend
docker build -t debtor-backend .

# 构建前端镜像
cd ../frontend
docker build -t debtor-frontend .

# 运行
docker run -d -p 8000:8000 --env-file backend/.env debtor-backend
```

### 2.4 生产环境部署

#### 使用Gunicorn (推荐)

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 使用systemd服务 (Linux)

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
ExecStart=/path/to/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
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

### 2.5 默认账户

系统首次启动会自动创建默认管理员账户:

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | super_admin |

**重要: 首次登录后请立即修改密码!**

---

## 3. 管理后台使用指南

### 3.1 系统访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| **管理后台** | http://localhost | 管理员登录和系统管理 |
| **H5身份验证** | http://localhost/h5/verify | 债务人手机端身份验证入口 |
| **H5债务查询** | http://localhost/h5/debt-info | 验证后债务信息查询 |
| **H5凭证上传** | http://localhost/h5/voucher/upload | 还款凭证上传 |
| **H5凭证结果** | http://localhost/h5/voucher/result | 凭证上传结果查看 |
| **API文档** | http://localhost:8000/docs | Swagger API文档 |
| **短信Mock** | http://localhost:8001 | SMS模拟服务器 |

**Docker部署端口说明**:
- `FRONTEND_PORT=80` (默认) - 前端Nginx端口
- `BACKEND_PORT=8000` (默认) - 后端API端口
- `SMS_MOCK_PORT=8001` (默认) - 短信Mock服务端口

### 3.3 登录页面

1. 访问管理后台登录页面
2. 输入用户名和密码
3. 输入图形验证码
4. 点击"登录"按钮

登录成功后会跳转到仪表盘页面。

### 3.4 仪表盘 (Dashboard)

仪表盘展示系统关键数据和快捷操作入口:

**统计卡片:**
- 债务人总数
- 今日新增债务人
- 待审核凭证数
- 活跃批次数量

**快捷操作区:**
- 批次管理 - 跳转至批次管理页面
- 债务人管理 - 跳转至债务人列表
- 发送短信 - 跳转至短信模板管理
- 凭证管理 - 跳转至凭证审核页面

**最近凭证表格:**
- 显示最近提交的凭证
- 可快速审核

### 3.5 债务人管理页面 (Debtors)

#### 3.3.1 功能说明

债务人管理是系统的核心功能页面,提供债务人的CRUD操作。

#### 3.3.2 页面布局

```
┌────────────────────────────────────────────────────────────┐
│ 债务人管理                                      [导出] [导入] [新增] │
├────────────────────────────────────────────────────────────┤
│ 搜索: [____________] 状态: [全部▼]              [搜索] [重置]      │
├────────────────────────────────────────────────────────────┤
│ ID  │ 编号        │ 姓名  │ 手机号    │ 欠款金额 │ 逾期天数 │ 状态 │ 操作 │
├─────┼────────────┼───────┼───────────┼──────────┼─────────┼──────┼──────┤
│  1  │ D20240001   │ 张三  │ 138****00  │ ¥50,000 │   90天  │ 逾期 │ ...  │
│  2  │ D20240002   │ 李四  │ 139****01  │ ¥30,000 │   60天  │ 正常 │ ...  │
└────────────────────────────────────────────────────────────┘
```

#### 3.3.3 功能操作

**新增债务人:**
1. 点击右上角"新增"按钮
2. 填写表单: 债务人编号、姓名、身份证号、手机号、邮箱、银行信息、欠款金额、逾期天数等
3. 点击"保存"按钮

**搜索和筛选:**
1. 在搜索框输入债务人编号或姓名
2. 选择状态筛选(全部/正常/逾期/已还清/黑名单)
3. 点击"搜索"按钮

**查看详情:**
1. 点击操作列的"查看"按钮
2. 在抽屉中查看完整信息

**编辑债务人:**
1. 点击操作列的"编辑"按钮
2. 修改需要变更的字段
3. 点击"保存"按钮

**删除债务人:**
1. 点击操作列的"删除"按钮
2. 确认删除操作

**批量导入:**
1. 点击右上角"导入"按钮
2. 选择Excel文件(.xlsx或.xls)
3. 系统自动验证并显示预览
4. 确认导入

### 3.6 批次管理页面 (Batches)

#### 3.4.1 功能说明

批次管理用于将债务人分组管理,方便批量操作和统计。

#### 3.4.2 创建批次

1. 点击右上角"新增批次"按钮
2. 填写批次名称和描述
3. 点击"保存"按钮

#### 3.4.3 批次操作

- 查看批次详情
- 编辑批次信息
- 将债务人分配到批次
- 关闭/归档批次

### 3.7 短信渠道管理页面 (SMS Channels)

#### 3.5.1 功能说明

短信渠道管理用于配置短信发送通道,支持多渠道和负载均衡。

#### 3.5.2 页面展示

```
┌─────────────────────────────────────────────────────────────┐
│ 短信渠道管理                               [扫描目录] [添加渠道]   │
├─────────────────────────────────────────────────────────────┤
│ 渠道总数: 3  │ 启用中: 2  │ 禁用中: 1  │ 平均成功率: 98.5%      │
├─────────────────────────────────────────────────────────────┤
│ ID │ 渠道名称 │ 提供商  │ 状态  │ 优先级 │ 成功率 │ 响应时间 │ 操作 │
├────┼─────────┼─────────┼───────┼────────┼────────┼─────────┼──────┤
│  1 │ 主通道   │ Aliyun  │ 启用  │   1    │ 99.2%  │  150ms  │ ...  │
│  2 │ 备用通道 │ Tencent │ 禁用  │   2    │ 97.8%  │  200ms  │ ...  │
└─────────────────────────────────────────────────────────────┘
```

#### 3.5.3 添加渠道

1. 点击右上角"添加渠道"按钮
2. 填写表单:
   - 渠道名称: 如"阿里云主通道"
   - 提供商: 选择短信服务商(aliyun/tencent/mock等)
   - 接入地址: API接口URL
   - API密钥: 服务商提供的密钥
   - 优先级: 数字越小优先级越高
3. 点击"保存"按钮

#### 3.5.4 渠道操作

**测试渠道:**
1. 点击操作列的"测试"按钮
2. 输入测试手机号
3. 点击"发送测试短信"按钮
4. 查看发送结果

**启用/禁用:**
- 点击"启用"或"禁用"按钮切换状态

**编辑配置:**
1. 点击"配置"按钮
2. 修改渠道参数
3. 保存更改

**删除渠道:**
1. 点击"删除"按钮
2. 确认删除操作

### 3.8 短信模板管理页面 (SMS Templates)

#### 3.6.1 功能说明

管理短信通知模板,支持变量替换。

#### 3.6.2 模板变量

常用变量格式: `{{变量名}}`

| 变量名 | 说明 |
|--------|------|
| name | 债务人姓名 |
| amount | 欠款金额 |
| due_date | 到期日期 |
| phone | 手机号 |

#### 3.6.3 添加模板

1. 点击右上角"新增模板"按钮
2. 填写:
   - 模板名称
   - 模板类型(通知/验证码/提醒)
   - 短信内容(支持变量)
3. 点击"保存"按钮

### 3.9 凭证管理页面 (Vouchers)

#### 3.7.1 功能说明

凭证管理用于上传和审核债务人的付款凭证。

#### 3.7.2 凭证状态

| 状态 | 说明 |
|------|------|
| pending | 待审核 |
| approved | 已通过 |
| rejected | 已拒绝 |

#### 3.7.3 审核操作

**批准凭证:**
1. 点击操作列的"审核"按钮
2. 查看凭证详情
3. 点击"批准"按钮
4. 填写审核备注(可选)
5. 确认提交

**拒绝凭证:**
1. 点击操作列的"审核"按钮
2. 查看凭证详情
3. 点击"拒绝"按钮
4. 填写拒绝原因
5. 确认提交

### 3.10 用户管理 (需在后端API操作)

系统用户管理通过后端API进行:

```bash
# 获取用户列表
curl -X GET "http://localhost:8000/api/users/" \
  -H "Authorization: Bearer <admin_token>"

# 创建用户
curl -X POST "http://localhost:8000/api/users/" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "pass123", "role": "operator"}'

# 重置用户密码
curl -X POST "http://localhost:8000/api/users/{user_id}/password/reset" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"new_password": "newpass123"}'
```

---

## 4. H5移动端身份验证流程

### 4.1 H5流程概述

H5移动端为债务人提供手机端身份验证和债务信息查询服务。

### 4.2 访问地址

| 页面 | URL | 说明 |
|------|-----|------|
| H5首页/身份验证 | http://localhost/h5/verify | 债务人输入手机号获取验证码 |
| 债务信息查询 | http://localhost/h5/debt-info | 验证成功后查询债务信息 |
| 凭证上传 | http://localhost/h5/voucher/upload | 上传还款凭证 |
| 凭证结果 | http://localhost/h5/voucher/result | 查看凭证上传结果 |

**注意**: H5页面需要在PC端先登录管理后台获取会话，或使用独立的身份验证流程。

### 4.3 验证流程图

```
┌─────────────┐
│  打开H5页面  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ 输入手机号      │
│ 请求验证码      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  系统发送短信   │
│  验证码至手机  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  输入验证码    │
│  提交验证      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  验证成功      │
│  获取H5 Token  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  使用Token     │
│  查询债务信息  │
└─────────────────┘
```

### 4.4 API接口说明

#### 4.3.1 请求验证码

```
POST /api/h5/captcha
Content-Type: application/json

{
  "phone": "13800138000"
}
```

**响应:**
```json
{
  "captcha_id": "xxx",
  "expires_in": 300
}
```

#### 4.3.2 验证并获取Token

```
POST /api/h5/verify
Content-Type: application/json

{
  "phone": "13800138000",
  "captcha": "123456"
}
```

**响应:**
```json
{
  "access_token": "eyJhbGc...",
  "expires_in": 604800
}
```

#### 4.3.3 查询债务信息

```
POST /api/h5/debt-info
Authorization: Bearer <h5_token>
Content-Type: application/json

{
  "debtor_id_card": "110101199001011234"
}
```

**响应:**
```json
{
  "debtor_id": 1,
  "name": "张三",
  "id_card": "110101199001011234",
  "phone": "138****0000",
  "debt_amount": 50000.00,
  "status": "overdue"
}
```

#### 4.3.4 获取付款账户

```
GET /api/h5/payment-accounts
Authorization: Bearer <h5_token>
```

**响应:**
```json
{
  "accounts": [
    {
      "bank_name": "中国工商银行",
      "bank_account": "622202****7890",
      "bank_account_name": "张三"
    }
  ]
}
```

#### 4.3.5 查询剩余限额

```
GET /api/h5/query-limit
Authorization: Bearer <h5_token>
```

**响应:**
```json
{
  "remaining": 95,
  "limit": 100,
  "reset_at": "2024-01-15 23:59:59"
}
```

### 4.5 每日限额说明

- 默认每日查询限额: 100次
- 限额按自然日重置
- 超限后需等到次日或联系管理员调整

---

## 5. 合作伙伴API使用指南

### 5.1 认证机制

合作伙伴API使用签名认证机制,需要:

1. API Key: 合作伙伴唯一标识
2. Secret Key: 签名密钥
3. 签名: 基于请求参数的HMAC-SHA256签名

### 5.2 认证头格式

```
Authorization: Partner <api_key>:<signature>:<timestamp>
```

其中:
- `api_key`: 合作伙伴的API Key
- `signature`: HMAC-SHA256签名
- `timestamp`: Unix时间戳(秒)

### 5.3 签名计算方法

```python
import hmac
import hashlib
import time

def generate_signature(api_key, secret_key, params=""):
    timestamp = int(time.time())
    message = f"{api_key}:{params}:{timestamp}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{api_key}:{signature}:{timestamp}"
```

### 5.4 API接口

#### 5.4.1 健康检查

```
GET /api/partner/health
```

**响应:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### 5.4.2 查询债务人

```
POST /api/partner/query
Authorization: Partner <credentials>
Content-Type: application/json

{
  "id_card": "110101199001011234",
  "name": "张三"
}
```

**响应:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "debtor_id": 1,
    "name": "张三",
    "id_card": "110101199001011234",
    "phone": "13800138000",
    "debt_amount": 50000.00,
    "status": "overdue"
  }
}
```

#### 5.4.3 获取统计信息

```
GET /api/partner/stats
Authorization: Partner <credentials>
```

**响应:**
```json
{
  "total_queries": 1000,
  "today_queries": 50,
  "remaining_quota": 9950
}
```

### 5.5 限流说明

| 限制类型 | 默认值 |
|----------|--------|
| 每分钟请求数 | 100 |
| 每日请求数 | 10000 |

超限返回429错误。

### 5.6 错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 403 | 姓名与身份证不匹配 |
| 404 | 未找到债务人 |
| 429 | 请求过于频繁 |

---

## 6. 短信服务配置

### 6.1 短信架构

系统采用插件化短信架构,支持多渠道负载均衡和故障转移。

### 6.2 内置短信提供商

| 提供商 | 说明 |
|--------|------|
| aliyun | 阿里云短信服务 |
| tencent | 腾讯云短信服务 |
| mock | 开发测试用模拟服务 |

### 6.3 添加自定义短信提供商

在 `backend/sms_providers/` 目录下创建新的提供商模块:

```python
# backend/sms_providers/my_provider.py

from typing import Dict, Any
from app.plugins.sms.base import SMSProviderBase

class MyProvider(SMSProviderBase):
    name = "my_provider"
    
    def __init__(self, config: Dict[str, Any]):
        self.endpoint = config.get("endpoint")
        self.api_key = config.get("api_key")
    
    async def send(self, phone: str, message: str) -> Dict[str, Any]:
        # 实现发送逻辑
        response = await self._http_client.post(
            self.endpoint,
            json={"phone": phone, "message": message},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    def _parse_response(self, response: Dict) -> bool:
        return response.get("code") == "OK"
```

### 6.4 渠道优先级与故障转移

当配置多个短信渠道时:

1. 系统按优先级选择可用渠道
2. 当高优先级渠道失败时,自动切换到下一优先级
3. 渠道自动禁用条件:
   - 连续失败5次
   - 成功率低于80%

### 6.5 短信模板变量

在短信内容中使用变量:

| 变量 | 说明 | 示例 |
|------|------|------|
| {{name}} | 债务人姓名 | 张三 |
| {{amount}} | 欠款金额 | 50000 |
| {{due_date}} | 到期日期 | 2024-01-31 |
| {{debtor_number}} | 债务人编号 | D20240001 |

### 6.6 短信日志查询

```bash
# 获取短信发送日志
curl -X GET "http://localhost:8000/api/sms/" \
  -H "Authorization: Bearer <token>"

# 查询单条短信状态
curl -X GET "http://localhost:8000/api/sms/{sms_id}/status" \
  -H "Authorization: Bearer <token>"
```

---

## 7. 批量导入操作流程

### 7.1 支持的文件格式

- Excel文件 (.xlsx)
- Excel旧格式 (.xls)

### 7.2 Excel文件格式要求

**必填字段:**
| 字段 | 说明 | 示例 |
|------|------|------|
| debtor_number | 债务人编号 | D20240001 |
| name | 姓名 | 张三 |
| id_card | 身份证号 | 110101199001011234 |
| phone | 手机号 | 13800138000 |

**可选字段:**
| 字段 | 说明 |
|------|------|
| email | 电子邮箱 |
| bank_name | 银行名称 |
| bank_account | 银行账号 |
| bank_account_name | 账户名 |
| address | 地址 |
| overdue_amount | 逾期金额 |
| overdue_days | 逾期天数 |
| remark | 备注 |

### 7.3 导入流程

#### 步骤1: 准备Excel文件

1. 打开Excel软件
2. 创建工作表,表头行为第一行
3. 按上述格式填写数据
4. 保存为.xlsx格式

#### 步骤2: 上传文件

通过管理后台上传:
1. 进入"债务人管理"页面
2. 点击右上角"导入"按钮
3. 选择准备好的Excel文件
4. 点击"上传"按钮

通过API上传:
```bash
curl -X POST "http://localhost:8000/api/debtors/import" \
  -H "Authorization: Bearer <token>" \
  -F "file=@debtors.xlsx"
```

#### 步骤3: 数据验证

系统自动进行验证:
- 必填字段检查
- 身份证号格式验证
- 手机号格式验证
- 重复数据检查

验证结果会显示:
- 成功导入数量
- 失败记录数量
- 失败原因详情

#### 步骤4: 确认导入

1. 查看验证结果
2. 如有错误,可下载错误报告
3. 修正Excel文件后重新导入
4. 确认无误后点击"确认导入"

### 7.4 导入任务记录

查看导入历史:
```bash
curl -X GET "http://localhost:8000/api/debtors/imports/history" \
  -H "Authorization: Bearer <token>"
```

**响应:**
```json
{
  "tasks": [
    {
      "id": 1,
      "filename": "debtors.xlsx",
      "total_count": 100,
      "success_count": 95,
      "fail_count": 5,
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "created_by": "admin"
    }
  ]
}
```

### 7.5 常见导入错误

| 错误类型 | 原因 | 解决方法 |
|----------|------|----------|
| 必填字段缺失 | 编号/姓名/身份证号未填写 | 补充缺失数据 |
| 身份证号格式错误 | 身份证号不符合18位规则 | 核对并修正身份证号 |
| 手机号格式错误 | 手机号不符合11位规则 | 核对并修正手机号 |
| 重复数据 | 债务人编号已存在 | 使用新的编号或更新现有记录 |
| 日期格式错误 | 日期格式不符合要求 | 使用标准日期格式YYYY-MM-DD |

---

## 8. 故障排除

### 8.1 启动问题

#### 8.1.1 ModuleNotFoundError

**错误信息:**
```
ModuleNotFoundError: No module named 'xxx'
```

**解决方案:**
```bash
pip install -r requirements.txt
```

#### 8.1.2 数据库连接失败

**错误信息:**
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError)
```

**排查步骤:**
1. 检查 `DATABASE_URL` 配置是否正确
2. 确认数据库服务已启动
3. 检查数据库访问权限
4. 验证防火墙设置

**SQLite问题:**
```bash
# 检查文件是否存在
ls -la backend/debtor.db

# 修复权限
chmod 666 backend/debtor.db
```

### 8.2 认证问题

#### 8.2.1 401 Unauthorized

**原因:**
- Token已过期
- Token格式不正确
- Authorization头拼写错误

**排查步骤:**
1. 检查Token是否过期(默认30分钟)
2. 确认请求头格式: `Authorization: Bearer <token>`
3. 重新登录获取新Token

#### 8.2.2 403 Forbidden

**原因:**
- 用户权限不足
- 操作需要更高权限

**解决方案:**
联系管理员确认账户角色和权限。

### 8.3 短信发送问题

#### 8.3.1 短信发送失败

**排查步骤:**
1. 检查短信网关服务是否运行:
   ```bash
   curl http://localhost:8001/health
   ```
2. 验证SMS_GATEWAY_URL配置
3. 检查API Key是否正确
4. 查看短信日志:
   ```bash
   curl -X GET "http://localhost:8000/api/sms/" \
     -H "Authorization: Bearer <token>"
   ```

#### 8.3.2 渠道响应超时

**解决方案:**
1. 检查网络连接
2. 调整渠道超时配置
3. 考虑切换到响应更快的渠道

### 8.4 H5验证问题

#### 8.4.1 验证码获取失败

**排查步骤:**
1. 确认手机号格式正确(11位)
2. 检查短信服务是否正常
3. 验证验证码有效期(300秒)

#### 8.4.2 Token获取后立即过期

**原因:** 系统时间不同步

**解决方案:**
```bash
# 同步系统时间 (macOS)
sudo sntp -s time.apple.com

# 同步系统时间 (Linux)
sudo ntpdate time.nist.gov
```

### 8.5 合作伙伴API问题

#### 8.5.1 签名验证失败

**排查步骤:**
1. 确认API Key和Secret Key正确
2. 检查时间戳是否在有效期内(±5分钟)
3. 验证签名计算方法

**Python签名示例:**
```python
import hmac
import hashlib
import time

def generate_auth_header(api_key, secret_key):
    timestamp = int(time.time())
    message = f"{api_key}::{timestamp}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"Partner {api_key}:{signature}:{timestamp}"
```

#### 8.5.2 429 Too Many Requests

**原因:** 触发限流

**解决方案:**
1. 等待一段时间后重试
2. 联系管理员检查限流配置
3. 确认IP是否在白名单内

### 8.6 数据导入问题

#### 8.6.1 导入文件格式错误

**解决方案:**
1. 确保文件格式为.xlsx或.xls
2. 表头必须在第一行
3. 不要合并单元格
4. 避免特殊字符

#### 8.6.2 部分数据导入失败

**排查步骤:**
1. 查看导入结果报告
2. 修正失败行的数据
3. 重新导入失败的数据

### 8.7 性能问题

#### 8.7.1 API响应慢

**排查步骤:**
1. 检查数据库查询性能
2. 查看是否有慢查询日志
3. 检查服务器资源使用情况

**优化建议:**
- 启用数据库连接池
- 添加缓存(Redis)
- 使用负载均衡

#### 8.7.2 前端加载慢

**排查步骤:**
1. 检查网络延迟
2. 清理浏览器缓存
3. 查看前端控制台错误

### 8.8 日志查看

#### 8.8.1 后端日志

```bash
# 实时查看日志 (Docker)
docker-compose logs -f backend

# 实时查看日志 (本地)
tail -f backend/app.log
```

#### 8.8.2 数据库日志

```bash
# SQLite
cat backend/debtor.db

# MySQL
mysql -u root -p -e "SHOW VARIABLES LIKE 'log%';"
```

### 8.9 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 短信网关健康检查
curl http://localhost:8001/health

# 数据库连接检查
curl http://localhost:8000/api/sms/channels/
```

### 8.10 常见问题FAQ

**Q1: 如何重置管理员密码?**
```bash
# 方式1: 通过API
curl -X POST "http://localhost:8000/api/users/1/password/reset" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"new_password": "newpassword123"}'

# 方式2: 直接修改数据库
sqlite3 backend/debtor.db "UPDATE users SET password_hash='$2b$12$...' WHERE id=1;"
```

**Q2: 如何备份数据库?**
```bash
# SQLite
cp backend/debtor.db backend/debtor.db.backup

# MySQL
mysqldump -u root -p debtor_db > backup.sql
```

**Q3: 如何查看API文档?**
启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Q4: H5每日查询限额可以调整吗?**
可以,修改环境变量:
```env
H5_DAILY_QUERY_LIMIT=200
```
然后重启服务。

**Q5: 如何添加新的短信渠道?**
1. 联系短信服务商获取API Key
2. 在管理后台添加渠道配置
3. 设置渠道优先级
4. 测试渠道连通性

---

## 附录A: 环境变量完整列表

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| APP_NAME | 应用名称 | Debtor Query System | 是 |
| VERSION | 版本号 | 1.0.0 | 是 |
| DEBUG | 调试模式 | false | 是 |
| DATABASE_URL | 数据库连接URL | sqlite:///./debtor.db | 是 |
| SECRET_KEY | JWT密钥(64字符) | - | **是** |
| ALGORITHM | JWT算法 | HS256 | 是 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token过期时间 | 30 | 是 |
| SMS_GATEWAY_URL | 短信网关地址 | http://localhost:8001 | 是 |
| SMS_GATEWAY_API_KEY | 短信网关API密钥 | - | 是 |
| RATE_LIMIT_PER_MINUTE | 每分钟限流 | 60 | 是 |
| CAPTCHA_EXPIRE_SECONDS | 验证码有效期 | 300 | 是 |
| MAX_LOGIN_ATTEMPTS | 最大登录尝试 | 5 | 是 |
| LOCKOUT_DURATION_MINUTES | 账户锁定时长 | 15 | 是 |
| H5_TOKEN_EXPIRE_DAYS | H5 Token过期天数 | 7 | 是 |
| H5_DAILY_QUERY_LIMIT | H5每日查询限制 | 100 | 是 |
| AES_KEY | AES加密密钥(32字节) | - | **是** |

## 附录B: API错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| 400 | 400 | 请求参数错误 |
| 401 | 401 | 认证失败 |
| 403 | 403 | 权限不足 |
| 404 | 404 | 资源不存在 |
| 429 | 429 | 请求过于频繁 |
| 500 | 500 | 服务器内部错误 |

## 附录C: 联系方式

如有问题,请联系系统管理员或提交Issue。

---

*本文档最后更新: 2024年*
