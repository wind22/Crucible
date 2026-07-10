# Changelog

## 0.0.1 - 2026-07-07

首个可运行版本：架构文档（architecture.md）的最小完整实现。同一个内核，两种运行时——Claude Code 技能集合（对话内）与 Python 引擎（程序化），共享同一份实例描述符。

### 技能集合（对话内运行时）
- Claude Code 插件结构：`.claude-plugin/plugin.json` + 自托管 marketplace，可经 `/plugin marketplace add wind22/Crucible` 安装
- `skills/crucible`：辩证内核技能（触发条件、L1–L4 深度、执行步骤）+ 完整辩证协议 `references/dialectical-protocol.md`（角色规范、循环流程、每轮收敛状态行、统一输出结构）
- `agents/crucible-challenger`：独立上下文的挑战者子代理——只接收命题与前提，不接收倡议者的推理过程
- `commands/crucible`：`/crucible <问题>` 斜杠命令入口
- 实例单一事实源：`scripts/render_skill_instances.py` 从 JSON 描述符生成技能侧实例文件，`tests/test_skill_sync.py` 校验两者同步

### 内核（领域无关）
- 辩证循环控制流：倡议者提出 → 挑战者攻击 → 倡议者修正/放弃 → 反思者审视 → 收敛判断（`engine.py`）
- 角色协议：Proposer / Challenger / Reflector 为同一模型的不同 prompt，输出以 JSON Schema 约束（`roles.py`）
- 收敛门：连续 N 轮无实质性削弱 + 反思者连续 M 轮无新发现 + 硬上限（`convergence.py`）
- 统一输出结构与认知审计追踪：幸存/被驳斥命题、认知增益、未解决张力、框架评价、置信度、逐轮记录（`schema.py`）
- 能力自适应：L1–L4 深度预设（轮数、收敛阈值、思考深度）

### 领域实例（可插拔）
- 实例描述符：premise_types + integrity_rules + method_market，JSON 加载与校验（`instance.py`）
- 内置实例：纯思辨（pure-reasoning）、数据分析（data-analysis）、战略推演（strategic-simulation）

### 基础设施
- LLM 后端协议 + Anthropic 实现（claude-opus-4-8，adaptive thinking，structured outputs，系统提示词共享段缓存）；FakeLLM 用于离线测试
- CLI：`crucible instances`、`crucible run`（前提、等级、模型、审计输出）
- 19 个不依赖网络的测试覆盖收敛门、实例加载、引擎全路径（幸存/驳斥/修正/框架转换/硬上限）与 CLI
