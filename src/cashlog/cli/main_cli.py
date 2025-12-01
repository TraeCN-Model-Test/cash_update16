"""主命令行接口"""
import click
from cashlog.cli.transaction_cli import transaction
from cashlog.cli.todo_cli import todo
from cashlog.cli.report_cli import report


@click.group()
@click.version_option("0.1.0", "-v", "--version")
def cli():
    """
    轻量化本地记账 / 待办 CLI 工具
    
    用于管理个人收支和待办事项的命令行工具，数据存储在本地SQLite数据库中。
    """
    pass


# 注册子命令
cli.add_command(transaction)
cli.add_command(todo)
cli.add_command(report)


if __name__ == "__main__":
    cli()
