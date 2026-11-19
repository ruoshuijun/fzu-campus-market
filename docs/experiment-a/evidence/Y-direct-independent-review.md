通过

- 约定违规数 **0**。改动仅涉及 `bookings/views.py` 和 `bookings/templates/bookings/mine.html`。`mine` 保留 `@login_required`，查询始终按 `buyer=request.user` 限定。模板继续展示商品标题、状态和到期时间，并为无预订和筛选无结果提供提示。统一验收 8 项全部通过。
- 架构冲突数 **0**。筛选复用 `Reservation.Status`，服务端按创建时间和主键倒序排列，每页 20 条。未知状态归为全部，分页链接保留有效状态，`Paginator.get_page()` 处理非数字页码和超过总页数的页码。视图只读取数据，diff 无模型或迁移改动。
- 测试提示：本次 diff 未新增模块内测试。统一验收已覆盖本次行为，不构成合入障碍。