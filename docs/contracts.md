# 公共事件协议 v0.2

## ToolRequest

| 字段 | 含义 |
| --- | --- |
| `request_id` | 单次工具请求 ID |
| `task_id` | 用户任务 ID |
| `agent_id` | 发起请求的 Agent |
| `tool_name` | MCP 工具名 |
| `action` | 工具内具体动作 |
| `arguments` | 结构化参数 |
| `source_trust` | 触发该请求的信息来源 |

## TraceEvent

当前事件类型：

- `POLICY_DECISION`
- `APPROVAL_REQUIRED`
- `APPROVAL_RESOLVED`
- `TOOL_EXECUTED`
- `TOOL_FAILED`
- `ROLLBACK_COMPLETED`
- `ROLLBACK_SKIPPED`
- `CIRCUIT_OPENED`
- `CIRCUIT_REJECTED`

前端与评测模块应以该事件结构开发 Mock 数据，避免后续联调时重新定义字段。

## 后续 API

```text
POST /api/tasks
GET  /api/tasks/{id}
GET  /api/tasks/{id}/events
POST /api/tasks/{id}/decision
POST /api/tasks/{id}/cancel
POST /api/approvals/{id}/decision
GET  /api/incidents/{id}
POST /api/evaluations/run
GET  /api/evaluations/{id}
```

除评测接口外均已由核心后端实现。队友开发前端时以 `POST /api/tasks` 返回的 `status`、`pending_request_id`、`plan_summary`、`results` 为准，不应在前端自行推断策略结果。

## 团队并行边界

- 前端队员：消费任务、审批、事件和熔断接口，不修改策略判定；
- 评测队员：基于公共事件协议统计拦截率、误报率和恢复成功率；
- 核心后端：维护 AgentArts 适配器、状态机、策略网关与恢复语义。

真实 AgentArts 的项目 ID、工作流 API 和鉴权配置尚未写入仓库，等待平台资源开通后通过环境变量接入。
