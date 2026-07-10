# 数据分析实例（data-analysis）

> 本文件由 scripts/render_skill_instances.py 从 src/crucible/instances/data_analysis.json 生成，请勿手改。

以经验数据为前提的分析论证。地基是数据完整性：数字可追溯、逻辑闭合、呈现不误导。

## 前提类型（什么算有效输入）

- **empirical_data**：经验数据：来自外部世界的、可重复验证的观察记录（表、指标、日志）（校验：challenger 检查数字是否可追溯到源数据）
- **metric_definition**：指标口径定义：指标如何计算、分子分母是什么、统计窗口是什么（校验：challenger 检查口径是否在论证中悄悄变化）
- **context_constraint**：业务或采集上下文约束：数据在什么条件下产生、有什么已知缺陷（校验：challenger 检查结论是否超出数据的适用范围）

## 完整性约束（什么算不可接受的错误；blocker 级违规直接构成实质性削弱）

- **[traceable_numbers]**（blocker，检查者：challenger）数字来自可追溯的源数据，不得凭空引入未声明的数字
- **[logical_closure]**（blocker，检查者：challenger）逻辑闭合：分子分母可加总、分解项相加等于总量、双算检测
- **[no_misleading_presentation]**（blocker，检查者：challenger）呈现不误导：格式合规、明确声明数据与结论的限制条件
- **[correlation_is_not_causation]**（blocker，检查者：challenger）相关性结论不得表述为因果结论，除非使用了因果推断方法并声明其假设

## 方法市场（按需选用，并在论证中注明所用方法的 id）

- **[contribution_decomposition]** 贡献度分解（additive/LMDI/ratio/Shapley） —— 适用时机：需要回答"总量变化由哪些部分贡献"时
- **[cohort_analysis]** 同期群分析（经典/区间/滚动留存、转化、LTV） —— 适用时机：行为随时间演化、不同时期用户不可直接混合比较时
- **[statistical_testing]** 统计检验（显著性、置信区间、功效分析） —— 适用时机：需要区分真实效应与抽样噪音时
- **[causal_inference]** 因果推断（DID、RDD、IV、匹配方法） —— 适用时机：需要从观察数据回答因果问题、且随机实验不可行时
- **[time_series_decomposition]** 时间序列分解（趋势、季节、残差） —— 适用时机：指标随时间波动、需要分离长期趋势与周期性时
- **[anomaly_detection]** 异常检测（统计过程控制、隔离森林） —— 适用时机：需要判断某个观测是异常还是正常波动时
