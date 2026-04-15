import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Import Base from models.py
from app.models.models import Base

# Import enums from models.py
from app.models.models import (
    DebtorStatus, BatchStatus, VoucherStatus, SMSTaskStatus,
    SmsTemplateStatus, ChannelStatus, AttemptType, AIStatus, ImportTaskStatus,
    CaseBatch, PaymentVoucher, SmsTemplate, SmsTask, SmsSendLog,
    SmsChannel, SystemConfig, ConfigChangeLog, ImportTask, ApiAccessLog,
    Captcha, Partner, Admin, AdminSession, Debtor, PaymentAccount,
    AccessToken, SessionToken, FailedAttempt
)

# Import User from user.py
from app.models.user import User, UserRole, UserStatus

# Import database dependency
from app.models.database import get_db

# Import security functions
from app.core.security import create_access_token, create_h5_token, get_password_hash

# Import settings
from app.core.config import settings

# Import main app
from app.main import app

# Test database URL - SQLite in-memory for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============ User Fixtures ============

@pytest.fixture
def admin_user(db_session) -> User:
    """Create an admin user"""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_superadmin=False
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
        status=UserStatus.ACTIVE,
        is_superadmin=False,
        login_attempts=5,
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
        batch_id="BATCH-20240101-TEST01",
        batch_name="Test Batch",
        client_name="Test Client",
        partner_id="PARTNER001",
        commission_date=datetime.utcnow(),
        status=BatchStatus.ACTIVE.value,
        remark="Test batch description"
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
def h5_user(db_session) -> Debtor:
    """Create an H5 user (Debtor with phone for H5 auth)"""
    debtor = Debtor(
        debtor_number="H520240001",
        name="H5 User",
        id_card="110101199001019999",
        encrypted_phone="13900139000",  # Stored encrypted
        phone_nonce="h5_nonce",
        phone_tag="h5_tag",
        status=DebtorStatus.ACTIVE
    )
    db_session.add(debtor)
    db_session.commit()
    db_session.refresh(debtor)
    return debtor


@pytest.fixture
def h5_token(h5_user) -> str:
    """Create H5 access token"""
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
        is_api_enabled=True,
        is_revoked=False,
        rate_limit_per_minute=60,
        rate_limit_per_day=10000
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
