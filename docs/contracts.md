# 公共事件协议 v0.1

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

前端与评测模块应以该事件结构开发 Mock 数据，避免后续联调时重新定义字段。

## 后续 API

```text
POST /api/tasks
GET  /api/tasks/{id}/events
POST /api/approvals/{id}/decision
GET  /api/incidents/{id}
POST /api/evaluations/run
GET  /api/evaluations/{id}
```

