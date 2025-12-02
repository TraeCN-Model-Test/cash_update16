"""数据备份与恢复服务"""
import os
import shutil
import sqlite3
import datetime
from pathlib import Path
from typing import Optional
from cashlog.models.db import DB_PATH


class DataService:
    """数据服务类，处理备份和恢复操作"""
    
    @staticmethod
    def create_backup(output_path: Optional[str] = None, overwrite: bool = False) -> str:
        """
        创建数据库备份
        
        Args:
            output_path: 备份文件路径，如果为None则使用默认路径
            overwrite: 是否覆盖已有文件
            
        Returns:
            备份文件的绝对路径
            
        Raises:
            FileExistsError: 当文件已存在且overwrite为False时
            IOError: 当备份过程中出现IO错误时
            ValueError: 当路径无效时
        """
        # 确保原数据库文件存在
        if not os.path.exists(DB_PATH):
            raise IOError(f"原数据库文件不存在: {DB_PATH}")
        
        # 确定备份文件路径
        if not output_path:
            # 默认备份路径: 项目内的data/backups目录
            backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            today = datetime.datetime.now().strftime("%Y%m%d")
            output_path = os.path.join(backup_dir, f"backup_{today}.db")
        else:
            # 验证输出路径
            output_path = os.path.expanduser(output_path)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                raise ValueError(f"输出目录不存在: {output_dir}")
            
            # 验证文件后缀
            if not output_path.endswith(".db"):
                raise ValueError("备份文件必须以.db为后缀")
        
        # 检查文件是否已存在
        if os.path.exists(output_path) and not overwrite:
            raise FileExistsError(f"备份文件已存在: {output_path}，使用-f参数覆盖")
        
        try:
            # 执行备份
            shutil.copy2(DB_PATH, output_path)
            
            # 验证备份文件是否为有效的SQLite数据库
            if not DataService._is_valid_sqlite_db(output_path):
                os.remove(output_path)  # 删除无效的备份文件
                raise IOError("创建的备份文件无效")
            
            return os.path.abspath(output_path)
        except Exception as e:
            if isinstance(e, (FileExistsError, ValueError, IOError)):
                raise
            raise IOError(f"备份失败: {str(e)}")
    
    @staticmethod
    def restore_backup(input_path: str, backup_current: bool = True, confirm: bool = True) -> dict:
        """
        从备份文件恢复数据库
        
        Args:
            input_path: 备份文件路径
            backup_current: 是否先备份当前数据库
            confirm: 是否需要确认
            
        Returns:
            恢复结果信息
            
        Raises:
            FileNotFoundError: 当备份文件不存在时
            ValueError: 当备份文件无效时
            IOError: 当恢复过程中出现错误时
        """
        # 展开用户路径
        input_path = os.path.expanduser(input_path)
        
        # 检查备份文件是否存在
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"备份文件不存在: {input_path}")
        
        # 验证备份文件是否为有效的SQLite数据库
        if not DataService._is_valid_sqlite_db(input_path):
            raise ValueError("无效的SQLite数据库文件")
        
        # 如果需要，先备份当前数据库
        current_backup_path = None
        if backup_current and os.path.exists(DB_PATH):
            # 创建带时间戳的备份文件
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            current_backup_path = os.path.join(backup_dir, f"pre_restore_{timestamp}.db")
            shutil.copy2(DB_PATH, current_backup_path)
        
        try:
            # 获取恢复前的数据统计
            before_stats = DataService._get_database_stats() if os.path.exists(DB_PATH) else {}
            
            # 执行恢复
            shutil.copy2(input_path, DB_PATH)
            
            # 获取恢复后的数据统计
            after_stats = DataService._get_database_stats()
            
            return {
                "restored_from": os.path.abspath(input_path),
                "current_backup_path": current_backup_path,
                "before_stats": before_stats,
                "after_stats": after_stats
            }
        except Exception as e:
            # 如果发生错误，尝试恢复原来的数据库
            if current_backup_path and os.path.exists(current_backup_path):
                try:
                    shutil.copy2(current_backup_path, DB_PATH)
                except:
                    pass  # 忽略恢复失败的错误
            
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            raise IOError(f"恢复失败: {str(e)}")
    
    @staticmethod
    def _is_valid_sqlite_db(db_path: str) -> bool:
        """
        验证文件是否为有效的SQLite数据库
        
        Args:
            db_path: 数据库文件路径
            
        Returns:
            是否为有效的SQLite数据库
        """
        try:
            # SQLite数据库文件头标识
            with open(db_path, 'rb') as f:
                header = f.read(16)
                if header != b'SQLite format 3\x00':
                    return False
            
            # 尝试连接数据库
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            cursor.fetchall()
            conn.close()
            return True
        except:
            return False
    
    @staticmethod
    def _get_database_stats() -> dict:
        """
        获取数据库统计信息
        
        Returns:
            数据库统计信息
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 获取表信息
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            stats = {"tables": {}}
            for table in tables:
                table_name = table[0]
                # 获取表中的记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                stats["tables"][table_name] = count
            
            conn.close()
            return stats
        except:
            return {}
