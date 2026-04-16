import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import bcrypt

# Import Base from models.py
from app.models.models import Base

# Import enums from models.py
from app.models.models import (
    DebtorStatus, BatchStatus, VoucherStatus, SMSTaskStatus,
    SmsTemplateStatus, ChannelStatus, AttemptType, AIStatus, ImportTaskStatus,
    CaseBatch, PaymentVoucher, SmsTemplate, SmsTask, SmsSendLog,
    SmsChannel, SystemConfig, ConfigChangeLog, ImportTask, ApiAccessLog,
    Captcha, Partner, Admin, AdminSession, Debtor, PaymentAccount,
    AccessToken, SessionToken, FailedAttempt, H5User
)

# Import User from user.py
from app.models.user import User, UserRole, UserStatus

# Import database dependency - MUST override both app.core.database and app.models.database
# since different routers import from different modules
from app.core.database import get_db as core_get_db
from app.models.database import get_db as models_get_db

# Import security functions
from app.core.security import create_access_token, create_h5_token

# Import settings
from app.core.config import settings

# Import main app
from app.main import app

# Test database URL - SQLite in-memory for tests
TEST_DATABASE_URL = "sqlite:///:memory:"


def get_password_hash(password: str) -> str:
    """Password hash using direct bcrypt (not passlib)."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[core_get_db] = override_get_db
    app.dependency_overrides[models_get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============ User Fixtures ============

@pytest.fixture
def admin_user(db_session) -> User:
    """Create a superadmin user (has full privileges)"""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_superadmin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def operator_user(db_session) -> User:
    """Create an operator user"""
    user = User(
        username="operator",
        email="operator@example.com",
        hashed_password=get_password_hash("operator123"),
        role=UserRole.OPERATOR,
        status=UserStatus.ACTIVE,
        is_superadmin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def viewer_user(db_session) -> User:
    """Create a viewer user"""
    user = User(
        username="viewer",
        email="viewer@example.com",
        hashed_password=get_password_hash("viewer123"),
        role=UserRole.VIEWER,
        status=UserStatus.ACTIVE,
        is_superadmin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def locked_user(db_session) -> User:
    """Create a locked user"""
    user = User(
        username="locked",
        email="locked@example.com",
        hashed_password=get_password_hash("locked123"),
        role=UserRole.OPERATOR,
        status=UserStatus.LOCKED,
        is_superadmin=False,
        locked_until=datetime.utcnow() + timedelta(minutes=15)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============ Auth Token Fixtures ============

@pytest.fixture
def admin_token(admin_user) -> str:
    """Create admin JWT token"""
    return create_access_token(
        data={"sub": str(admin_user.id), "username": admin_user.username, "role": admin_user.role.value}
    )


@pytest.fixture
def operator_token(operator_user) -> str:
    """Create operator JWT token"""
    return create_access_token(
        data={"sub": str(operator_user.id), "username": operator_user.username, "role": operator_user.role.value}
    )


@pytest.fixture
def viewer_token(viewer_user) -> str:
    """Create viewer JWT token"""
    return create_access_token(
        data={"sub": str(viewer_user.id), "username": viewer_user.username, "role": viewer_user.role.value}
    )


@pytest.fixture
def admin_headers(admin_token) -> dict:
    """Admin authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def operator_headers(operator_token) -> dict:
    """Operator authorization headers"""
    return {"Authorization": f"Bearer {operator_token}"}


@pytest.fixture
def viewer_headers(viewer_token) -> dict:
    """Viewer authorization headers"""
    return {"Authorization": f"Bearer {viewer_token}"}


# ============ Debtor Fixtures ============

@pytest.fixture
def sample_batch(db_session, admin_user) -> CaseBatch:
    """Create a sample batch"""
    batch = CaseBatch(
        batch_no="BATCH-20240101-TEST01",
        name="Test Batch",
        partner_id="PARTNER001",
        status=BatchStatus.PENDING,
        total_count=0,
        success_count=0,
        fail_count=0,
        created_by=admin_user.id
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture
def sample_debtor(db_session, sample_batch, admin_user) -> Debtor:
    """Create a sample debtor"""
    debtor = Debtor(
        debtor_number="D20240001",
        name="Zhang San",
        id_card="110101199001011234",
        encrypted_phone="13800138000",  # Stored encrypted
        phone_nonce="nonce_placeholder",
        phone_tag="tag_placeholder",
        address="Beijing",
        overdue_amount=10000,
        overdue_days=30,
        status=DebtorStatus.ACTIVE,
        created_by_id=admin_user.id
    )
    db_session.add(debtor)
    db_session.commit()
    db_session.refresh(debtor)
    return debtor


@pytest.fixture
def sample_debtors(db_session, sample_batch, admin_user) -> list:
    """Create multiple sample debtors"""
    debtors = []
    for i in range(5):
        debtor = Debtor(
            debtor_number=f"D2024000{i+1}",
            name=f"Debtor {i}",
            id_card=f"11010119900101{i:04d}",
            encrypted_phone=f"1380013{i:04d}",  # Stored encrypted
            phone_nonce=f"nonce_{i}",
            phone_tag=f"tag_{i}",
            address=f"Address {i}",
            overdue_amount=1000 * (i + 1),
            overdue_days=30 * (i + 1),
            status=DebtorStatus.ACTIVE,
            created_by_id=admin_user.id
        )
        debtors.append(debtor)
        db_session.add(debtor)
    db_session.commit()
    return debtors


# ============ H5 Fixtures ============

@pytest.fixture
def h5_user(db_session) -> H5User:
    """Create an H5 user for authentication"""
    user = H5User(
        phone="13900139000",
        name="H5 User",
        is_locked=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def h5_token(h5_user) -> str:
    """Create H5 access token using H5User's phone"""
    return create_h5_token(data={"phone": h5_user.phone, "sub": str(h5_user.id)})


@pytest.fixture
def h5_headers(h5_token) -> dict:
    """H5 authorization headers"""
    return {"Authorization": f"Bearer {h5_token}"}


# ============ Partner Fixtures ============

@pytest.fixture
def sample_partner(db_session) -> Partner:
    """Create a sample partner"""
    partner = Partner(
        partner_id="PARTNER001",
        partner_name="Test Partner",
        partner_code="TP001",
        api_key="test-api-key-123",
        secret_key="test-secret-key-456",
        is_api_enabled=True,
        is_revoked=False,
        rate_limit_per_minute=60,
        rate_limit_per_day=10000,
        daily_query_limit=1000,
        monthly_query_limit=30000,
        today_query_count=0
    )
    db_session.add(partner)
    db_session.commit()
    db_session.refresh(partner)
    return partner


# ============ Config Fixtures ============

@pytest.fixture
def sample_config(db_session, admin_user) -> SystemConfig:
    """Create a sample config"""
    config = SystemConfig(
        config_id="CFG001",
        config_key="MAX_QUERY_LIMIT",
        config_value="1000",
        is_active=True,
        description="Maximum query limit",
        changed_by=admin_user.username
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    return config


# ============ Payment Account Fixtures ============

@pytest.fixture
def sample_payment_account(db_session) -> PaymentAccount:
    """Create a sample payment account"""
    account = PaymentAccount(
        account_id="ACC001",
        partner_id="PARTNER001",
        bank_name="ICBC",
        account_number="6222021234567890",
        account_name="Test Company",
        is_active=True,
        is_primary=True
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


# ============ SMS Channel Fixtures ============

@pytest.fixture
def sample_channel(db_session) -> SmsChannel:
    """Create a sample SMS channel"""
    channel = SmsChannel(
        channel_id="CH001",
        channel_name="Test Channel",
        channel_code="TEST_CHANNEL",
        class_name="MockSMSProvider",
        file_path="/app/sms_providers/mock.py",
        config_data={"api_key": "***", "api_url": "http://test.com"},
        is_default=True,
        status="active",
        priority=1,
        name="Test Channel",
        provider="MockProvider",
        endpoint="http://test.com/api",
        api_key="test-key",
        is_active=True
    )
    db_session.add(channel)
    db_session.commit()
    db_session.refresh(channel)
    return channel


# ============ SMS Template Fixtures ============

@pytest.fixture
def sample_template(db_session, sample_channel) -> SmsTemplate:
    """Create a sample SMS template"""
    template = SmsTemplate(
        template_id="TPL001",
        template_name="Test Template",
        template_content="Hello {{name}}, your debt is {{amount}}",
        variables=["name", "amount"],
        status="active",
        channel_id=sample_channel.channel_id
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


# ============ SMS Task Fixtures ============

@pytest.fixture
def sample_task(db_session, sample_template, admin_user) -> SmsTask:
    """Create a sample SMS task"""
    task = SmsTask(
        task_id="TASK001",
        template_id=sample_template.template_id,
        user_ids=["USER001", "USER002"],
        phone_numbers=["13800138000", "13800138001"],
        variables_data={"name": ["John", "Jane"], "amount": ["1000", "2000"]},
        status="pending"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


# ============ Voucher Fixtures ============

@pytest.fixture
def sample_voucher(db_session, admin_user) -> PaymentVoucher:
    """Create a sample payment voucher"""
    voucher = PaymentVoucher(
        voucher_id="VCH001",
        file_name="test_voucher.xlsx",
        file_path="./uploads/test_voucher.xlsx",
        file_size=1024,
        total_count=10,
        success_count=8,
        fail_count=2,
        status="pending",
        uploaded_by=admin_user.id,
        ai_status="manual"
    )
    db_session.add(voucher)
    db_session.commit()
    db_session.refresh(voucher)
    return voucher


# ============ Access Token Fixtures ============

@pytest.fixture
def sample_access_token(db_session, admin_user) -> AccessToken:
    """Create a sample access token for H5"""
    token = AccessToken(
        token="ABC12",
        user_id=str(admin_user.id),
        expires_at=datetime.utcnow() + timedelta(days=7),
        max_visits=3,
        visit_count=0,
        is_used=False
    )
    db_session.add(token)
    db_session.commit()
    db_session.refresh(token)
    return token


# ============ Session Token Fixtures ============

@pytest.fixture
def h5_session_token(db_session, admin_user) -> SessionToken:
    """Create a sample H5 session token"""
    token = SessionToken(
        session_token="h5_session_test_token_12345",
        user_id=str(admin_user.id),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db_session.add(token)
    db_session.commit()
    db_session.refresh(token)
    return token


# ============ SMS Send Log Fixtures ============

@pytest.fixture
def sample_sms_log(db_session) -> SmsSendLog:
    """Create a sample SMS send log"""
    log = SmsSendLog(
        task_id="TASK001",
        user_id="USER001",
        phone_number="13800138000",
        template_id="TPL001",
        gateway_type="mock",
        status="success"
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    return log
