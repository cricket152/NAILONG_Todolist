# NAILONG TodoList

一个带一点奶龙快乐气息的 PyQt6 桌面待办工具。它适合用来管理课程作业、DDL、每日习惯和每周计划：打开就能记，做完就勾，超时会提醒，删错还能撤销。

<p align="center">
  <img src="resources/app_icon2.png" alt="NAILONG TodoList 图标" width="180">
</p>

<p align="center">
  <b>把 DDL 变成一只可以被驯服的小黄龙。</b>
</p>

> 图片使用项目内置图标资源：`resources/app_icon2.png`。

## 为什么做它

很多待办软件很强，但也容易让人陷入“整理待办本身也变成待办”的循环。这个项目的目标很朴素：

- 任务类型清晰：DDL、每日、每周分开管理。
- 操作路径短：搜索、筛选、新增、完成、删除都在主界面完成。
- 数据本地化：使用 SQLite，本地保存，不依赖云服务。
- 适合打包交付：可通过 PyInstaller 生成单文件 Windows `.exe`。

## 功能亮点

### 任务管理

- **三类任务**：DDL 任务、每日任务、每周任务，使用标签页分区展示。
- **优先级**：支持高 / 中 / 低优先级，并在列表中用颜色区分。
- **完成状态**：点击自定义复选框即可切换待完成 / 已完成。
- **搜索高亮**：输入关键词后，标题中的匹配内容会高亮。
- **筛选统计**：状态栏显示当前视图任务数、待完成数、已完成数。
- **空状态提示**：没有任务时会提示用户点击“新增”或按 `Ctrl+N`。

### DDL 体验

- **截止日期**：DDL 任务支持设置日期和时间。
- **快捷日期**：新增 / 编辑 DDL 时可一键设置“今天”“明天”“下周”。
- **超时提醒**：后台定时检查已超时任务，并通过系统托盘提醒。
- **今日到期统计**：状态栏会显示今日到期和超时任务数量。

### 每日 / 每周任务

- **每日任务自动重置**：跨天后，已完成的每日任务会重新变成待完成。
- **每周任务自动重置**：跨 ISO 周后，每周任务自动重置。
- **按当前标签新增**：在“每日任务”或“每周任务”页点击新增，会默认创建对应类型。

### 删除与导出

- **软删除**：删除任务不会立刻物理清除，方便撤销。
- **撤销删除**：删除后可按 `Ctrl+Z` 恢复最近删除的任务。
- **批量删除**：选中多行后点击“删除选中”或按 `Delete`。
- **数据导出**：支持导出 JSON / CSV，文件后缀会自动补全。

### 系统集成

- **系统托盘**：关闭窗口时可最小化到托盘。
- **托盘快捷操作**：托盘菜单支持显示主窗口、添加任务、退出。
- **开机自启**：可在设置中开启或关闭。
- **窗口状态记忆**：自动保存和恢复窗口尺寸位置。

## 快捷键

| 快捷键 | 功能 |
| --- | --- |
| `Ctrl+N` | 新增任务 |
| `Ctrl+E` | 编辑当前任务 |
| `Delete` | 删除选中任务 |
| `Ctrl+Z` | 撤销最近一次删除 |
| `Ctrl+T` | 查看今日任务 |
| `Ctrl+Shift+A` | 查看全部任务 |
| `Ctrl+Shift+E` | 导出任务 |

## 技术栈

- Python 3.9+
- PyQt6
- SQLite
- PyInstaller

## 项目结构

```text
TodoList_Pyqt6/
├── main.py
├── requirements.txt
├── TodoList.spec
├── resources/
│   ├── style.qss
│   ├── app_icon2.png
│   ├── down_arrow.svg
│   └── up_arrow.svg
└── todo_app/
    ├── __init__.py
    ├── database.py
    ├── export_util.py
    ├── models.py
    ├── utils.py
    └── ui/
        ├── checkbox_delegate.py
        ├── delete_delegate.py
        ├── highlight_delegate.py
        ├── main_window.py
        ├── settings_dialog.py
        ├── task_dialog.py
        ├── task_table_model.py
        ├── today_task_dialog.py
        └── tray_manager.py
```

## 本地运行

建议使用独立环境：

```powershell
conda create -n Todolist_pyqt python=3.9
conda activate Todolist_pyqt
pip install -r requirements.txt
python main.py
```

如果你已经有同名环境：

```powershell
conda activate Todolist_pyqt
python main.py
```

## 打包为 exe

项目已提供 `TodoList.spec`：

```powershell
conda activate Todolist_pyqt
pyinstaller --clean TodoList.spec
```

生成结果：

```text
dist/TodoList.exe
```

## 数据存储

- 开发运行时，数据库默认位于项目本地数据目录。
- 打包运行时，数据库位于 `%APPDATA%/TodoListPyQt6/`。
- 任务表包含标题、描述、优先级、截止日期、状态、任务类型、创建时间、完成时间、删除时间等字段。
- 删除为软删除，导出时会保留完整任务结构。

## 安全与隐私

本项目不会主动联网，也不会上传任务数据。所有待办内容默认只保存在用户本机 SQLite 数据库中。

仓库忽略以下本地文件和构建产物：

- 数据库文件
- Python 缓存
- 虚拟环境
- `dist/`、`build/`
- 本地学习 / 修改报告

## 许可证

本项目为课程学习与个人效率工具项目，可自由学习、修改和使用。
