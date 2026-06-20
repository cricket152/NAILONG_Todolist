# TodoList (PyQt6)

一个基于 PyQt6 的 Windows 桌面待办事项应用，支持按截止日期（DDL）、每日、每周三种任务类型管理，提供到期提醒、数据导出、系统托盘等实用功能。

## 功能特性

### 任务管理
- **三种任务类型**：DDL 任务（带描述与截止日期）、每日任务、每周任务，分标签页管理
- **增删改查**：添加、编辑、删除任务，支持优先级（高/中/低）与状态（待完成/已完成）筛选
- **删除撤销**：删除任务后 5 秒内可按 `Ctrl+Z` 撤销（软删除机制，数据不丢失）
- **搜索高亮**：关键字搜索任务标题，匹配文本高亮显示

### 提醒与统计
- **到期通知**：后台定时检测超时任务，通过系统托盘气泡提醒
- **每周自动重置**：每周任务按 ISO 周自动重置为待完成，错过开机时间也能补偿重置
- **状态栏汇总**：实时显示今日到期、超时、未完成任务数量

### 系统集成
- **系统托盘**：最小化到托盘，托盘双击唤出窗口
- **开机自启**：可选开机自动启动
- **数据导出**：支持导出为 JSON 或 CSV 格式（`Ctrl+Shift+E`）

### 界面
- Coffee & Cream 浅色主题，自定义 QSS 样式
- 高 DPI 自适应
- 任务表格自定义委托（复选框、删除按钮、搜索高亮）

## 技术栈

- **Python 3.9+**
- **PyQt6** (GUI 框架)
- **sqlite3** (数据存储，标准库)
- **PyInstaller** (打包为单文件 exe)

## 项目结构

```
TodoList_Pyqt6/
├── main.py                      # 入口
├── requirements.txt
├── TodoList.spec                # PyInstaller 打包配置
├── resources/
│   ├── style.qss                # 主题样式表
│   ├── app_icon2.png            # 应用图标
│   ├── down_arrow.svg
│   └── up_arrow.svg
└── todo_app/
    ├── __init__.py              # 应用初始化（QSS 加载、数据库初始化）
    ├── database.py              # 数据库管理（sqlite3，含迁移与软删除）
    ├── models.py                # Task 数据模型
    ├── utils.py                 # 资源路径、数据目录、开机自启工具
    ├── export_util.py           # JSON/CSV 导出
    └── ui/
        ├── main_window.py       # 主窗口
        ├── task_table_model.py  # 任务表格模型（QAbstractTableModel）
        ├── task_dialog.py       # 添加/编辑任务弹窗
        ├── today_task_dialog.py # 今日任务汇总弹窗
        ├── checkbox_delegate.py # 复选框委托
        ├── delete_delegate.py   # 删除按钮委托
        ├── highlight_delegate.py# 搜索高亮委托
        ├── settings_dialog.py   # 设置弹窗
        └── tray_manager.py      # 系统托盘管理
```

## 安装与运行

### 开发模式

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

开发模式下，数据库文件存放在项目根目录的 `TodoListPyQt6/` 子目录中。

### 打包为 exe

需要使用安装了 PyQt6 的 Python 环境进行打包：

```bash
# 确保环境中已安装 PyQt6 和 pyinstaller
pip install PyQt6 pyinstaller

# 打包
python -m PyInstaller TodoList.spec --noconfirm --clean
```

生成的可执行文件位于 `dist/TodoList.exe`。

打包模式下，数据库文件存放在 `%APPDATA%/TodoListPyQt6/` 目录中。

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Z` | 撤销最近一次删除 |
| `Ctrl+Shift+E` | 导出任务 |

## 数据说明

- 任务数据存储在 SQLite 数据库中
- 支持数据库 schema 版本迁移，升级版本时自动执行增量迁移
- 删除操作为软删除（标记 `deleted_at` 时间戳），可通过撤销恢复
- 导出格式支持 JSON（保留完整结构）和 CSV（表格兼容）

## 许可证

本项目为个人学习项目，可自由使用。
