import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from passlib.context import CryptContext

from app.models.models import Base, User, UserRole, Debtor, DebtorStatus, Batch, BatchStatus
from app.models.models import Voucher, VoucherStatus, SMSTemplate, SMSTask, SMSTaskStatus
from app.models.models import H5User, Partner, SMSChannel, ChannelStatus, PaymentAccount, Config
from app.models.database import get_db
from app.core.security import create_access_token, create_h5_token, get_password_hash
from app.core.config import settings
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
        is_active=True
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
        is_active=True
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
        is_active=True
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
        is_active=True,
        is_locked=True,
        locked_until=datetime.utcnow() + timedelta(minutes=15),
        failed_login_attempts=5
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
def sample_batch(db_session, admin_user) -> Batch:
    """Create a sample batch"""
    batch = Batch(
        batch_no="BATCH-20240101-TEST01",
        name="Test Batch",
        description="Test batch description",
        status=BatchStatus.PENDING,
        created_by=admin_user.id
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture
def sample_debtor(db_session, sample_batch) -> Debtor:
    """Create a sample debtor"""
    debtor = Debtor(
        name="Zhang San",
        id_card="110101199001011234",
        phone="13800138000",
        address="Beijing",
        debt_amount=10000.0,
        status=DebtorStatus.ACTIVE,
        batch_id=sample_batch.id
    )
    db_session.add(debtor)
    db_session.commit()
    db_session.refresh(debtor)
    return debtor


@pytest.fixture
def sample_debtors(db_session, sample_batch) -> list:
    """Create multiple sample debtors"""
    debtors = []
    for i in range(5):
        debtor = Debtor(
            name=f" Debtor {i}",
            id_card=f"11010119900101{i:04d}",
            phone=f"1380013{i:04d}",
            address=f"Address {i}",
            debt_amount=1000.0 * (i + 1),
            status=DebtorStatus.ACTIVE,
            batch_id=sample_batch.id
        )
        debtors.append(debtor)
        db_session.add(debtor)
    db_session.commit()
    return debtors


# ============ Voucher Fixtures ============

@pytest.fixture
def sample_voucher(db_session, operator_user) -> Voucher:
    """Create a sample voucher"""
    voucher = Voucher(
        file_name="test.xlsx",
        file_path="/uploads/test.xlsx",
        file_size=1024,
        status=VoucherStatus.PENDING,
        uploaded_by=operator_user.id
    )
    db_session.add(voucher)
    db_session.commit()
    db_session.refresh(voucher)
    return voucher


# ============ SMS Fixtures ============

@pytest.fixture
def sample_template(db_session, admin_user) -> SMSTemplate:
    """Create a sample SMS template"""
    template = SMSTemplate(
        name="Debt Reminder",
        content="Dear {{name}}, your debt of {{amount}} is due.",
        variables="name,amount",
        is_active=True,
        created_by=admin_user.id
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def sample_task(db_session, sample_template, sample_batch, operator_user) -> SMSTask:
    """Create a sample SMS task"""
    task = SMSTask(
        task_no="SMS-20240101-TEST01",
        template_id=sample_template.id,
        channel_id=1,
        recipient_count=100,
        status=SMSTaskStatus.PENDING,
        created_by=operator_user.id
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


# ============ Channel Fixtures ============

@pytest.fixture
def sample_channel(db_session) -> SMSChannel:
    """Create a sample SMS channel"""
    channel = SMSChannel(
        name="Test Channel",
        provider="MockProvider",
        endpoint="http://localhost:8001",
        api_key="test-api-key",
        status=ChannelStatus.ACTIVE,
        priority=1,
        is_active=True
    )
    db_session.add(channel)
    db_session.commit()
    db_session.refresh(channel)
    return channel


# ============ H5 Fixtures ============

@pytest.fixture
def h5_user(db_session) -> H5User:
    """Create an H5 user"""
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
        name="Test Partner",
        api_key="test-api-key-123",
        secret_key="test-secret-key-456",
        is_active=True,
        rate_limit=100,
        daily_limit=10000
    )
    db_session.add(partner)
    db_session.commit()
    db_session.refresh(partner)
    return partner


# ============ Config Fixtures ============

@pytest.fixture
def sample_config(db_session, admin_user) -> Config:
    """Create a sample config"""
    config = Config(
        config_key="MAX_QUERY_LIMIT",
        config_value="1000",
        description="Maximum query limit",
        is_active=True,
        changed_by=admin_user.id
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
        bank_name="ICBC",
        account_no="6222021234567890",
        account_name="Test Company",
        bank_code="ICBC",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account
