# 债务人还款账号查询系统 - 100%后端测试覆盖计划

## 一、测试覆盖概览

### 1.1 API端点清单与当前测试状态

| # | API模块 | 端点文件 | 现有测试 | 覆盖状态 |
|---|---------|----------|----------|----------|
| 1 | auth | api/auth.py | ❌ 缺失 | 0% |
| 2 | users | api/users.py | ❌ 缺失 | 0% |
| 3 | debtors | api/debtors.py | ⚠️ 部分 | 60% |
| 4 | h5 | api/h5.py | ❌ 缺失 | 0% |
| 5 | h5_auth | api/h5_auth.py | ✅ 已覆盖 | 100% |
| 6 | partner | api/partner.py | ❌ 缺失 | 0% |
| 7 | partners | api/partners.py | ⚠️ 部分 | 50% |
| 8 | captcha | api/captcha.py | ❌ 缺失 | 0% |
| 9 | batches | api/batches.py | ✅ 已覆盖 | 100% |
| 10 | channels | api/channels.py | ✅ 已覆盖 | 100% |
| 11 | config_endpoints | api/config_endpoints.py | ✅ 已覆盖 | 100% |
| 12 | vouchers | api/vouchers.py | ✅ 已覆盖 | 100% |
| 13 | import_endpoints | api/import_endpoints.py | ✅ 已覆盖 | 100% |
| 14 | partner_api | api/partner_api.py | ✅ 已覆盖 | 100% |
| 15 | admin_auth | api/admin_auth.py | ✅ 已覆盖 | 100% |
| 16 | sms | api/sms.py | ✅ 已覆盖 | 100% |

### 1.2 需要新增的测试文件

```
tests/
├── test_auth.py           # 认证API测试
├── test_users.py          # 用户管理API测试
├── test_h5.py             # H5查询API测试
├── test_partner.py        # 合作伙伴API测试
├── test_captcha.py        # 图形验证码API测试
└── test_debtors.py        # 债务人API测试（需增强）
```

---

## 二、新增测试详细规范

### 2.1 test_auth.py - 认证模块测试

```python
# 测试用例清单

# 1. 登录测试
- POST /api/auth/login - 正确凭据登录成功
- POST /api/auth/login - 错误密码登录失败
- POST /api/auth/login - 不存在用户登录失败
- POST /api/auth/login - 锁定账户登录失败
- POST /api/auth/login - 缺少必填字段
- POST /api/auth/login - 图形验证码错误

# 2. 用户信息测试
- GET /api/auth/me - 获取当前用户信息（已登录）
- GET /api/auth/me - 未授权访问被拒绝

# 3. 令牌刷新测试
- POST /api/auth/refresh - 刷新有效令牌
- POST /api/auth/refresh - 使用过期令牌
- POST /api/auth/refresh - 使用无效令牌

# 4. 密码重置测试
- POST /api/auth/password/reset - 发送重置验证码
- POST /api/auth/password/reset/confirm - 确认重置密码
- POST /api/auth/password/reset/confirm - 错误验证码
- POST /api/auth/password/reset/confirm - 过期验证码

# 5. 登出测试
- POST /api/auth/logout - 登出成功
- POST /api/auth/logout - 无效令牌
```

### 2.2 test_users.py - 用户管理模块测试

```python
# 测试用例清单

# 1. 用户列表测试
- GET /api/users/ - 获取用户列表（管理员）
- GET /api/users/ - 分页参数测试
- GET /api/users/ - 角色过滤测试

# 2. 用户CRUD测试
- POST /api/users/ - 创建新用户
- POST /api/users/ - 创建用户（用户名重复）
- POST /api/users/ - 创建用户（邮箱重复）
- GET /api/users/{id} - 获取用户详情
- GET /api/users/{id} - 用户不存在
- PUT /api/users/{id} - 更新用户信息
- PUT /api/users/{id} - 更新不存在的用户
- DELETE /api/users/{id} - 删除用户
- DELETE /api/users/{id} - 删除不存在的用户

# 3. 权限测试
- DELETE /api/users/{id} - 非管理员禁止删除
- PUT /api/users/{id}/role - 修改用户角色
- PUT /api/users/{id}/status - 修改用户状态

# 4. 批量操作测试
- POST /api/users/batch/delete - 批量删除用户
- POST /api/users/batch/status - 批量修改状态
```

### 2.3 test_h5.py - H5移动端API测试

```python
# 测试用例清单

# 1. H5 Token获取测试
- POST /api/auth/h5/token - 短信验证码获取Token
- POST /api/auth/h5/token - 错误验证码
- POST /api/auth/h5/token - 过期验证码
- POST /api/auth/h5/token - 不存在的手机号

# 2. H5债务查询测试
- GET /api/h5/query - 按手机号查询（有效Token）
- GET /api/h5/query - 按姓名+身份证查询
- GET /api/h5/query - 无效Token被拒绝
- GET /api/h5/query - 分页参数测试
- GET /api/h5/query - 超出每日限额

# 3. H5债务详情测试
- GET /api/h5/debtor/{debtor_number} - 获取详情
- GET /api/h5/debtor/{debtor_number} - 不存在债务人
- GET /api/h5/debtor/{debtor_number} - 无效Token

# 4. H5统计接口测试
- GET /api/h5/stats - 获取统计数据
- GET /api/h5/stats - 无效Token
```

### 2.4 test_partner.py - 合作伙伴API测试

```python
# 测试用例清单

# 1. Partner注册测试
- POST /api/partner/register - 正确注册
- POST /api/partner/register - 重复API Key
- POST /api/partner/register - 缺少必填字段

# 2. Partner Token获取测试
- POST /api/partner/token - 获取访问令牌
- POST /api/partner/token - 错误密钥
- POST /api/partner/token - 禁用合作方

# 3. Partner债务查询测试
- GET /api/partner/query - 有效Token查询
- GET /api/partner/query - 无效/过期Token
- GET /api/partner/query - 限流测试

# 4. Partner凭证上传测试
- POST /api/partner/voucher - 上传凭证
- POST /api/partner/voucher - 无效文件类型
- POST /api/partner/voucher - 文件过大

# 5. Partner状态管理测试
- POST /api/partner/revoke - 撤销合作
- POST /api/partner/suspend - 暂停合作
- POST /api/partner/activate - 激活合作
```

### 2.5 test_captcha.py - 图形验证码测试

```python
# 测试用例清单

# 1. 验证码生成测试
- GET /api/captcha/generate - 生成新验证码
- GET /api/captcha/generate - 连续生成测试
- GET /api/captcha/generate - 验证返回格式

# 2. 验证码验证测试
- POST /api/captcha/verify - 正确验证码
- POST /api/captcha/verify - 错误验证码
- POST /api/captcha/verify - 过期验证码
- POST /api/captcha/verify - 已使用的验证码
- POST /api/captcha/verify - 无效Key
- POST /api/captcha/verify - 缺少参数

# 3. 验证码频率限制测试
- 多次频繁请求生成验证码
- 多次频繁请求验证验证码
```

---

## 三、Service层测试覆盖

### 3.1 Service层覆盖清单

| Service | 文件 | 测试文件 | 覆盖率目标 |
|---------|------|----------|------------|
| AuthService | services/auth_service.py | test_auth.py | 100% |
| UserService | services/user_service.py | test_users.py | 100% |
| DebtorService | services/debtor_service.py | test_debtors.py | 100% |
| H5Service | services/h5_service.py | test_h5.py | 100% |
| PartnerService | services/partner_service.py | test_partner.py | 100% |
| BatchService | services/batch_service.py | test_batches.py | 100% |
| ChannelService | services/channel_service.py | test_channels.py | 100% |
| ConfigService | services/config_service.py | test_config.py | 100% |
| VoucherService | services/voucher_service.py | test_vouchers.py | 100% |
| ImportService | services/import_service.py | test_import.py | 100% |
| CaptchaService | services/captcha_service.py | test_captcha.py | 100% |
| SmsService | services/sms_service.py | test_sms.py | 100% |

---

## 四、测试数据规范

### 4.1 Fixtures命名规范

```python
# 用户类Fixture
admin_user          # 管理员用户
operator_user       # 操作员用户
viewer_user         # 查看者用户
locked_user         # 锁定用户
inactive_user       # 禁用用户

# Token类Fixture
admin_token         # 管理员Token
operator_token      # 操作员Token
viewer_token        # 查看者Token
h5_token            # H5访问Token
partner_token       # Partner API Token

# 数据类Fixture
sample_debtor       # 单个债务人
sample_debtors      # 债务人列表
sample_batch        # 单个批次
sample_voucher      # 凭证记录
sample_template     # 短信模板
sample_channel      # 短信渠道
sample_partner      # 合作伙伴
sample_config       # 系统配置
sample_payment_account  # 付款账户

# 请求头类Fixture
admin_headers       # 管理员请求头
operator_headers    # 操作员请求头
viewer_headers      # 查看者请求头
h5_headers          # H5请求头
partner_headers     # Partner请求头
```

### 4.2 测试数据隔离

每个测试使用独立的数据库session，确保测试间数据隔离：
```python
@pytest.fixture(scope="function")
def db_session(db_engine):
    # 每个测试创建新的session
    TestingSessionLocal = sessionmaker(...)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()
```

---

## 五、执行计划

### 5.1 测试执行顺序

1. **第一阶段：修复现有测试**
   - 修复test_debtors.py中的导入错误
   - 验证现有测试可通过

2. **第二阶段：新增核心测试**
   - test_auth.py（认证模块）
   - test_users.py（用户模块）
   - test_h5.py（H5模块）
   - test_partner.py（合作伙伴模块）
   - test_captcha.py（验证码模块）

3. **第三阶段：完整测试运行**
   - 执行完整测试套件
   - 生成覆盖率报告
   - 修复发现的问题

### 5.2 覆盖率目标

- **API端点覆盖率**: 100%
- **Service方法覆盖率**: 100%
- **关键业务逻辑覆盖率**: 100%

---

## 六、测试执行命令

```bash
# 进入后端目录
cd /Users/bion/Documents/Development/xingyun_sms/debtor-query-system/backend

# 运行所有测试
pytest tests/ -v

# 运行指定测试文件
pytest tests/test_auth.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 运行测试并显示print输出
pytest tests/ -v -s

# 运行测试并停在第一个失败
pytest tests/ -x

# 运行测试标记为slow的用例
pytest tests/ -v -m slow
```

---

## 七、测试验收标准

### 7.1 通过标准

- ✅ 所有测试用例通过
- ✅ API端点覆盖率 >= 95%
- ✅ Service层覆盖率 >= 90%
- ✅ 无测试数据泄漏
- ✅ 测试执行时间 < 5分钟

### 7.2 质量标准

- 测试函数命名清晰，以`test_`开头
- 每个测试函数只测试一个功能点
- 测试数据使用fixtures，不硬编码
- 异常情况测试覆盖完整
- 权限测试覆盖所有角色
