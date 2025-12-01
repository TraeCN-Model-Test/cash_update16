"""待办事项服务单元测试"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cashlog.models.db import Base, get_db
from cashlog.models.todo import Todo, TodoStatus
from cashlog.services.todo_service import TodoService

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


def test_create_todo_success(db_session):
    """测试成功创建待办事项"""
    todo_data = {
        "content": "完成项目报告",
        "category": "工作",
        "tags": "重要,紧急",
        "deadline": "2023-12-31 18:00:00"
    }
    
    todo = TodoService.create_todo(db_session, todo_data)
    
    assert todo.id is not None
    assert todo.content == "完成项目报告"
    assert todo.category == "工作"
    assert todo.tags == "重要,紧急"
    assert todo.status == TodoStatus.TODO
    assert todo.deadline.strftime("%Y-%m-%d %H:%M:%S") == "2023-12-31 18:00:00"


def test_create_todo_missing_content(db_session):
    """测试缺少待办内容"""
    todo_data = {
        "category": "工作"
    }
    
    with pytest.raises(ValueError, match="待办内容为必填项"):
        TodoService.create_todo(db_session, todo_data)


def test_create_todo_missing_category(db_session):
    """测试缺少分类"""
    todo_data = {
        "content": "完成项目报告"
    }
    
    with pytest.raises(ValueError, match="分类为必填项"):
        TodoService.create_todo(db_session, todo_data)


def test_create_todo_invalid_deadline(db_session):
    """测试截止时间格式错误"""
    todo_data = {
        "content": "完成项目报告",
        "category": "工作",
        "deadline": "2023/12/31"
    }
    
    with pytest.raises(ValueError, match="截止时间格式不正确"):
        TodoService.create_todo(db_session, todo_data)


def test_get_todos_by_status(db_session):
    """测试按状态查询待办事项"""
    # 创建测试数据
    TodoService.create_todo(db_session, {
        "content": "任务1",
        "category": "工作"
    })
    todo2 = TodoService.create_todo(db_session, {
        "content": "任务2",
        "category": "工作"
    })
    # 更新第二个任务状态
    TodoService.update_todo_status(db_session, todo2.id, "doing")
    
    # 查询待办状态
    todo_todos = TodoService.get_todos(db_session, status="todo")
    assert len(todo_todos) == 1
    assert todo_todos[0].status == TodoStatus.TODO
    
    # 查询进行中状态
    doing_todos = TodoService.get_todos(db_session, status="doing")
    assert len(doing_todos) == 1
    assert doing_todos[0].status == TodoStatus.DOING


def test_get_todos_by_category(db_session):
    """测试按分类查询待办事项"""
    # 创建测试数据
    TodoService.create_todo(db_session, {
        "content": "任务1",
        "category": "工作"
    })
    TodoService.create_todo(db_session, {
        "content": "任务2",
        "category": "个人"
    })
    
    # 查询工作分类
    work_todos = TodoService.get_todos(db_session, category="工作")
    assert len(work_todos) == 1
    assert work_todos[0].category == "工作"


def test_get_todos_by_deadline(db_session):
    """测试按截止时间查询待办事项"""
    # 创建测试数据
    TodoService.create_todo(db_session, {
        "content": "任务1",
        "category": "工作",
        "deadline": "2023-12-15 18:00:00"
    })
    TodoService.create_todo(db_session, {
        "content": "任务2",
        "category": "工作",
        "deadline": "2023-12-25 18:00:00"
    })
    
    # 查询截止时间之前
    before_todos = TodoService.get_todos(db_session, deadline_before="2023-12-20")
    assert len(before_todos) == 1
    assert before_todos[0].content == "任务1"
    
    # 查询截止时间之后
    after_todos = TodoService.get_todos(db_session, deadline_after="2023-12-20")
    assert len(after_todos) == 1
    assert after_todos[0].content == "任务2"


def test_update_todo_status_success(db_session):
    """测试成功更新待办事项状态"""
    # 创建测试数据
    todo = TodoService.create_todo(db_session, {
        "content": "任务1",
        "category": "工作"
    })
    
    # 更新状态为doing
    updated_todo = TodoService.update_todo_status(db_session, todo.id, "doing")
    assert updated_todo.status == TodoStatus.DOING
    
    # 更新状态为done
    updated_todo = TodoService.update_todo_status(db_session, todo.id, "done")
    assert updated_todo.status == TodoStatus.DONE


def test_update_todo_status_invalid(db_session):
    """测试无效的状态值"""
    # 创建测试数据
    todo = TodoService.create_todo(db_session, {
        "content": "任务1",
        "category": "工作"
    })
    
    with pytest.raises(ValueError, match="状态无效"):
        TodoService.update_todo_status(db_session, todo.id, "invalid")


def test_update_todo_status_not_found(db_session):
    """测试更新不存在的待办事项"""
    with pytest.raises(ValueError, match="待办事项ID 999 不存在"):
        TodoService.update_todo_status(db_session, 999, "doing")


def test_get_todo_by_id(db_session):
    """测试按ID查询待办事项"""
    # 创建测试数据
    todo = TodoService.create_todo(db_session, {
        "content": "任务1",
        "category": "工作"
    })
    
    # 查询
    found_todo = TodoService.get_todo_by_id(db_session, todo.id)
    assert found_todo is not None
    assert found_todo.id == todo.id
    
    # 查询不存在的ID
    not_found = TodoService.get_todo_by_id(db_session, 999)
    assert not_found is None
