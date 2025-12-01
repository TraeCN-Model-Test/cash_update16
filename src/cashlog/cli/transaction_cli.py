"""交易相关命令行接口"""
import click
from typing import Optional
from cashlog.models.db import get_db, init_db
from cashlog.services.transaction_service import TransactionService
from cashlog.utils.formatter import Formatter


@click.group()
def transaction():
    """交易管理命令组"""
    pass


@transaction.command()
@click.option("-a", "--amount", required=True, help="金额，收入为正，支出为负")
@click.option("-c", "--category", required=True, help="分类")
@click.option("-t", "--tags", help="标签，多个标签用逗号分隔")
@click.option("-n", "--notes", help="备注")
@click.option("-d", "--date", help="日期时间，格式：YYYY-MM-DD HH:MM:SS")
def add(amount: str, category: str, tags: Optional[str], notes: Optional[str], date: Optional[str]):
    """
    添加交易记录
    
    示例:
    cashlog transaction add -a 100.50 -c 工资 -t "收入,月度"
    cashlog transaction add -a -50.00 -c 餐饮 -t "支出,日常" -n "午餐"
    """
    init_db()  # 确保数据库已初始化
    
    try:
        transaction_data = {
            "amount": amount,
            "category": category,
            "tags": tags,
            "notes": notes
        }
        if date:
            transaction_data["created_at"] = date
        
        db = next(get_db())
        transaction = TransactionService.create_transaction(db, transaction_data)
        Formatter.print_success(f"交易记录已添加 (ID: {transaction.id})")
    except ValueError as e:
        Formatter.print_error(str(e))
    except Exception as e:
        Formatter.print_error(f"添加交易记录失败: {str(e)}")


@transaction.command()
@click.option("-m", "--month", help="月份，格式：YYYY-MM")
@click.option("-c", "--category", help="分类")
@click.option("-t", "--tags", help="标签，多个标签用逗号分隔")
@click.option("--type", type=click.Choice(["income", "expense"]), help="交易类型: income(收入), expense(支出)")
def list(month: Optional[str], category: Optional[str], tags: Optional[str], type: Optional[str]):
    """
    列出交易记录
    
    示例:
    cashlog transaction list  # 列出所有交易
    cashlog transaction list -m 2023-10  # 列出10月交易
    cashlog transaction list --type income  # 列出所有收入
    cashlog transaction list -c 餐饮 -t "午餐,晚餐"  # 按分类和标签筛选
    """
    init_db()  # 确保数据库已初始化
    
    try:
        filters = {}
        if month:
            filters["month"] = month
        if category:
            filters["category"] = category
        if tags:
            filters["tags"] = tags
        if type:
            filters["transaction_type"] = type
        
        db = next(get_db())
        transactions = TransactionService.get_transactions(db, **filters)
        
        # 格式化并打印
        formatted_data = Formatter.format_transactions(transactions)
        headers = {
            "id": "ID",
            "amount": "金额",
            "type": "类型",
            "category": "分类",
            "tags": "标签",
            "notes": "备注",
            "created_at": "时间"
        }
        
        if filters:
            Formatter.print_info(f"查询条件: {filters}")
        Formatter.print_table(formatted_data, headers)
        
    except ValueError as e:
        Formatter.print_error(str(e))
    except Exception as e:
        Formatter.print_error(f"查询交易记录失败: {str(e)}")
