# 实验 X 架构决定

## ADR-X01 查询和权限留在服务端

保留原 `items:mine` 和 Django Session。查询以 `Listing.seller=request.user` 为入口，再根据合法状态在数据库筛选，最后分页。拒绝先把列表全部返回给浏览器再用脚本过滤，因为那样把数据范围和分页控制交给客户端，也无法复用数据库索引。

## ADR-X02 复用现有模型与模板协议

状态选项来自 `Listing.Status.choices`，排序使用 `-created_at, -pk`。使用 Django `Paginator` 和 GET 参数 `status`、`page`，列表页保留卖家确认组件 `bookings/_seller_actions.html`。拒绝增加新 API、前端框架或字段，因为现有模板和模型足够，新增公共接口会增大成员间协调成本。

## ADR-X03 将分页细节留在模块

模板翻页时把当前合法状态带回来。模块内可用本地链接或保留查询参数的模板标签，公共分页模板可保持不变。拒绝直接改现有公共分页模板，因为它还被多个页面复用，本故事只负责一个模块。

追溯：FR-X01 → ADR-X01 → EXP-X AC1；FR-X02 → ADR-X01/02 → AC2；FR-X03 → ADR-X02/03 → AC3/4；NFR-X01 → ADR-X03 → AC5。
