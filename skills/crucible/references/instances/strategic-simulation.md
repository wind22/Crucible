# 战略推演实例（strategic-simulation）

> 本文件由 scripts/render_skill_instances.py 从 src/crucible/instances/strategic_simulation.json 生成，请勿手改。

以数据、假设与竞争性预判为混合前提的战略论证。地基是数据完整性与逻辑完整性的混合，外加：假设必须标注为假设，预判必须标注为预判。

## 前提类型（什么算有效输入）

- **empirical_data**：经验数据：同数据分析实例，可追溯、可验证（校验：challenger 检查数字是否可追溯）
- **assumption**：假设：未被验证但被采用的判断，必须显式标注为假设（校验：challenger 检查假设是否被当作事实使用）
- **competitive_anticipation**：竞争性预判：对手可能的行动（"对手可能做 X"），必须与"我们知道 X"区分（校验：challenger 检查预判是否被当作既定事实）
- **constraint**：约束条件：资源、时间、法规等硬性边界（校验：challenger 检查方案是否违反已声明的约束）

## 完整性约束（什么算不可接受的错误；blocker 级违规直接构成实质性削弱）

- **[data_integrity]**（blocker，检查者：challenger）数据部分：同数据分析实例（可追溯、闭合、不误导）
- **[logic_integrity]**（blocker，检查者：challenger）逻辑部分：同纯思辨实例（前提显式、无自相矛盾、无概念漂移、步骤显式）
- **[assumptions_labeled]**（blocker，检查者：challenger）假设被显式标注为假设，不与数据混淆
- **[anticipations_labeled]**（blocker，检查者：challenger）竞争性预判被显式标注（"对手可能做 X" vs "我们知道 X"）

## 方法市场（按需选用，并在论证中注明所用方法的 id）

- **[scenario_planning]** 情景规划（best/base/worst case，带触发条件） —— 适用时机：关键不确定性无法消除、需要为多种未来准备时
- **[game_matrix]** 博弈矩阵（参与者、策略、收益、均衡） —— 适用时机：结果取决于多方互动、各方有明确策略集合时
- **[anticipation_recursion]** 预判 vs 反预判（"对手预判了我们的预判"的递归） —— 适用时机：对手有能力和动机对我方策略做出反应时
- **[robustness_analysis]** 稳健性分析（计划在哪些假设变化下仍成立） —— 适用时机：方案依赖多个不确定假设、需要找出承重墙时
- **[option_thinking]** 期权思维（延迟决策的价值、不可逆决策的成本） —— 适用时机：决策可逆性差异大、信息随时间揭示时
- **[competitive_landscape]** 竞争态势推演（波特五力、价值网络） —— 适用时机：需要系统评估行业结构与竞争压力来源时
- **[system_dynamics]** 系统动力学（反馈回路、延迟效应、非线性） —— 适用时机：行动的后果会反过来改变系统本身时
