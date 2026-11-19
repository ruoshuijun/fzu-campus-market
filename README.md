# 福大校园闲置物品预订系统

这是四个人共用的开发底座。**新加入的队友先读 [开工指南](docs/开始开发.md)**，里面有克隆命令、成员分工、必读文档和 PR 示例。

## 先跑起来

使用 **Python 3.13 + Django 5.2 + HTML/CSS + Git**。个人开发默认 SQLite。第一次启动时，在含 `manage.py` 的项目目录运行以下命令。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver
```

打开 [本地网站](http://127.0.0.1:8000/)。以后只需执行最后一行。macOS/Linux 把 `.\.venv\Scripts\python.exe` 换为 `.venv/bin/python`。

演示账号：`student1`（卖家）、`student2`（买家）、`student3`（另一买家）、`admin`（管理员）。新导入账号密码统一为 **`DemoPass123!`**，仅供本机演示。`seed_demo` 可重复运行，不重置已存在用户的密码、不覆盖交易状态。

## 每个人读什么

| 人员 | 负责目录 | 任务书 |
|---|---|---|
| 成员一 | accounts/ | [账号：登录、注册、资料](docs/成员1-账号.md) |
| 成员二 | items/ | [物品：发布、浏览、上下架](docs/成员2-物品.md) |
| 成员三 | bookings/ | [预订：取消、到期、双方确认](docs/成员3-预订.md) |
| 成员四（你） | core/、config/、moderation/、公共文件 | [基础、管理员与整合](docs/成员4-整合.md) |

大家先看一遍 [公共约定](docs/公共约定.md)，里面已经定好数据字段、网址和模块连接方式。个人任务书最后一段可以直接复制给 AI。开发必须拿到完整项目，单独发任务书不够。

## 当前已经有什么

可运行的项目、统一模型与迁移、演示数据、基础登录/退出、只读物品列表/详情、个人模块入口、公共页面样式、可用管理员管理台、事务锁工具、测试和 GitHub CI。

**仍待开发**：注册与资料修改、搜索与物品写入、预订/取消/确认/周期到期回收。待开发写接口返回 501；页面明确提示，不会伪造成功。成员一至三以自己的任务书补齐。

## 检查与上传 GitHub

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

成员四在 GitHub 邀请另外三人为协作者。每个人克隆同一个仓库，从 `main` 创建自己的分支（`feat/accounts`、`feat/items` 或 `feat/bookings`），只修改对应模块。完成后提交 PR，由成员四检查并合并。`.gitignore` 会排除虚拟环境、本地数据库和 `.env`。

需要从本地副本创建仓库时，参照成员四任务书。GitHub Actions 会用 PostgreSQL 执行自动检查，运行结果见仓库的 Actions 页面。

## PostgreSQL 整合环境（最后再用）

安装 Docker Desktop 并启动后，另开 PowerShell，在项目根目录执行：

```powershell
docker compose up -d db
. .\scripts\use-postgres.ps1
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py runserver
```

若 PowerShell 禁止脚本执行，可直接设置 `$env:DB_ENGINE="postgres"`，其他连接参数已有本地默认值。数据库准备好后再运行迁移。切换的是一个**独立的新数据库**，SQLite 数据不会自动搬过去。

SQLite 没有 PostgreSQL 那样的行锁行为，因此个人页面开发用 SQLite，最终抢单并发验收用 PostgreSQL。[Django 数据库说明](https://docs.djangoproject.com/en/5.2/ref/databases/#sqlite-notes)

## 课程说明

实验 A 的结果见 [项目复盘](retrospective.md)。后续根据课件补齐团队的 BMAD 过程、用户故事、真实决策日志和演示录屏。每个人在开发时把真实的决策和测试结果记在自己的模块内。

本底座由 Codex 辅助生成；提交作业时说明实际工具、模型与版本，并保留本次对话。不要把生成文档当作已经完成的访谈、测试或人机决策证据。
