# ⚙️ Antigravity Work Instructions — Resonant AI Build

These are the **operating rules** for any agent (or sub-agent) executing `BUILD_INSTRUCTIONS.md` inside Antigravity. They govern *how* work happens, not *what* to build — the source of truth for scope remains `BUILD_INSTRUCTIONS.md`. Every rule below is mandatory unless the user explicitly overrides it in-session.

---

## 1. Governing Principles (read first)

1. **One step at a time.** Never start step *N+1* until step *N* has been implemented, verified, and explicitly marked complete.
2. **Verify before advancing.** Every step ends with a verification gate (see §4). No gate = no progress.
3. **Minimize tokens aggressively.** Treat context and output tokens as a scarce, billed resource (see §3).
4. **Right-size the model.** Not every task needs the most capable/expensive model — route by task complexity (see §2).
5. **Never silently deviate.** If a build instruction is ambiguous, contradictory, or technically unsound (e.g. claims like "sub-35ms latency," "DriverKit," "C++ ring buffer" implemented in `ring_buffer.py`), flag it and ask/log an assumption instead of guessing.
6. **Small, reviewable diffs.** Each step should touch the minimum files needed for that step only.

---

## 2. Sub-Agent Orchestration & Model Routing

Use a **lead/orchestrator agent** plus **specialized sub-agents**. The orchestrator never writes large amounts of code itself — it plans, delegates, and verifies.

| Role | Responsibility | Recommended Model Tier | Why |
|---|---|---|---|
| **Orchestrator (Lead)** | Reads `BUILD_INSTRUCTIONS.md`, breaks it into steps, delegates one step at a time, reviews sub-agent output, runs verification gates, updates the roadmap checklist. | Highest-capability model available (e.g. your top-tier reasoning model) | Needs strong planning, judgement, and cross-file reasoning; but it should call this model *sparingly* — for planning/review only, not bulk generation. |
| **Scaffolding Sub-Agent** | Boilerplate: folder structure, `.gitignore`, `.env.example`, config files, package manifests. | Small/cheap model | Purely templated, low-reasoning work. |
| **Backend/Audio Engine Sub-Agent** | Python audio pipeline: ring buffer, `sounddevice` I/O, ONNX Runtime inference wiring, quantization scripts. | Mid-to-high capability coding model | Real-time/DSP + concurrency code needs correctness-focused reasoning. |
| **ML/Training Sub-Agent** | PyTorch training scripts, ONNX export, INT8 quantization, vocoder/timbre-encoder integration. | Mid-to-high capability coding model | Needs domain familiarity with ML tooling; isolate from the audio-engine agent to keep context small. |
| **Frontend/Electron Sub-Agent** | React + Tailwind system tray UI, IPC bindings. | Mid-capability coding model | Well-trodden patterns; doesn't need top-tier reasoning. |
| **Database/Supabase Sub-Agent** | SQL DDL, RLS policies, `supabase_client.py`. | Mid-capability coding model | Schema work is templated but security-sensitive — needs a review pass by the orchestrator, not a bigger model. |
| **DevOps/Packaging Sub-Agent** | PyInstaller, electron-builder, code signing/notarization scripts. | Small/cheap model | Command sequences, low ambiguity. |
| **Docs/Landing Page Sub-Agent** | GoDaddy Airo copy, HTML widget snippet. | Small/cheap model | Static content generation. |
| **Compliance/Research Sub-Agent** | DPIIT, CDSCO, FDA, HIPAA/GDPR notes. | Small/cheap model, web-search enabled | This is research/summarization, not code — never burn a large coding model on it. |

**Routing rule of thumb:** default to the *cheapest model that has historically succeeded* at that task category. Escalate to a stronger model only when a sub-agent's output fails verification twice.

**Isolation rule:** each sub-agent gets **only** the files/context relevant to its current step — never hand a sub-agent the entire `BUILD_INSTRUCTIONS.md` or full repo tree. The orchestrator extracts and passes the minimal relevant slice.

---

## 3. Token Minimization Rules

1. **Context slicing:** never paste the full 1000+ line `BUILD_INSTRUCTIONS.md` into a sub-agent prompt. Extract only the relevant `Feature N` section (Objective / Files Needed / Step-by-Step Logic / Testing Verification) for the step at hand.
2. **No redundant re-reads:** once a file has been read in a session, reuse that content from working memory/notes rather than re-viewing it, unless it may have changed.
3. **Summarize, don't paste, prior work:** when the orchestrator briefs a sub-agent on completed steps, pass a **one-paragraph summary** ("ring buffer + audio ingestion done, exposes `AudioRingBuffer` class in `ring_buffer.py`"), not the full file contents.
4. **Diff-sized output:** sub-agents should output only the code/content that changed, not full-file reprints, when editing an existing file.
5. **Batch related, sequence unrelated:** small same-file edits can be batched into one sub-agent call; unrelated features must stay in separate calls so failures don't cascade and force re-generation of unrelated work.
6. **Cap verification chatter:** verification steps should produce short pass/fail + evidence, not long narrative explanations.
7. **Prune the roadmap file, not re-summarize it:** update the checklist in place (see §5) rather than regenerating full status reports each step.

---

## 4. Step-Wise Execution & Verification Gate Protocol

For **every** step (each `Feature N` sub-task, each DB migration, each packaging action):

```
1. PLAN   — Orchestrator states: goal of this step, files to touch, sub-agent assigned, model tier.
2. BUILD  — Sub-agent implements only this step. Nothing else.
3. SELF-CHECK — Sub-agent runs the "Testing Verification" listed for that feature in
              BUILD_INSTRUCTIONS.md (or a reasonable equivalent: lint, unit test,
              manual smoke test, schema check).
4. VERIFICATION PLAN — Orchestrator writes/executes a short, explicit checklist, e.g.:
     [ ] File(s) created at correct path
     [ ] Code compiles / imports without error
     [ ] Feature's stated "Testing Verification" criterion passes
     [ ] No secrets/credentials committed
     [ ] No unrelated files modified
5. GATE   — Only if ALL verification items pass → mark step ✅ complete, commit,
            and move to the next step. If ANY item fails → stop, report, fix, re-verify.
              Do not proceed on partial success.
6. LOG    — One-line status appended to the roadmap/checklist (see §5).
```

**Hard rule:** a step is never "mostly done." It is either ✅ verified-complete or 🔴 blocked/in-progress. No step is started while another is 🔴.

---

## 5. Progress Tracking

Maintain a single lightweight `PROGRESS.md` (not a bloated log) mirroring the Phase 1/Phase 2 checklist from `BUILD_INSTRUCTIONS.md §6`. Each line updated in place:

```
- [x] Feature 1: Audio ingestion & virtual mic routing — verified 2026-08-26
- [ ] Feature 2: Model training / INT8 quantization / ONNX engine — in progress (Backend/ML sub-agent, mid-tier model)
- [ ] Feature 3: Timbre encoder & Vocos vocoder
...
```

This file is the **single handoff artifact** between steps and sessions — sub-agents and the orchestrator read this instead of re-deriving status from scratch, saving tokens.

---

## 6. Safety & Security Rules (non-negotiable)

1. **Never commit secrets.** `.env`, `*.pem`, `*.key`, service-role keys stay out of git per the provided `.gitignore` — verify this in every step touching config.
2. **No raw audio/PCM persisted to cloud.** Only encrypted embeddings go to Supabase, per the compliance notes (HIPAA / GDPR Art. 9 — voice biometric data is Special Category data).
3. **RLS policies are mandatory**, not optional, on any Supabase table holding user or biometric data — verify policy exists before marking the DB step complete.
4. **Flag, don't fabricate, compliance claims.** Statements like "bypasses invasive class-C/D medical approvals" or specific reimbursement dollar amounts are regulatory claims — the agent must not present these as verified facts; flag them for human/legal review rather than treating them as build requirements.
5. **Flag unrealistic technical claims** (e.g., sub-35ms end-to-end latency for a full neural pipeline, a `.py` file described as a "C++ Circular Ring Buffer") as assumptions/risks in the PLAN step rather than quietly building around them.

---

## 7. Escalation Rules

An agent must pause and surface the issue to the user (not guess) when:
- A verification gate fails twice in a row on the same step.
- The build instructions conflict with each other or with the tech stack (e.g., a Python file claimed as C++).
- A step requires credentials, licenses, or accounts (Supabase project, Apple Developer ID, GoDaddy) not yet provided.
- Legal/regulatory/medical-device claims need sign-off beyond what an agent can verify.

---

## 8. Summary Cheat-Sheet

| Rule | One-liner |
|---|---|
| Orchestration | Lead agent plans/reviews; sub-agents execute one narrow task each |
| Model routing | Cheapest model that historically succeeds at that task type; escalate only after 2 failures |
| Token minimization | Slice context, summarize instead of paste, diff-sized output only |
| Execution order | Strictly one step at a time — no parallel unrelated steps |
| Verification | Explicit checklist gate after every step; must fully pass before advancing |
| Progress tracking | Single `PROGRESS.md`, updated in place |
| Security | No secrets in git, no raw audio in cloud, RLS mandatory |
| Escalation | Stop and ask on repeated failure, conflicting specs, or missing credentials |
