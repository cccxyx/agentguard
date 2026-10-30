# AgentArts接入与部署

## 作品中的职责边界

```text
可视化Demo
  -> AgentArts多智能体/工作流
     -> 业务规划Agent
     -> 内容隔离Agent
     -> 行为守卫Agent
  -> AgentGuard MCP Server
     -> 任务护照
     -> ALLOW / CONFIRM / BLOCK
     -> 审批摘要绑定
     -> 回滚、熔断与Trace
  -> 脱敏模拟工具
```

AgentArts负责模型、提示词、工作流、多Agent协作、阻塞恢复、调用链和评估。仓库代码负责确定性的安全执行边界。比赛演示必须以AgentArts为主入口，本地适配器只用于离线回归，不能作为已经接入AgentArts的证明。

## 本地MCP服务

MCP部署环境与普通开发环境隔离：

- Python 3.11；
- `mcp==1.28.1`；
- Streamable HTTP；
- 无状态协议传输；
- 服务路径`/mcp`；
- 探活路径`/ping`。

构建ARM64镜像：

```bash
docker buildx build \
  --platform linux/arm64 \
  -f deploy/mcp_server/Dockerfile \
  -t agentguard-mcp:dev \
  --load .
```

本地启动：

```bash
docker run --rm -p 8080:8080 agentguard-mcp:dev
```

探活：

```bash
curl http://127.0.0.1:8080/ping
```

列出MCP工具：

```bash
curl -X POST http://127.0.0.1:8080/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

本地验收结果：镜像构建、`initialize`、`tools/list`和`runtime_status`调用均已通过；创建模拟活动后，文件修改和群发通知会停在`WAITING_CONFIRMATION`。这证明协议入口与安全暂停链路可运行，但不能替代云上AgentArts部署证据。

## AgentArts控制台步骤

1. 开通AgentArts并接入可调用模型；
2. 将ARM64镜像上传至华为云SWR；
3. 在“托管与运行 > 智能体运行时”创建运行时，入站协议选择MCP；
4. 取得访问地址，通过`tools/list`和`tools/call`完成云上验证；
5. 在“开发中心 > 智能体组件 > MCP”创建自定义MCP，选择Streamable HTTP；
6. 创建业务规划、内容隔离、行为守卫三个Agent；
7. 创建固定工作流，按规划、隔离、护照、行为裁决、确认、执行的顺序连接；
8. 高影响操作使用提问器或等待输入节点，拒绝时调用`cancel_activity_task`；
9. 提交版本并部署多智能体应用，开启日志、指标和调用链；
10. 可视化Demo调用AgentArts运行时API，不直接绕过AgentArts调用本地FastAPI。

## 建议工作流

```text
开始
 -> 提问器补齐活动参数
 -> 业务规划Agent
 -> 内容隔离Agent
 -> create_secure_activity
 -> 判断任务状态
    -> WAITING_CONFIRMATION: 等待用户确认
       -> 同意: resolve_activity_approval(true)
       -> 拒绝: resolve_activity_approval(false)
    -> BLOCKED: 展示风险证据
    -> SUCCEEDED: 展示结果
 -> get_task_trace
 -> 结束
```

## 当前限制

- 服务状态仍保存在单进程内存中，只适合初赛原型和单副本演示；
- 正式多副本部署前需将任务、护照、审批和Trace持久化；
- 真实AgentArts工作流、调用链截图和平台评估需在取得云账号与模型资源后完成；
- 不得在仓库提交API Key、Token或`.agentarts_config.yaml`。
