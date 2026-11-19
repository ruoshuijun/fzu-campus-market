---
title: "EXP-X 我的发布按状态筛选和分页"
status: done
baseline_commit: d09fcf11a44493878f3b57f6324b71ec75411710
---

# Story 1.1 · EXP-X 我的发布按状态筛选和分页

## 故事

作为已经发布多件物品的福大学生，我希望在「我的发布」按状态查找并翻页，以便快速找到需要处理的物品。

## 验收标准

1. **AC1** 给定两个卖家各有发布记录，当前登录卖家打开 `/items/mine/`，则默认只显示本人的全部状态物品，按创建时间倒序。未登录时按原有规则跳到登录页。
2. **AC2** 给定本人有多种状态的记录，选择任意有效状态，则只显示本人处于该状态的记录，页面标出当前选择。传未知状态时回到全部状态。
3. **AC3** 给定筛选后的记录超过 20 条，打开第一和第二页，则每页最多 20 条，按一致顺序分页，翻页链接保留筛选状态。
4. **AC4** 给定无匹配数据、恶意或超范围页码，访问列表应正常渲染。无匹配时显示明确提示。
5. **AC5** 给定既有卖家确认片段和公共路由，更新列表后仍兼容。Django 检查和迁移一致性检查通过。

## Tasks

- [x] 在 `items/views.py` 的 `mine` 视图中，读取 GET status/page，校验状态枚举，把条件和分页施加到当前卖家查询。
- [x] 在 `items/templates/items/mine.html` 加状态选择和翻页控件，保留每件物品原有的标题、价格、状态与确认片段。
- [x] 在 `items/test_mine.py` 覆盖权限、筛选和页间状态，记录真实测试结果。

## Dev Notes

- Planning context: `_bmad-output/planning-artifacts/prd.md` 和 `architecture.md`。
- Project rules: `_bmad-output/project-context.md`。
- 现有入口 `items:mine`，数据模型 `core.models.Listing`。本故事只改现有读路径，不增加状态迁移。
- 需要改分页参数时，可在本模块的模板中用 Django 现有查询字符串工具，或构建安全的 GET 链接。每个分页链接必须带合法筛选。
- 由于 Django 仅在启用 request context processor 时提供模板请求参数，改链接前核对现有配置。
- 人工验收时先登录 student1，再访问“我的发布”。演示初始化可能不到 20 条，自动化检查须构造超过一页的数据。

## Dev Agent Record

### Completion Notes

操作者在独立 Codex 会话返回代码后保存文件，运行统一验收并发起独立评审。8 项统一检查通过，项目回归 36 项通过、1 项 PostgreSQL 检查跳过。独立评审首轮通过。见实验目录中的 `evidence/X-bmad-round1-checks.json`、`X-bmad-regression.txt` 和 `X-bmad-independent-review.md`。状态由操作者依据实测更新。

### File List

- `items/views.py`
- `items/templates/items/mine.html`
- `items/test_mine.py`
