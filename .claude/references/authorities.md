# Authorities — Avengers Assemble

The people and research that inform how this skill ecosystem works. Read this when blending authorities for new personas, when validating design decisions against research, or when the operator asks "why do we do it this way?"

## The ETH Zurich SRI Lab

**Martin Vechev** — Full professor, ETH Zurich. Leads the Secure, Reliable, and Intelligent Systems Lab. Six spin-offs: DeepCode (acquired by Snyk), InvariantLabs (secure AI agents, acquired), LogicStar (AI code agents), NetFabric, LatticeFlow, ChainSecurity. His lab's research on LLM reliability directly informs our approach to context management.

**Veselin Raychev** — Pioneered AI-for-code at ETH in 2013. Co-founded DeepCode. ACM Doctoral Dissertation Award Honorable Mention — only the 3rd European in the award's 40-year history. His work on learning from code at scale established that tool/interface design matters as much as model capability.

**Niels Mündler** — PhD at SRI Lab focused on faithfulness and correctness of generated code. Created SWT-Bench for testing agent validation. Co-authored the AGENTS.md paper.

**Thibaud Gloaguen** — PhD at SRI Lab. Led the "Evaluating AGENTS.md" study (arXiv:2602.11988, Feb 2026). His key finding: LLM-generated context files reduce task success rates by ~3% while increasing cost by 20%+. Developer-written files help only ~4%, and only when containing non-inferable information.

### Key Paper: "Evaluating AGENTS.md" (Gloaguen et al., 2026)

**Methodology:** Tested 4 agents (Claude Code/Sonnet-4.5, Codex/GPT-5.2, Codex/GPT-5.1-mini, Qwen Code/Qwen3-30b) across SWE-bench Lite (300 tasks) and AGENTbench (138 tasks from 12 repos with developer-written context files).

**Critical findings that shape this skill:**
1. LLM-generated context files hurt performance in 5/8 settings
2. Context files cause agents to explore more broadly but not more effectively (14-22% more reasoning tokens)
3. Repository overviews in context files did NOT help agents find relevant files faster
4. When existing docs were removed, context files helped +2.7% — they only add value when filling genuine knowledge gaps
5. Agents faithfully follow context file instructions — the problem isn't disobedience, it's that unnecessary requirements make tasks harder
6. Recommendation: "Include only minimal requirements (e.g., specific tooling to use with this repository)"

**What this means for us:** The skill must produce context files that contain ONLY non-derivable, genuinely useful knowledge. The 60-line cap, derivability test, and The Snap all trace back to this research.

## Boris Cherny — Creator of Claude Code

**Key practices:**
- CLAUDE.md as institutional memory: "Anytime we see Claude do something incorrectly we add it to the CLAUDE.md"
- Runs 5+ parallel sessions via git worktrees
- Plan mode first, then auto-accept after alignment
- Uses Opus for everything: "less steering + better tool use = faster overall results"
- #1 tip: "Give Claude a way to verify its work — 2-3x quality improvement"
- Skill design: build for workflows repeated daily, "Gotchas" sections are highest-signal content
- Treats CLAUDE.md like code: review when things go wrong, prune regularly, test changes

## Anthropic Engineering Guides

### "Building Effective Agents" (Dec 2024)
Core philosophy: "Start with the simplest solution possible, only increase complexity when needed." Five composable patterns: prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer. Key insight: the most successful implementations use simple patterns, not complex frameworks.

### "Effective Context Engineering" (2025)
Defines context engineering as "curating the optimal set of tokens during inference." Key principle: "Find the smallest set of high-signal tokens maximizing desired outcome likelihood." Introduces just-in-time retrieval, compaction, structured note-taking, and sub-agent architectures.

### "Writing Tools for Agents" (2025)
Tools are only as good as their descriptions. "Tools that are most ergonomic for agents also end up being surprisingly intuitive for humans." Prioritize token efficiency, natural formats, and clear documentation. Anthropic spent more time optimizing tools than prompts for SWE-bench.

### "Effective Harnesses for Long-Running Agents" (2025)
Initializer + coding agent pattern. One feature at a time, incremental progress. Key: write progress artifacts so the next session can orient itself.

## Agent Research (Cited by Gloaguen et al.)

**Yang et al. — SWE-agent (NeurIPS 2024):** Agent-Computer Interface (ACI) design. Careful interface design improves agent performance without modifying model weights. Custom commands with concise, context-limited outputs prevent overwhelming the context window.

**Shinn et al. — Reflexion (2023):** Agents that verbally reflect on task feedback in episodic memory make dramatically better decisions. 91% pass@1 on HumanEval. The mechanism: linguistic feedback stored in memory, not weight updates.

**Liu et al. — "Lost in the Middle" (2023):** LLMs struggle with information positioned in the middle of long contexts. Performance peaks at beginning and end. Critical for rules file design — put the most important content first and last.

**Kong et al. — Role-Play Prompting (2023):** Personas activate relevant domain knowledge when specific. Accuracy improvements of 10-60% on reasoning benchmarks. The mechanism: personas trigger chain-of-thought reasoning more effectively than "think step by step."

**Pei et al. — "When a Helpful Assistant Is Not Really Helpful" (2023):** Generic personas ("helpful assistant") perform no better than no persona at all across 162 personas tested. The key distinction: *specific, task-matched* personas help. *Generic* ones don't.

**Xu et al. — ExpertPrompting (2023):** Detailed, customized expert identity descriptions per instruction improve answer quality. The persona must be *synthesized for the specific task*, not a generic role.

**Hu et al. — "Expert Personas Improve LLM Alignment but Damage Accuracy" (2026):** Persona effectiveness is task-type dependent. Expert personas consistently improve alignment-dependent tasks (writing style, tone, safety refusal, format adherence: +0.40 to +0.65 on MT-Bench) but consistently damage pretraining-dependent tasks (factual recall, coding knowledge, math: -0.10 to -0.65). Longer personas amplify both effects. Models more optimized for system-prompt steering are more sensitive to both gains and losses. For reasoning-distilled models, gains come from added context length triggering reasoning chains, not from persona identity itself.

**Hong et al. — MetaGPT (2023):** Multi-agent framework with SOPs and intermediate verification. Assembly line paradigm with diverse roles. Key insight: checking at every stage prevents cascading hallucinations.

## What This Means for Persona Blending

The research presents a nuanced picture: personas work when they're **specific syntheses of real authorities** (Kong, Xu, Pei) — but they also carry a cost. Hu et al. (2026) showed that persona context competes with factual recall at the attention level, consistently degrading knowledge-retrieval tasks even when the persona is well-matched.

This means every persona in the skill ecosystem must:
1. Name 2-3+ specific authorities with their distinct contributions
2. Explain what each authority brings to the blend
3. Apply specifically to the project's domain, not generically
4. Be concrete enough that the persona would produce measurably different output than a generic prompt
5. **Separate alignment signal from knowledge signal** — alignment-shaping content (quality bars, approach, anti-patterns) belongs in always-on rules; domain-knowledge content (factual specifics, technical details) belongs in on-demand references
6. **Include task-type awareness** — personas should know when to step back and let the model's training lead (see persona template)
