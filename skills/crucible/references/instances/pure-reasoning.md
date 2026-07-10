# 纯思辨实例（pure-reasoning）

> 本文件由 scripts/render_skill_instances.py 从 src/crucible/instances/pure_reasoning.json 生成，请勿手改。

以概念和逻辑为前提的纯粹思辨论证。地基是逻辑完整性：前提显式、概念一致、推理步骤可追溯。

## 前提类型（什么算有效输入）

- **conceptual_definition**：概念定义，必须显式声明，不可在论证中偷换（校验：challenger 检查概念使用一致性）
- **axiom**：公理或先验命题，作为不再回溯论证的起点（校验：challenger 检查公理是否被默默替换或加强）
- **thought_experiment**：思想实验：构造的情景及其直觉判断（校验：challenger 检查情景是否偷带了结论）

## 完整性约束（什么算不可接受的错误；blocker 级违规直接构成实质性削弱）

- **[no_hidden_premises]**（blocker，检查者：challenger）所有前提必须显式声明，不得隐藏假设
- **[no_self_contradiction]**（blocker，检查者：challenger）不能同时主张 A 和 非A
- **[no_concept_drift]**（blocker，检查者：challenger）概念使用一致，同一术语在论证全程含义不变（无定义漂移）
- **[explicit_steps]**（blocker，检查者：challenger）推理步骤显式化，不允许逻辑跳跃
- **[traceable_references]**（warning，检查者：challenger）引用链可追溯：引用他人观点时可定位其来源与语境

## 方法市场（按需选用，并在论证中注明所用方法的 id）

- **[reductio_ad_absurdum]** 归谬法：假设命题为真 → 推出矛盾 → 命题为假 —— 适用时机：需要检验命题逻辑必然性时
- **[thought_experiment]** 思想实验：构造情景，检验直觉或原则 —— 适用时机：抽象原则需要具体情景来暴露后果时
- **[concept_genealogy]** 概念谱系追溯：概念的起源与演化，识别语义漂移 —— 适用时机：怀疑论证双方使用同一个词但含义不同时
- **[socratic_questioning]** 苏格拉底式诘问：持续追问"你这么说到底是什么意思" —— 适用时机：命题含糊、依赖未经审视的直觉时
- **[analogy_validation]** 类比推理验证：A:B::C:D，检验结构同构性 —— 适用时机：论证依赖类比时，检验类比是否在关键维度成立
- **[boundary_exploration]** 边界条件探索：命题在极端情况下还成立吗 —— 适用时机：命题声称普遍有效时
- **[counterfactual_reasoning]** 反事实推演：如果 X 不成立，会怎样 —— 适用时机：检验某前提对结论的承重程度时
- **[framework_comparison]** 框架对比：同一问题用不同理论框架分析，差异在哪 —— 适用时机：怀疑结论是框架的产物而非问题的答案时
- **[premise_sensitivity]** 前提敏感性测试：改变某个前提 → 结论如何变化 —— 适用时机：评估结论的稳健性时
