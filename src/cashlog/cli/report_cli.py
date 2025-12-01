"""报表相关命令行接口"""
import click
from typing import Optional
from cashlog.models.db import get_db, init_db
from cashlog.services.report_service import ReportService
from cashlog.utils.formatter import Formatter


@click.group()
def report():
    """报表管理命令组"""
    pass


@report.command()
@click.option("-m", "--month", help="月份，格式：YYYY-MM，默认为当前月")
@click.option("--format", type=click.Choice(["text", "markdown"]), default="text", help="输出格式，默认为text")
def monthly(month: Optional[str], format: str):
    """
    生成月度收支报表
    
    示例:
    cashlog report monthly  # 生成当前月报表
    cashlog report monthly -m 2023-10  # 生成指定月份报表
    cashlog report monthly --format markdown  # 生成Markdown格式报表
    """
    init_db()  # 确保数据库已初始化
    
    try:
        db = next(get_db())
        report_data = ReportService.generate_monthly_report(db, month)
        formatted_report = ReportService.format_report(report_data, format)
        
        if not report_data["has_data"]:
            Formatter.print_info(f"{month or '当前月'} 暂无交易数据")
        
        # 打印报表
        from rich.console import Console
        console = Console()
        console.print(formatted_report)
        
    except ValueError as e:
        Formatter.print_error(str(e))
    except Exception as e:
        Formatter.print_error(f"生成报表失败: {str(e)}")
