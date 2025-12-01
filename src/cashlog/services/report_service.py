"""报表业务逻辑服务"""
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from cashlog.models.transaction import Transaction


class ReportService:
    """报表服务类"""

    @staticmethod
    def generate_monthly_report(db: Session, month: str = None) -> Dict[str, Any]:
        """
        生成月度收支报表

        Args:
            db: 数据库会话
            month: 月份，格式：YYYY-MM，默认为当前月

        Returns:
            报表数据，包含收入、支出、结余、分类统计等
        """
        # 如果未指定月份，使用当前月
        if not month:
            month = datetime.now().strftime("%Y-%m")

        # 验证月份格式
        try:
            if len(month) != 7 or month[4] != "-":
                raise ValueError("月份格式应为YYYY-MM")
            start_date = datetime.strptime(month + "-01", "%Y-%m-%d")
            # 计算下个月的第一天
            if start_date.month == 12:
                end_date = datetime.strptime(f"{start_date.year + 1}-01-01", "%Y-%m-%d")
            else:
                end_date = datetime.strptime(f"{start_date.year}-{start_date.month + 1:02d}-01", "%Y-%m-%d")
        except ValueError:
            raise ValueError("月份格式应为YYYY-MM")

        # 查询该月所有交易
        transactions = db.query(Transaction).filter(
            and_(Transaction.created_at >= start_date, Transaction.created_at < end_date)
        ).all()

        if not transactions:
            return {
                "month": month,
                "total_income": 0,
                "total_expense": 0,
                "balance": 0,
                "category_stats": {},
                "has_data": False
            }

        # 计算总收入和支出
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        total_expense = -sum(t.amount for t in transactions if t.amount < 0)
        balance = total_income - total_expense

        # 按分类统计
        category_stats = {}
        for transaction in transactions:
            if transaction.category not in category_stats:
                category_stats[transaction.category] = {
                    "income": 0,
                    "expense": 0,
                    "count": 0
                }
            
            if transaction.amount > 0:
                category_stats[transaction.category]["income"] += transaction.amount
            else:
                category_stats[transaction.category]["expense"] += -transaction.amount
            category_stats[transaction.category]["count"] += 1

        # 计算分类占比
        for category, stats in category_stats.items():
            if total_income > 0:
                stats["income_percentage"] = (stats["income"] / total_income) * 100
            else:
                stats["income_percentage"] = 0
            if total_expense > 0:
                stats["expense_percentage"] = (stats["expense"] / total_expense) * 100
            else:
                stats["expense_percentage"] = 0

        return {
            "month": month,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "category_stats": category_stats,
            "transaction_count": len(transactions),
            "has_data": True
        }

    @staticmethod
    def format_report(report_data: Dict[str, Any], format_type: str = "text") -> str:
        """
        格式化报表输出

        Args:
            report_data: 报表数据
            format_type: 输出格式，text 或 markdown

        Returns:
            格式化后的报表字符串
        """
        if not report_data["has_data"]:
            if format_type == "markdown":
                return f"# {report_data['month']} 月度收支报表\n\n暂无数据"
            else:
                return f"{report_data['month']} 月度收支报表\n\n暂无数据"

        if format_type == "markdown":
            return ReportService._format_report_markdown(report_data)
        else:
            return ReportService._format_report_text(report_data)

    @staticmethod
    def _format_report_text(report_data: Dict[str, Any]) -> str:
        """格式化为文本格式"""
        lines = []
        lines.append(f"{report_data['month']} 月度收支报表")
        lines.append("=" * 50)
        lines.append(f"总收入: {report_data['total_income']:.2f}")
        lines.append(f"总支出: {report_data['total_expense']:.2f}")
        lines.append(f"结余: {report_data['balance']:.2f}")
        lines.append(f"交易笔数: {report_data['transaction_count']}")
        lines.append("\n分类统计:")
        lines.append("-" * 50)

        for category, stats in sorted(
            report_data["category_stats"].items(),
            key=lambda x: x[1]["income"] + x[1]["expense"],
            reverse=True
        ):
            total = stats["income"] + stats["expense"]
            lines.append(f"{category}:")
            lines.append(f"  收入: {stats['income']:.2f} ({stats['income_percentage']:.1f}%)")
            lines.append(f"  支出: {stats['expense']:.2f} ({stats['expense_percentage']:.1f}%)")
            lines.append(f"  总金额: {total:.2f}")
            lines.append(f"  笔数: {stats['count']}")
            lines.append("-" * 50)

        return "\n".join(lines)

    @staticmethod
    def _format_report_markdown(report_data: Dict[str, Any]) -> str:
        """格式化为Markdown格式"""
        lines = []
        lines.append(f"# {report_data['month']} 月度收支报表")
        lines.append("")
        
        # 汇总信息
        lines.append("## 汇总信息")
        lines.append("| 项目 | 金额 |")
        lines.append("|-----|------|")
        lines.append(f"| 总收入 | {report_data['total_income']:.2f} |")
        lines.append(f"| 总支出 | {report_data['total_expense']:.2f} |")
        lines.append(f"| 结余 | {report_data['balance']:.2f} |")
        lines.append(f"| 交易笔数 | {report_data['transaction_count']} |")
        lines.append("")

        # 分类统计
        lines.append("## 分类统计")
        lines.append("| 分类 | 收入 | 收入占比 | 支出 | 支出占比 | 总金额 | 笔数 |")
        lines.append("|-----|------|---------|------|---------|-------|------|")

        for category, stats in sorted(
            report_data["category_stats"].items(),
            key=lambda x: x[1]["income"] + x[1]["expense"],
            reverse=True
        ):
            total = stats["income"] + stats["expense"]
            lines.append(
                f"| {category} | "
                f"{stats['income']:.2f} | "
                f"{stats['income_percentage']:.1f}% | "
                f"{stats['expense']:.2f} | "
                f"{stats['expense_percentage']:.1f}% | "
                f"{total:.2f} | "
                f"{stats['count']} |"
            )

        return "\n".join(lines)
