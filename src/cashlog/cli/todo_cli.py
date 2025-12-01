"""待办事项相关命令行接口"""
import click
from typing import Optional
from cashlog.models.db import get_db, init_db
from cashlog.services.todo_service import TodoService
from cashlog.utils.formatter import Formatter


@click.group()
def todo():
    """待办事项管理命令组"""
    pass


@todo.command()
@click.option("-c", "--content", required=True, help="待办内容")
@click.option("-C", "--category", required=True, help="分类")
@click.option("-t", "--tags", help="标签，多个标签用逗号分隔")
@click.option("-d", "--deadline", help="截止时间，格式：YYYY-MM-DD HH:MM:SS")
def add(content: str, category: str, tags: Optional[str], deadline: Optional[str]):
    """
    添加待办事项
    
    示例:
    cashlog todo add -c "完成项目报告" -C 工作 -t "重要,紧急" -d 2023-12-31
    cashlog todo add -c "购物" -C 个人 -t "日常" -d 2023-12-15 18:00:00
    """
    init_db()  # 确保数据库已初始化
    
    try:
        todo_data = {
            "content": content,
            "category": category,
            "tags": tags,
            "deadline": deadline
        }
        
        db = next(get_db())
        todo = TodoService.create_todo(db, todo_data)
        Formatter.print_success(f"待办事项已添加 (ID: {todo.id})")
    except ValueError as e:
        Formatter.print_error(str(e))
    except Exception as e:
        Formatter.print_error(f"添加待办事项失败: {str(e)}")


@todo.command()
@click.argument("todo_id")
@click.argument("status", type=click.Choice(["todo", "doing", "done"]))
def update(todo_id: str, status: str):
    """
    更新待办事项状态
    
    示例:
    cashlog todo update 1 doing  # 将ID为1的待办事项标记为进行中
    cashlog todo update 2 done    # 将ID为2的待办事项标记为已完成
    """
    init_db()  # 确保数据库已初始化
    
    try:
        # 验证ID格式
        try:
            todo_id_int = int(todo_id)
        except ValueError:
            Formatter.print_error("待办事项ID必须为数字")
            return
        
        db = next(get_db())
        todo = TodoService.update_todo_status(db, todo_id_int, status)
        Formatter.print_success(f"待办事项(ID: {todo.id})状态已更新为: {todo.status_text}")
    except ValueError as e:
        Formatter.print_error(str(e))
    except Exception as e:
        Formatter.print_error(f"更新待办事项状态失败: {str(e)}")


@todo.command()
@click.option("-s", "--status", type=click.Choice(["todo", "doing", "done"]), help="状态")
@click.option("-c", "--category", help="分类")
@click.option("-t", "--tags", help="标签，多个标签用逗号分隔")
@click.option("--before", help="截止时间之前，格式：YYYY-MM-DD")
@click.option("--after", help="截止时间之后，格式：YYYY-MM-DD")
def list(status: Optional[str], category: Optional[str], tags: Optional[str], before: Optional[str], after: Optional[str]):
    """
    列出待办事项
    
    示例:
    cashlog todo list  # 列出所有待办事项
    cashlog todo list -s todo  # 列出待办状态的事项
    cashlog todo list -c 工作 --before 2023-12-31  # 列出工作分类且截止日期在2023-12-31之前的事项
    """
    init_db()  # 确保数据库已初始化
    
    try:
        filters = {}
        if status:
            filters["status"] = status
        if category:
            filters["category"] = category
        if tags:
            filters["tags"] = tags
        if before:
            filters["deadline_before"] = before
        if after:
            filters["deadline_after"] = after
        
        db = next(get_db())
        todos = TodoService.get_todos(db, **filters)
        
        # 格式化并打印
        formatted_data = Formatter.format_todos(todos)
        headers = {
            "id": "ID",
            "content": "内容",
            "category": "分类",
            "status": "状态",
            "tags": "标签",
            "deadline": "截止时间",
            "created_at": "创建时间"
        }
        
        if filters:
            Formatter.print_info(f"查询条件: {filters}")
        Formatter.print_table(formatted_data, headers)
        
    except ValueError as e:
        Formatter.print_error(str(e))
    except Exception as e:
        Formatter.print_error(f"查询待办事项失败: {str(e)}")
