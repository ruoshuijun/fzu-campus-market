# 所有 AI 先读这里

这是四人并行开发的同一个 Django 项目。先读 `docs/公共约定.md`，再读用户指定成员的任务书，直接在已有骨架上完成任务。

- 成员一：只改 `accounts/`，任务书 `docs/成员1-账号.md`。
- 成员二：只改 `items/`，任务书 `docs/成员2-物品.md`。
- 成员三：只改 `bookings/`，任务书 `docs/成员3-预订.md`。
- 成员四：维护其余公共文件与 `moderation/`，任务书 `docs/成员4-整合.md`。
- 不重建项目，不改技术栈，不创建第二套 User/Listing/Reservation，不修改其他成员目录。
- `core/models.py`、迁移、`config/`、公共模板/CSS、依赖与 CI 是公共基线。新增公共需求先向成员四提出具体修改；独立模块内可自行增加 views/forms/services/tests/templates/static/templatetags。
- 读取公共模型和锁函数是正常依赖；业务模块之间不要互相 import 对方 views/services。成员三使用共享模板片段接入成员二页面，不修改成员二文件。
- HTML 表单使用 Session + CSRF。预订写入口返回 `core.results.Result` 定义的 JSON，表单编码请求。登录页走 Django 自带认证。
- 业务冲突以 Result 正常返回，避免回滚已执行的到期释放。先权限校验，再在事务内先锁 Listing、后锁 Reservation。
- SQLite 用于个人开发；涉及真实并发的结论只能在 PostgreSQL 验证。
- 完成后运行 `python manage.py check`、`python manage.py makemigrations --check --dry-run` 和 `python manage.py test`，说明实际结果与未验证项。不把待开发接口 501 当成功。
- 关键 AI 决策和测试结果记在自己模块的 `开发记录.md`（真实发生再创建），便于成员四后续整理课程作业证据。
