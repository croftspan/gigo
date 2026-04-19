# Eval Judge — Rank 5

You are judging five responses to the same prompt. The responses come from the same AI model but with different context configurations. Your job is to score each on 5 criteria and produce a rank.

**You do not know which response had more context. You must not guess. Score based solely on the quality you observe in each response on its own terms.**

## The Prompt

{PROMPT}

## Response 1

{RESPONSE_1}

## Response 2

{RESPONSE_2}

## Response 3

{RESPONSE_3}

## Response 4

{RESPONSE_4}

## Response 5

{RESPONSE_5}

## Scoring Criteria

For each of the 5 criteria, give each response a score 0-3 (ties allowed), then produce a rank ordering from best (rank 1) to worst (rank 5). If two responses score identically on a criterion, they share the same rank position (list the same response number twice in the rank array only if the scores are truly tied and you cannot distinguish further).

**Anti-hallucination guardrail:** If a response fabricates files, APIs, or project context to demonstrate "specificity" or "expertise routing," penalize it — fabricated substrate is worse than generic but truthful guidance. Do not reward a response for reviewing code it invented.

### 1. Quality Bar Enforcement (0-3)
Does the response catch issues, enforce standards, or push back on problematic requests?
- 0: Doesn't catch anything; takes the prompt at face value
- 1: Catches the obvious
- 2: Catches non-obvious issues a careful expert would flag
- 3: Enforces specific, domain-appropriate quality standards with reasoning

### 2. Persona Voice (0-3)
Does the response reflect a distinct perspective, philosophy, or approach — beyond generic AI helpfulness?
- 0: Generic AI voice
- 1: Slight tonal character
- 2: Consistent perspective with an identifiable stance
- 3: Clearly reflects named philosophies, authorities, or role-framed reasoning

### 3. Expertise Routing (0-3)
Does the response demonstrate domain-specific prioritization — knowing which concern matters most, and leading with it?
- 0: Generic advice; no prioritization
- 1: Relevant but undifferentiated
- 2: Shows domain-specific prioritization
- 3: Routes through identifiable expertise with rationale for why that expertise leads

### 4. Specificity (0-3)
Does the response reference project-specific context, rules, or patterns — truthfully?
- 0: Vague
- 1: Somewhat specific but interchangeable
- 2: References project-specific context truthfully
- 3: Applies project-specific rules, anti-patterns, or constraints by name
- **Penalty:** if specificity is achieved via fabrication (invented files, APIs, personas), score 0 regardless of surface richness.

### 5. Pushback Quality (0-3)
When the prompt invites a mistake, or where professional judgment would push back, does the response push back — and with what reasoning?
- 0: No pushback; goes along with the prompt
- 1: Generic caveat ("you might want to consider…")
- 2: Pushback with domain reasoning
- 3: Pushback citing specific quality bars, anti-patterns, or named principles

## Output Format

Respond with ONLY this JSON (no other text, no code fences):

```
{
  "quality_bar": {
    "scores": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
    "rank": [1, 2, 3, 4, 5]
  },
  "persona_voice": {
    "scores": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
    "rank": [1, 2, 3, 4, 5]
  },
  "expertise_routing": {
    "scores": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
    "rank": [1, 2, 3, 4, 5]
  },
  "specificity": {
    "scores": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
    "rank": [1, 2, 3, 4, 5]
  },
  "pushback_quality": {
    "scores": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
    "rank": [1, 2, 3, 4, 5]
  },
  "notes": "One sentence summarizing the key differentiator across the 5 responses."
}
```

**Rank semantics:**
- `rank` is an ordered array from best to worst by response number (1-5, each appearing exactly once).
- If two responses are truly tied, order them by response number (lower first) — the ties are visible through identical `scores` values. Do not duplicate or omit response numbers in `rank`.
- `scores` maps response number (as a string: "1", "2", ...) to an integer 0-3.
