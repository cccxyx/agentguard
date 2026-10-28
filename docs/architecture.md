# 架构决策 v0.1

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
  -> AgentArts 编排（待接入）
  -> ToolRequest
  -> PolicyEngine
     -> ALLOW   -> MCPGateway -> Tool
     -> CONFIRM -> Approval   -> MCPGateway -> Tool
     -> BLOCK   -> AuditEvent
  -> Trace / Evaluation
```

## 为什么不让 LLM 最终授权

大模型适合判断外部文本是否在诱导 Agent，但其输出具有概率性。删除、发送和数据导出等执行边界必须由可测试、可追踪的规则控制。后续 AgentArts 接入只增加语义证据，不绕过策略引擎。

