# 架构决策 v0.2

## 核心原则

1. Agent 负责理解任务和提供风险证据，不拥有最终执行授权；
2. 确定性策略引擎负责工具、动作和参数判断；
3. 所有工具只能通过 MCP 安全网关执行；
4. 高影响操作必须进入人工确认；
5. 决策、审批和执行统一记录为 Trace 事件；
6. 初赛只连接脱敏模拟工具。

## 主链路

```text
用户任务
  -> AgentArts 编排适配层
     -> 业务 Agent：任务拆解
     -> 内容隔离 Agent：来源分级与授权隔离
     -> 行为守卫 Agent：高影响行为举证
  -> TaskCoordinator（事务状态机）
  -> ToolRequest
  -> PolicyEngine
     -> ALLOW   -> MCPGateway -> Tool
     -> CONFIRM -> Approval   -> MCPGateway -> Tool
     -> BLOCK   -> AuditEvent
  -> Trace / Evaluation
```

## 可替换的 AgentArts 边界

当前 `DeterministicAgentArtsAdapter` 在离线环境生成稳定计划，便于三名队员并行开发和现场演示。真实 AgentArts 工作流只需实现 `PlanningAdapter`，返回相同的 `OrchestrationPlan`。无论使用本地适配器还是真实 AgentArts，所有工具调用都必须重新经过确定性策略引擎与 MCP 网关。

## 事务状态机

```text
CREATED -> RUNNING -> WAITING_CONFIRMATION -> RUNNING -> SUCCEEDED
                    -> CANCELLED（恢复任务前快照）
          -> BLOCKED / FAILED / RESTORED（恢复任务前快照）
```

后端在活动事务开始前保存全局模拟工作区快照；拒绝、取消、策略阻断或工具失败时恢复整个任务，而不仅是最后一个工具调用。

## 为什么不让 LLM 最终授权

大模型适合判断外部文本是否在诱导 Agent，但其输出具有概率性。删除、发送和数据导出等执行边界必须由可测试、可追踪的规则控制。后续 AgentArts 接入只增加语义证据，不绕过策略引擎。
