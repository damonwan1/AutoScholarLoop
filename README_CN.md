# AutoScholarLoop

[English](README.md) | [中文](README_CN.md)

**AutoScholarLoop** 是一个可审计的 AUTO Research 框架。它把研究自动化拆成分阶段、可追踪的多智能体循环：从研究想法、参考文献、论文材料和可选执行后端出发，生成带检查点的研究流程、论文草稿、参考文献文件以及质量审计结果。

该项目面向中国科学院计算机网络信息中心（CAS CNIC）AI Group 的科研自动化场景开发。

AI Group  
![AI Group](./img/img1.png)

## 本版本新增内容

这个版本补齐了第一版可用的参考文献闭环：

- 在 `S00` 中建立统一的参考文献元数据规范化流程；
- 对文献条目做去重，并生成稳定的 cite key；
- 在 `S03` 中真实输出 `paper/references.bib`；
- Markdown 草稿中会插入内联引用标记；
- LaTeX 导出会根据规范化后的条目生成参考文献部分；
- `S04` 现在执行真实的 citation audit，而不是仅输出占位说明；
- 引用审计会把阻塞问题和元数据 warning 分开报告。

目前中文文献源还没有全部接入，但底层元数据模式已经为后续扩展铺好，统一包含 `language`、`source`、`doi`、`source_id`、`entry_type`、`note` 等字段。后续接入中文数据库时，不需要再重构参考文献格式。

## 流程结构

AutoScholarLoop 模拟的是一个小型研究组，而不是单个聊天机器人。默认流程如下：

1. `S00` 领域归档：构建 field map、paper cards、evidence bank 和规范化 reference inventory。
2. `S01` 教授决策：多轮生成、批判、排序并选定研究方向。
3. `S02` 博士执行：规划 baseline、实现、运行实验并汇总结果。
4. `S03` 写作评审：生成论文计划、claim-evidence table、草稿、`references.bib` 和 LaTeX。
5. `S04` 质量门：审查 novelty、citation、reproducibility、claim support 与发布就绪状态。

```text
S00 证据准备
  -> S01 教授决策循环
  -> S02 执行-评审循环
  -> S03 写作-评审循环
  -> S04 质量门
  -> submission_candidate / revise / pivot / kill
```

每个阶段都会写出 Markdown 检查点和结构化产物，方便追溯研究方向为什么被选中、有哪些证据支持、用了哪些参考文献，以及为什么质量门通过或失败。

## 当前能力

- 分阶段 AUTO Research 循环，带显式检查点和 manifest 记录。
- 用于离线演示和 smoke run 的 deterministic local provider。
- OpenAI-compatible 模型适配层。
- `local`、`semanticscholar`、`openalex` 三类文献适配器。
- 统一参考文献元数据规范化与 cite key 生成。
- 自动生成 `paper/references.bib`。
- 生成 `04_quality/CITATION_AUDIT.md` 与 `CITATION_AUDIT.json`。
- `dry-run` 与 `shell` 两类执行后端。
- 面向 `acm`、`ieee`、`springer_lncs`、`chinese_thesis` 的格式感知写作。
- Markdown 与 LaTeX 两种论文导出。
- 在启用 `--compile-pdf` 且本地 LaTeX 环境满足条件时尝试编译 PDF。
- 用于启动任务、查看进度和预览产物的 Vue Web 控制台。

![Workflow](./img/img2.png)

## 安装

```powershell
cd AutoScholarLoop
pip install -e ".[api,web,dev]"
```

前端安装：

```powershell
cd web
npm install
```

## CLI 快速开始

```powershell
autoscholarloop run `
  --seed "I want to study retrieval-augmented agents for scientific writing." `
  --loop-mode fast `
  --paper-format ieee `
  --workspace runs/demo
```

带参考文献输入和文献检索的例子：

```powershell
autoscholarloop run `
  --seed "your research idea" `
  --reference "paper title, URL, local path, or note" `
  --reference ".\\papers\\example.pdf" `
  --num-ideas 5 `
  --loop-mode standard `
  --paper-format acm `
  --literature semanticscholar `
  --execution-backend dry-run `
  --review-ensemble 5 `
  --compile-pdf `
  --workspace runs/demo
```

默认 `local` provider 只是确定性的演示模式。要做真实运行，需要配置 OpenAI-compatible 模型服务和 API key。

## 参考文献工作流

新的参考文献路径如下：

1. 用户通过 `--reference`、上传文件或外部文献检索提供参考材料。
2. `S00` 将每条记录规范化到统一 bibliography schema。
3. 系统执行去重，并生成稳定的 cite key。
4. `S03` 会输出：
   - `00_field_context/reference_inventory.md`
   - `00_field_context/reference_inventory.json`
   - `03_writing/reference_inventory.md`
   - `paper/references.bib`
5. 草稿正文中会插入 `[@key]` 形式的内联引用。
6. `S04` 会检查 cite key 是否可解析、元数据是否缺失、是否存在重复标题簇。

当前阻塞条件：

- 正文引用了不存在于 bibliography 中的 cite key；
- 论文草稿中完全没有发现内联引用。

当前 warning：

- 作者、年份、DOI、URL、source ID 等元数据缺失；
- 规范化后仍存在重复标题组。

## Web 控制台

启动 Python API：

```powershell
autoscholarloop web --host 127.0.0.1 --port 8000
```

启动 Vue 前端：

```powershell
cd web
npm run dev
```

Web 控制台支持：

- 模型提供方配置；
- 研究方向和目标 venue 输入；
- PDF、Markdown、文本和 BibTeX 上传；
- loop mode 与 backend 选择；
- 论文格式选择；
- `S00` 到 `S04` 的实时进度可视化；
- field map、idea report、execution analysis、paper plan、claim evidence、final gate、final draft 等产物预览。

## 运行输出目录

每次运行都会生成一个可审计的 workspace：

```text
run/
  source_papers/
  inputs/
  artifacts/
  logs/
  00_field_context/
  01_decision/
  02_execution/
  03_writing/
  04_quality/
  paper/
  release/
```

重要产物包括：

- `00_field_context/field_map.md`
- `00_field_context/paper_cards.md`
- `00_field_context/reference_inventory.md`
- `01_decision/IDEA_REPORT.md`
- `02_execution/RESULTS_ANALYSIS.md`
- `03_writing/PAPER_PLAN.md`
- `03_writing/claim_evidence_table.md`
- `paper/references.bib`
- `paper/main.tex`
- `04_quality/CITATION_AUDIT.md`
- `04_quality/CITATION_AUDIT.json`
- `04_quality/final_gate.md`
- `paper/final_draft.md`
- `release/README.md`

## 论文格式

当前支持：

- `acm`
- `ieee`
- `springer_lncs`
- `chinese_thesis`

生成结果是“可审计的论文草稿包”，不是最终投稿合规保证。正式投稿前，仍然需要人工核对官方模板、参考文献样式和投稿政策。

## 当前限制

- 中文文献检索源尚未完整接入。
- 当前 citation audit 主要校验 bibliography 与正文引用的一致性，还不是完整的全网事实核验。
- 文献检索质量依赖所选 adapter。
- 实验正确性、论文结论和投稿就绪状态仍然需要人工把关。

## 开发

运行测试：

```powershell
$env:PYTHONPATH='src'
python -m pytest tests -q
```

构建前端：

```powershell
cd web
npm run build
```

## 仓库结构

```text
docs/                          设计、路线图、工作流和版本说明
src/open_research_agent/       Python 研究循环主包
web/                           Vue Web 控制台
configs/                       示例配置
templates/                     研究工作区模板
examples/                      示例输入
tests/                         Smoke 测试
```

## 许可证与责任使用

本项目采用 **The AI Scientist Source Code License**，它是 Responsible AI License 的一个衍生版本。

**强制披露要求：** 如果你将本项目用于论文或科研写作，必须按照许可证和投稿 venue 的要求，明确披露 AI 的使用情况。

在提交任何生成内容之前，用户仍需自行核实所有 claim、reference、experiment、authorship 要求、投稿规则和披露义务。
