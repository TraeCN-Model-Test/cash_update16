"""交易服务单元测试"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cashlog.models.db import Base, get_db
from cashlog.models.transaction import Transaction
from cashlog.services.transaction_service import TransactionService

# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_transaction_success(db_session):
    """测试成功创建交易记录"""
    transaction_data = {
        "amount": "100.50",
        "category": "工资",
        "tags": "收入,月度",
        "notes": "12月份工资"
    }
    
    transaction = TransactionService.create_transaction(db_session, transaction_data)
    
    assert transaction.id is not None
    assert transaction.amount == 100.50
    assert transaction.category == "工资"
    assert transaction.tags == "收入,月度"
    assert transaction.notes == "12月份工资"


def test_create_transaction_invalid_amount(db_session):
    """测试金额格式错误"""
    transaction_data = {
        "amount": "invalid",
        "category": "工资"
    }
    
    with pytest.raises(ValueError, match="金额需为数字"):
        TransactionService.create_transaction(db_session, transaction_data)


def test_create_transaction_missing_category(db_session):
    """测试缺少分类"""
    transaction_data = {
        "amount": "100.50"
    }
    
    with pytest.raises(ValueError, match="分类为必填项"):
        TransactionService.create_transaction(db_session, transaction_data)


def test_create_transaction_with_datetime(db_session):
    """测试带时间的交易创建"""
    transaction_data = {
        "amount": "100.50",
        "category": "工资",
        "created_at": "2023-12-01 10:00:00"
    }
    
    transaction = TransactionService.create_transaction(db_session, transaction_data)
    
    assert transaction.created_at.strftime("%Y-%m-%d %H:%M:%S") == "2023-12-01 10:00:00"


def test_create_transaction_invalid_datetime(db_session):
    """测试时间格式错误"""
    transaction_data = {
        "amount": "100.50",
        "category": "工资",
        "created_at": "2023/12/01"
    }
    
    with pytest.raises(ValueError, match="时间格式不正确"):
        TransactionService.create_transaction(db_session, transaction_data)


def test_get_transactions_by_month(db_session):
    """测试按月份查询交易"""
    # 创建测试数据
    TransactionService.create_transaction(db_session, {
        "amount": "100.50",
        "category": "工资",
        "created_at": "2023-12-01 10:00:00"
    })
    TransactionService.create_transaction(db_session, {
        "amount": "200.50",
        "category": "奖金",
        "created_at": "2023-12-15 10:00:00"
    })
    TransactionService.create_transaction(db_session, {
        "amount": "50.00",
        "category": "工资",
        "created_at": "2023-11-01 10:00:00"
    })
    
    # 查询12月交易
    transactions = TransactionService.get_transactions(db_session, month="2023-12")
    
    assert len(transactions) == 2
    assert all(t.created_at.strftime("%Y-%m") == "2023-12" for t in transactions)


def test_get_transactions_by_category(db_session):
    """测试按分类查询交易"""
    # 创建测试数据
    TransactionService.create_transaction(db_session, {
        "amount": "100.50",
        "category": "工资"
    })
    TransactionService.create_transaction(db_session, {
        "amount": "200.50",
        "category": "奖金"
    })
    
    # 查询工资分类
    transactions = TransactionService.get_transactions(db_session, category="工资")
    
    assert len(transactions) == 1
    assert transactions[0].category == "工资"


def test_get_transactions_by_type(db_session):
    """测试按交易类型查询"""
    # 创建测试数据
    TransactionService.create_transaction(db_session, {
        "amount": "100.50",
        "category": "工资"
    })
    TransactionService.create_transaction(db_session, {
        "amount": "-50.00",
        "category": "餐饮"
    })
    
    # 查询收入
    income_transactions = TransactionService.get_transactions(db_session, transaction_type="income")
    assert len(income_transactions) == 1
    assert income_transactions[0].amount > 0
    
    # 查询支出
    expense_transactions = TransactionService.get_transactions(db_session, transaction_type="expense")
    assert len(expense_transactions) == 1
    assert expense_transactions[0].amount < 0


def test_get_transaction_by_id(db_session):
    """测试按ID查询交易"""
    # 创建测试数据
    transaction = TransactionService.create_transaction(db_session, {
        "amount": "100.50",
        "category": "工资"
    })
    
    # 查询
    found_transaction = TransactionService.get_transaction_by_id(db_session, transaction.id)
    assert found_transaction is not None
    assert found_transaction.id == transaction.id
    
    # 查询不存在的ID
    not_found = TransactionService.get_transaction_by_id(db_session, 999)
    assert not_found is None
