"""待办事项业务逻辑服务"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from cashlog.models.todo import Todo, TodoStatus


class TodoService:
    """待办事项服务类"""

    @staticmethod
    def create_todo(db: Session, todo_data: Dict[str, Any]) -> Todo:
        """
        创建新待办事项

        Args:
            db: 数据库会话
            todo_data: 待办事项数据，包含content、category等

        Returns:
            创建的待办事项对象
        """
        # 验证必填字段
        if not todo_data.get("content"):
            raise ValueError("待办内容为必填项")
        if not todo_data.get("category"):
            raise ValueError("分类为必填项")

        # 创建待办对象
        todo = Todo(
            content=todo_data["content"].strip(),
            category=todo_data["category"].strip(),
            tags=todo_data.get("tags", "").strip() or None
        )

        # 如果提供了截止时间，设置截止时间
        if todo_data.get("deadline"):
            try:
                # 支持多种时间格式
                formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]
                for fmt in formats:
                    try:
                        todo.deadline = datetime.strptime(todo_data["deadline"], fmt)
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError("截止时间格式不正确，请使用YYYY-MM-DD HH:MM:SS格式")
            except ValueError as e:
                raise e

        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo

    @staticmethod
    def get_todos(db: Session, **filters) -> List[Todo]:
        """
        查询待办事项列表

        Args:
            db: 数据库会话
            filters: 查询条件，包括status、category、deadline等

        Returns:
            待办事项列表
        """
        query = db.query(Todo)

        # 按状态筛选
        if filters.get("status"):
            status_map = {
                "todo": TodoStatus.TODO,
                "doing": TodoStatus.DOING,
                "done": TodoStatus.DONE
            }
            status = status_map.get(filters["status"].lower())
            if status:
                query = query.filter(Todo.status == status)
            else:
                raise ValueError("状态无效，可选值：todo, doing, done")

        # 按分类筛选
        if filters.get("category"):
            query = query.filter(Todo.category == filters["category"])

        # 按截止时间筛选
        if filters.get("deadline_before"):
            try:
                deadline = datetime.strptime(filters["deadline_before"] + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                query = query.filter(Todo.deadline <= deadline)
            except ValueError:
                raise ValueError("截止时间格式应为YYYY-MM-DD")

        if filters.get("deadline_after"):
            try:
                deadline = datetime.strptime(filters["deadline_after"], "%Y-%m-%d")
                query = query.filter(Todo.deadline >= deadline)
            except ValueError:
                raise ValueError("截止时间格式应为YYYY-MM-DD")

        # 按标签筛选（包含任一标签即可）
        if filters.get("tags"):
            tags = filters["tags"].split(",")
            tag_filters = [Todo.tags.like(f"%{tag.strip()}%") for tag in tags if tag.strip()]
            if tag_filters:
                query = query.filter(or_(*tag_filters))

        # 按创建时间排序
        query = query.order_by(Todo.created_at.desc())

        return query.all()

    @staticmethod
    def update_todo_status(db: Session, todo_id: int, status: str) -> Todo:
        """
        更新待办事项状态

        Args:
            db: 数据库会话
            todo_id: 待办事项ID
            status: 新状态

        Returns:
            更新后的待办事项对象
        """
        # 验证状态值
        status_map = {
            "todo": TodoStatus.TODO,
            "doing": TodoStatus.DOING,
            "done": TodoStatus.DONE
        }
        new_status = status_map.get(status.lower())
        if not new_status:
            raise ValueError("状态无效，可选值：todo, doing, done")

        # 查询待办事项
        todo = db.query(Todo).filter(Todo.id == todo_id).first()
        if not todo:
            raise ValueError(f"待办事项ID {todo_id} 不存在")

        # 更新状态
        todo.status = new_status
        todo.updated_at = datetime.now()
        db.commit()
        db.refresh(todo)
        return todo

    @staticmethod
    def get_todo_by_id(db: Session, todo_id: int) -> Optional[Todo]:
        """
        根据ID获取待办事项

        Args:
            db: 数据库会话
            todo_id: 待办事项ID

        Returns:
            待办事项对象或None
        """
        return db.query(Todo).filter(Todo.id == todo_id).first()
