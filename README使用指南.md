# cashlog 工具使用指南

## 概述

cashlog 是一款轻量化本地记账/待办 CLI 工具，用于管理个人收支和待办事项，所有数据存储在本地SQLite数据库中，确保数据隐私和安全性。

## 基本操作

### 查看帮助信息

```bash
# 查看主帮助
python main.py --help

# 查看版本
python main.py --version
```

## 交易管理功能

### 添加交易记录

```bash
# 添加一笔收入
python main.py transaction add -a 5000.00 -c 工资 -t 收入,月度 -n "12月份工资"

# 添加一笔支出
python main.py transaction add -a -150.00 -c 餐饮 -t 日常,午餐 -n "工作日午餐"

# 带时间的交易（可选，默认为当前时间）
python main.py transaction add -a 200.00 -c 交通 -t 地铁 -n "上下班地铁费" -d "2024-12-01 08:30:00"
```

**参数说明**：
- `-a, --amount`：金额（必需），负数表示支出，正数表示收入
- `-c, --category`：分类（必需）
- `-t, --tags`：标签，多个标签用逗号分隔
- `-n, --notes`：备注
- `-d, --datetime`：交易时间，格式为 "YYYY-MM-DD HH:MM:SS"

### 列出交易记录

```bash
# 列出所有交易记录
python main.py transaction list

# 列出指定月份的交易
python main.py transaction list -m 2024-12

# 按分类筛选
python main.py transaction list -c 餐饮

# 按标签筛选
python main.py transaction list -t 收入

# 按交易类型筛选（收入/支出）
python main.py transaction list --type income
python main.py transaction list --type expense

# 组合筛选
python main.py transaction list -m 2024-12 -c 餐饮 -t 午餐
```

**参数说明**：
- `-m, --month`：月份，格式为 "YYYY-MM"
- `-c, --category`：分类
- `-t, --tags`：标签
- `--type`：交易类型，可选值：income（收入）、expense（支出）

## 待办事项管理

### 添加待办事项

```bash
# 添加一个待办事项
python main.py todo add -c "完成项目报告" -C 工作 -t 重要,紧急 -d "2024-12-10 18:00:00"

# 添加无截止时间的待办事项
python main.py todo add -c "学习Python新特性" -C 学习 -t 自我提升
```

**参数说明**：
- `-c, --content`：待办内容（必需）
- `-C, --category`：分类（必需）
- `-t, --tags`：标签，多个标签用逗号分隔
- `-d, --deadline`：截止时间，格式为 "YYYY-MM-DD HH:MM:SS"

### 更新待办事项状态

```bash
# 更新待办事项状态为进行中
python main.py todo update 1 doing

# 更新待办事项状态为已完成
python main.py todo update 1 done

# 更新待办事项状态为已取消
python main.py todo update 1 cancelled
```

**参数说明**：
- 第一个参数：待办事项ID
- 第二个参数：状态，可选值：todo（待办）、doing（进行中）、done（已完成）、cancelled（已取消）

### 列出待办事项

```bash
# 列出所有待办事项
python main.py todo list

# 按状态筛选
python main.py todo list -s todo      # 只显示待办
python main.py todo list -s doing    # 只显示进行中
python main.py todo list -s done     # 只显示已完成

# 按分类筛选
python main.py todo list -c 工作

# 按截止时间筛选（只显示今天的待办）
python main.py todo list --deadline today

# 组合筛选
python main.py todo list -s todo -c 工作 --deadline today
```

**参数说明**：
- `-s, --status`：状态，可选值：todo、doing、done、cancelled
- `-c, --category`：分类
- `--deadline`：截止时间筛选，可选值：today（今天）、week（本周）

## 报表功能

### 生成月度收支报表

```bash
# 生成当前月份的报表
python main.py report monthly

# 生成指定月份的报表
python main.py report monthly -m 2024-12

# 生成Markdown格式报表（默认是纯文本格式）
python main.py report monthly -f markdown
```

**参数说明**：
- `-m, --month`：月份，格式为 "YYYY-MM"，默认为当前月份
- `-f, --format`：输出格式，可选值：text（纯文本）、markdown，默认为text

## 数据存储

- 所有数据存储在本地SQLite数据库中
- 数据库文件会自动创建在项目目录中
- 支持的数据类型：交易记录、待办事项
- 交易记录包含：金额、分类、标签、备注、时间
- 待办事项包含：内容、分类、标签、截止时间、状态

## 实际使用示例

### 日常记账流程

```bash
# 1. 早上上班，记录地铁费用
python main.py transaction add -a -8.00 -c 交通 -t 地铁 -n "早班地铁"

# 2. 中午吃饭，记录午餐费用
python main.py transaction add -a -35.00 -c 餐饮 -t 午餐 -n "商务午餐"

# 3. 收到工资，记录收入
python main.py transaction add -a 15000.00 -c 工资 -t 收入,月度 -n "12月份工资"

# 4. 月底查看月度报表
python main.py report monthly -m 2024-12 -f markdown > 2024年12月收支报表.md
```

### 待办事项管理流程

```bash
# 1. 早上规划一天的任务
python main.py todo add -c "完成代码审核" -C 工作 -t 重要 -d "2024-12-01 12:00:00"
python main.py todo add -c "购买办公用品" -C 工作 -t 次要 -d "2024-12-01 15:00:00"

# 2. 开始工作，更新状态
python main.py todo update 1 doing

# 3. 完成任务，更新状态
python main.py todo update 1 done

# 4. 下班前检查今日待办
python main.py todo list -s todo --deadline today
```

## 注意事项

1. 金额格式必须为数字（例如：100.50），负数表示支出
2. 时间格式必须为 "YYYY-MM-DD HH:MM:SS"
3. 标签之间使用逗号分隔，不要包含空格
4. 所有数据存储在本地，卸载程序时请记得备份数据
5. 首次使用时会自动初始化数据库

## 常见问题

**Q: 如何备份我的数据？**
A: 找到生成的SQLite数据库文件（通常在项目目录下），直接复制该文件即可。

**Q: 如何删除错误的交易记录？**
A: 目前版本暂不支持删除功能，后续版本会添加。

**Q: 可以自定义分类和标签吗？**
A: 是的，分类和标签完全自定义，系统会自动记录和识别您使用过的分类和标签。