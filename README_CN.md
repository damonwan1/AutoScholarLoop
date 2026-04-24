# AutoScholarLoop

[English](README.md) | [中文](README_CN.md)

**AutoScholarLoop** 是一个面向自动化科研写作场景的开源 AUTO Research 框架。它把用户的研究方向、近期论文、参考笔记和可选代码组织成一个可审计的多智能体科研闭环，用于生成研究方向、执行实验循环、证据驱动写作、质量审计和论文候选稿打包。

本项目基于中国科学院计算机网络信息中心人工智能部的科研自动化场景开发。

## 项目简介

AutoScholarLoop 模拟一个小型科研组，而不是单个聊天智能体。系统将科研过程拆成多个角色阶段：

1. `S00` 领域档案组：构建 field map、paper cards、method map、dataset/baseline map 和 evidence bank。
2. `S01` 教授决策组：多轮生成 idea、互相质疑、查重、排序并选择方向。
3. `S02` 博士执行组：规划 baseline、实现、实验、失败分析和教授复审 memo。
4. `S03` 写作组：基于证据生成论文计划、claim-evidence table、初稿、图表计划和审稿式修改。
5. `S04` 质量控制组：审计创新性、引用、可复现性、unsupported claims 和最终发布状态。

AI Group
![图片1](./img/img1.png)

核心流程是嵌套式科研循环：

```text
S00 证据准备
  -> S01 教授决策 loop
  -> S02 执行-复审 loop
  -> S03 写作-审稿 loop
  -> S04 质量 gate
  -> submission_candidate / revise / pivot / kill
```

每个阶段都会写入 Markdown checkpoint 和结构化 artifact，用户可以检查 idea 如何产生、为什么被选择、论文 claim 有哪些证据支撑、质量门控在哪里通过或失败。

## 功能

- 多阶段 AUTO Research loop 和显式 checkpoint。
- 本地 deterministic provider，用于离线 demo 和测试，不代表真实大模型科研运行。
- OpenAI-compatible provider，可接入真实大模型 API。
- Local、Semantic Scholar、OpenAlex 文献适配器。
- dry-run 和 shell 实验执行后端。
- 支持 `acm`、`ieee`、`springer_lncs`、`chinese_thesis` 四种论文格式。
- 输出 Markdown 和 LaTeX。
- 如果启用 `--compile-pdf` 且本地安装 LaTeX 工具链和所需 class 文件，可以尝试编译 PDF。
- Vue Web 控制台，支持首次模型配置、论文上传、进度观察和阶段结果预览。
- CLI 和 Web API 使用同一套 research pipeline。

![图片2](./img/img2.png)

## 安装

```powershell
cd AutoScholarLoop
pip install -e ".[api,web,dev]"
```

前端依赖：

```powershell
cd web
npm install
```

建议使用 Node 18+。当前前端为了兼容旧环境使用 Vite 2，后续可以升级到新版 Vite。

## CLI 快速开始

```powershell
autoscholarloop run `
  --seed "I want to study retrieval-augmented agents for scientific writing." `
  --loop-mode fast `
  --paper-format ieee `
  --workspace runs/demo
```

更多参数：

```powershell
autoscholarloop run `
  --seed "your research idea" `
  --reference "paper title, URL, local path, or note" `
  --num-ideas 5 `
  --loop-mode standard `
  --paper-format acm `
  --literature semanticscholar `
  --execution-backend dry-run `
  --review-ensemble 5 `
  --compile-pdf `
  --workspace runs/demo
```

说明：`local` provider 默认只是 deterministic demo。真实科研运行需要配置 OpenAI-compatible 模型 API 和 key。系统总会生成 `paper/main.tex`；PDF 只有在显式启用并且本地 LaTeX 环境支持目标模板时才会尝试生成。

## Web 控制台

启动后端：

```powershell
autoscholarloop web --host 127.0.0.1 --port 8000
```

启动前端：

```powershell
cd web
npm run dev
```

Web 支持：

- 首次大模型 API 配置；
- 中英文界面切换；
- 研究方向、目标会议/期刊输入；
- PDF、Markdown、文本和 BibTeX 上传；
- 教授组、博士组、写作组和全局大循环轮次配置；
- loop mode、文献后端、实验后端和论文格式选择；
- S00-S04 进度可视化；
- field map、idea report、execution analysis、paper plan、claim evidence、final gate、final draft 预览。

## 输出目录

每次运行会生成一个可审计 workspace：

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

重要输出：

- `00_field_context/field_map.md`
- `00_field_context/paper_cards.md`
- `01_decision/IDEA_REPORT.md`
- `01_decision/chosen_direction.md`
- `02_execution/RESULTS_ANALYSIS.md`
- `02_execution/CLAIMS_FROM_RESULTS.md`
- `02_execution/EXPERIMENT_AUDIT.md`
- `03_writing/PAPER_PLAN.md`
- `03_writing/claim_evidence_table.md`
- `04_quality/CITATION_AUDIT.md`
- `04_quality/final_gate.md`
- `paper/final_draft.md`
- `paper/main.tex`
- `release/README.md`

## 论文格式

支持：

- `acm`
- `ieee`
- `springer_lncs`
- `chinese_thesis`

生成结果是科研草稿和审计包，不保证自动满足具体会议/期刊的最终投稿规范。正式投稿前必须人工核对模板、引用、实验、作者贡献和 AI 使用披露要求。

## 致谢

AutoScholarLoop 参考和学习了多个自动科研与论文写作项目的思想：

- `AI-Scientist-main`：端到端 AI scientist 工作流。
- `academic-paper-writer-main`：论文格式和写作流程。
- Codex 和 ClaudeCode 风格的 coding-agent workflow。
- Semantic Scholar 和 OpenAlex 等开放文献基础设施。

本仓库是独立实现，架构、代码、阶段契约和 Web UI 均为 AutoScholarLoop 项目自有实现。

## 机构

Developed for:

**CAS CNIC**  
Computer Network Information Center, Chinese Academy of Sciences  
中国科学院计算机网络信息中心

## License & Responsible Use

This project is licensed under **The AI Scientist Source Code License**,
a derivative of the Responsible AI License.

**Mandatory Disclosure:** By using this code, you are legally bound to clearly
and prominently disclose the use of AI in any resulting scientific manuscripts
or papers.

Recommended attribution:

> "This manuscript was autonomously generated using AutoScholarLoop, an
> AI-assisted research-loop system inspired by The AI Scientist."

用户必须自行核验所有 claim、引用、实验、作者署名、投稿政策和 AI 使用披露要求。
