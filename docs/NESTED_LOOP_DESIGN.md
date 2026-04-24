# Nested Loop Design

AutoResearcher is organized as a nested-loop research system.

## Layers

```text
Non-loop preparation layer:
  S00 field context and evidence base

Local loop layer:
  S01 professor decision loop
  S02 PhD execution-review loop
  S03 writing-review loop
  S04 quality gate

Research big loop:
  decision -> execution -> review -> writing -> audit -> return/pivot/kill/promote
```

## S00 Field Archive

S00 is mostly non-loop. It converts user input, papers, code pointers, and
constraints into a shared evidence base.

Required outputs:

- `field_map.md`
- `paper_cards.md`
- `method_map.md`
- `dataset_baseline_map.md`
- `evidence_bank.md`

Repair loop triggers:

- too few papers;
- papers are from inconsistent subfields;
- PDF parsing failed;
- baseline or dataset information is missing.

## S01 Professor Decision Loop

S01 is mandatory. The professor group must not generate one-shot ideas.

Standard loop:

- R01-R03: understand field and challenge novelty assumptions;
- R04-R06: generate ideas and attack weaknesses;
- R07-R08: refine strong ideas and delete weak ones;
- R09-R10: converge on 3-5 ideas;
- frontier scout checks overlap;
- selected direction is handed to executors.

Stop conditions:

- minimum rounds reached;
- 3-5 candidates exist;
- each candidate has closest prior work;
- each candidate has dataset, baseline, and evaluation plan;
- no near-duplicate is found;
- one direction is selected.

## S02 PhD Execution-Review Loop

S02 is the strongest loop.

Each round writes:

- execution report;
- result summary;
- failure analysis;
- professor review memo.

Default standard rounds:

- R01 baseline scan;
- R02 baseline reproduction;
- R03 method implementation;
- R04 debugging/main experiment;
- R05 ablation/result analysis.

Allowed decisions:

- `continue`
- `revise`
- `add_experiment`
- `pivot`
- `kill`
- `promote_to_writing`

## S03 Writing-Review Loop

S03 turns evidence into a paper. It is not a polishing stage.

Required checks:

- claim has evidence;
- contribution matches experiments;
- related work covers recent work;
- method is reproducible;
- experiment description is fair;
- limitations are honest.

The central artifact is:

- `claim_evidence_table.md`

## S04 Quality Gate

S04 is a gate, not a long loop.

It writes:

- `novelty_audit.md`
- `citation_audit.md`
- `reproducibility_audit.md`
- `claim_audit.md`
- `final_gate.md`

Routing:

- novelty failure -> S01;
- experiment failure -> S02;
- writing overclaim -> S03;
- citation failure -> S00 or S03;
- unrecoverable direction -> killed.
