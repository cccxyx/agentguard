# 御界 AgentGuard

面向工具型智能体的可信执行守护系统。项目在 Agent 与 MCP 工具之间增加确定性执行边界，实现：

- `ALLOW`：符合授权的低风险操作直接执行；
- `CONFIRM`：群发、敏感数据等高影响操作等待人工确认；
- `BLOCK`：越权、外部诱导或危险参数在工具执行前被阻止；
- 统一 Trace：记录请求、决策、证据、审批和执行结果；
- 熔断恢复：后续接入任务取消、快照与状态恢复。

## 当前进度

第一阶段已经包含：

- 统一领域模型与事件协议；
- JSON 策略加载；
- 确定性三态策略引擎；
- MCP 安全网关与人工审批接口；
- FastAPI 运行时接口；
- 内存模拟工具；
- 工具失败回滚与连续失败熔断；
- 可暂停、审批、取消和恢复的活动事务状态机；
- 业务、内容隔离、行为守卫三 Agent 的统一编排协议；
- 正常、确认、阻断三条自动化测试；
- 可直接运行的命令行演示。

AgentArts、多 Agent 工作流、FastAPI 服务和前端控制台将在后续迭代接入。

## 快速运行

项目核心原型仅使用 Python 标准库，Python 3.9+ 可直接运行：

```bash
python3 scripts/run_demo.py
python3 scripts/run_task_demo.py
python3 -m unittest discover -s tests -v
```

安装 API 依赖后可以启动服务：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[api,dev]'
uvicorn backend.api.app:app --reload
```

Swagger 页面：`http://127.0.0.1:8000/docs`

完整活动事务从 `POST /api/tasks` 开始。当前使用离线的 AgentArts 兼容适配器；真实平台接入不会改变前端、策略网关或评测模块的接口。

## 目录

```text
backend/
├── agent_core/          # AgentArts 与多 Agent 编排适配层
├── policy_engine/       # 权限、参数和三态决策
├── mcp_gateway/         # 工具注册、执行拦截与审批
├── mock_tools/          # 活动资料、名单、通知等模拟工具
├── recovery/            # 快照、熔断与恢复
├── api/                 # 公共接口协议和后续 FastAPI 服务
└── models/              # 领域模型与事件结构
config/                  # 策略配置
docs/                    # 架构、接口和协作约定
evaluation/              # 评测团队工作区
frontend/                # 前端团队工作区
tests/                   # 核心自动化测试
```

## 开发分支

- `main`：可演示稳定版本；
- `develop`：日常集成；
- `feature/agent-core`、`feature/policy-mcp`：核心后端；
- `feature/web-console`：前端控制台；
- `feature/evaluation`：评测与数据。

## 安全边界

当前版本只操作脱敏模拟数据，不连接真实学校系统、邮箱、支付账户或个人通讯录。任何外部系统接入前，必须补充授权、凭据存储和测试环境说明。
