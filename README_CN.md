# AutoScholarLoop

[English](README.md) | [中文](README_CN.md)

**AutoScholarLoop** 是一个面向自动化科研写作场景的开源 AUTO Research 框架。它把用户的研究方向、近期论文、参考笔记和可选代码组织成一个可审计的多智能体科研闭环，用于生成研究方向、执行实验循环、证据驱动写作、质量审计和论文候选稿打包。

本项目面向 **CAS CNIC，中国科学院计算机网络信息中心 AI Group** 的科研自动化场景开发。

## 项目简介

AutoScholarLoop 模拟一个小型科研组，而不是单个聊天智能体。系统将科研过程拆成多个角色阶段：

1. `S00` 领域档案组：构建 field map、paper cards、method map、dataset/baseline map 和 evidence bank。
2. `S01` 教授决策组：多轮生成 idea、互相质疑、查重、排序并选择方向。
3. `S02` 博士执行组：规划 baseline、调用大模型生成代码、在本机运行实验、分析失败并形成教授复审 memo。
4. `S03` 写作组：基于证据生成论文计划、claim-evidence table、初稿、图表计划和审稿式修改。
5. `S04` 质量控制组：审计创新性、引用、可复现性、unsupported claims 和最终发布状态。

核心流程：

```text
S00 证据准备
  -> S01 教授决策 loop
  -> S02 本机代码生成与实验执行 loop
  -> S03 写作-审稿 loop
  -> S04 质量 gate
  -> submission_candidate / revise / pivot / kill
```

## 功能

- 多阶段 AUTO Research loop 和显式 checkpoint。
- 本地 deterministic provider 用于离线 demo 和测试，不代表真实大模型科研运行。
- OpenAI-compatible provider，可接入 DeepSeek、OpenAI 兼容接口等真实大模型 API。
- Local、Semantic Scholar、OpenAlex 文献适配器。
- dry-run 和本机 shell 实验执行后端。Web 控制台默认使用本机 shell：大模型生成代码后会写入 `code/`，然后在当前机器运行。
- 支持 `acm`、`ieee`、`springer_lncs`、`chinese_thesis` 四种论文格式。
- 输出 Markdown、LaTeX 和编译报告。
- 如果启用 PDF 编译且本地安装 LaTeX 工具链和所需 class 文件，可以尝试编译 PDF。
- Vue Web 控制台，支持模型配置、论文上传、进度观察和阶段结果预览。

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

## CLI 快速开始

```powershell
autoscholarloop run `
  --seed "I want to study retrieval-augmented agents for scientific writing." `
  --loop-mode fast `
  --paper-format ieee `
  --workspace runs/demo
```

真实大模型运行示例：

```powershell
$env:OPENAI_API_KEY='your_api_key'
$env:AUTOSCHOLARLOOP_HTTP_TRUST_ENV='0'
autoscholarloop run `
  --seed "your research idea" `
  --provider openai-compatible `
  --model deepseek-chat `
  --base-url https://api.deepseek.com/v1 `
  --execution-backend shell `
  --compile-pdf `
  --workspace runs/deepseek_demo
```

说明：

- `local` provider 只是 deterministic demo。
- 真实科研运行需要配置 OpenAI-compatible 模型 API 和 key。
- 系统总会生成 `paper/main.tex`。
- PDF 只有在启用编译且本地 LaTeX 环境支持目标模板时才会生成。
- 编译会优先使用 `latexmk`，然后回退到 `xelatex` 或 `pdflatex` 多轮编译。

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
- DeepSeek 预设：自动填入 `deepseek-chat` 和 `https://api.deepseek.com/v1`；
- 可关闭系统代理环境变量读取，用于解决部分环境下 `httpx` 连接 DeepSeek 失败的问题；
- 中英文界面切换；
- 研究方向、目标会议/期刊输入；
- PDF、Markdown、文本和 BibTeX 上传；
- 教授组、博士组、写作组和全局大循环轮次配置；
- 本机 shell 实验执行；
- LaTeX 和 PDF 编译报告预览；
- S00-S04 进度可视化；
- field map、idea report、generated code、execution analysis、paper plan、claim evidence、main.tex、compile report、final gate、final draft 预览。

## 输出目录

每次运行会生成一个可审计 workspace：

```text
run/
  source_papers/
  inputs/
  artifacts/
  logs/
  code/
  00_field_context/
  01_decision/
  02_execution/
  03_writing/
  04_quality/
  paper/
  release/
```

重要输出：

- `code/experiments/run_experiment.py`
- `code/methods/proposed_method.py`
- `code/experiments/result.json`
- `00_field_context/field_map.md`
- `01_decision/IDEA_REPORT.md`
- `02_execution/GENERATED_CODE.md`
- `02_execution/RESULTS_ANALYSIS.md`
- `03_writing/PAPER_PLAN.md`
- `03_writing/claim_evidence_table.md`
- `04_quality/CITATION_AUDIT.md`
- `04_quality/final_gate.md`
- `04_quality/compile_report.md`
- `paper/final_draft.md`
- `paper/main.tex`
- `paper/main.pdf`，如果本地 LaTeX 编译成功

## 现实边界

系统可以调用大模型生成代码并默认在本机运行，但真实实验仍然依赖用户机器上的数据集、baseline 代码、Python/conda 环境、CUDA/GPU、训练命令和可用算力。没有真实结果文件时，质量门控不会接受性能类 claim。

## License & Responsible Use

This project is licensed under **The AI Scientist Source Code License**,
a derivative of the Responsible AI License.

用户必须清晰披露 AI 参与，并自行核验所有 claim、引用、实验、作者署名、投稿政策和 AI 使用披露要求。
