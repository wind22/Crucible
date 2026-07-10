# Crucible
**人类一思考，上帝就发笑**

LLM 已经能写出令人信服的论证。但"听起来对"和"经受住攻击"之间，有巨大的距离。一个聪明的模型可以同时犯下基础错误——隐藏前提、偷换概念、逻辑跳跃——而你读过去只觉得很有道理。

Crucible 做的事情很简单：**在你相信一个想法之前，先让人攻击它。**

它只有三个角色：

- **Proposer** 构建论证。
- **Challenger** 尝试杀死它。
- **Reflector** 退后一步，问"框架本身对不对？"

三个角色形成一个循环。循环不因流程走完而终止——它因挑战者找不到新的攻击角度而收敛。幸存下来的命题不是被"证明"了，而是**暂时站住了**。这已经比绝大多数我们相信的东西更可靠。

内核是领域无关的。加载数据的前提和约束，它就驱动数据分析。加载概念和逻辑的前提和约束，它就驱动纯粹思辨。加载博弈和预判的前提和约束，它就驱动战略推演。

**同一个内核。不同的前提。不同的任务。**

模型越强，Crucible 不会变得多余——它会变得更强。因为辩证深度随能力自动提升：更强的 proposer 构建更复杂的论证，更强的 challenger 发起更致命的攻击。地基永远在。天花板自动抬高。

好的想法不是写出来的。**是在攻击中幸存下来的。**

---

## 快速开始

同一个内核，两种运行时。实例描述符（`src/crucible/instances/*.json`）是唯一事实源，两边共享。

### 作为 Claude Code 技能（对话内运行时）

本仓库同时是一个 Claude Code 插件：辩证内核技能 + 三个领域实例 + 独立上下文的挑战者子代理。

```
/plugin marketplace add wind22/Crucible
/plugin install crucible@crucible

# 然后
/crucible 自由意志与决定论相容吗？ L3
```

也可以不装插件，直接把 `skills/crucible/` 复制到 `.claude/skills/`。Claude 会分饰倡议者与反思者、按协议跑循环、每轮输出收敛状态行；在支持子代理的环境里，挑战者以独立上下文发起攻击——它看不到倡议者的推理过程，攻击更诚实。

### 作为 Python 引擎（程序化运行时）

```bash
pip install -e .
export ANTHROPIC_API_KEY=sk-ant-...

# 列出内置领域实例
crucible instances

# 把一个想法扔进坩埚
crucible run pure-reasoning "自由意志与决定论相容吗？" \
  --premise "决定论定义：给定过去与自然律，未来唯一确定" \
  --level L2 \
  --output result.json
```

`--level L1..L4` 控制辩证深度：L1 一轮攻击快速 sanity check，L4 收敛为止的深度对抗。输出是统一的结构（幸存命题、被驳斥命题及教训、认知增益、未解决张力、框架评价、置信度），`--output` 会额外写出含完整审计追踪的 JSON——每个结论都能回答"它经历过什么攻击"。

### 自定义领域实例

只需一个 JSON 描述符（前提类型 + 完整性约束 + 方法市场），见 `src/crucible/instances/` 与 [architecture.md](architecture.md)。修改或新增描述符后运行 `python3 scripts/render_skill_instances.py` 重新生成技能侧的实例文件，两个运行时即同时获得新领域。

---

*Crucible：坩埚。把想法扔进去，高温煅烧。杂质烧尽，留下来的才是真东西。*
