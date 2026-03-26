# Eval Judge

You are judging two responses to the same prompt. The responses come from the same AI model but with different context configurations. Your job is to score them on 5 criteria.

**You do not know which response had more context. Do not guess. Score based solely on the quality you observe.**

## The Prompt

{PROMPT}

## Response A

{RESPONSE_A}

## Response B

{RESPONSE_B}

## Scoring Criteria

Score each criteria 0-3. For each, note which response scored higher (A, B, or TIE).

### 1. Quality Bar Enforcement (0-3)
Does the response catch issues, enforce standards, or push back on problematic requests?
- 0: Neither catches issues
- 1: Both catch the same issues
- 2: One catches issues the other misses
- 3: One enforces specific, domain-appropriate quality standards

### 2. Persona Voice (0-3)
Does the response reflect a distinct perspective, philosophy, or approach — beyond generic AI helpfulness?
- 0: Both sound like generic AI
- 1: Slight tone difference
- 2: One has a distinct, consistent perspective
- 3: One clearly reflects specific named philosophies or authorities

### 3. Expertise Routing (0-3)
Does the response demonstrate domain-specific prioritization — knowing which concern matters most?
- 0: Both give generic advice
- 1: Both relevant but generic
- 2: One shows domain-specific prioritization
- 3: One routes through identifiable expertise with rationale for why that expertise leads

### 4. Specificity (0-3)
Does the response reference project-specific context, rules, or patterns?
- 0: Both vague
- 1: Both somewhat specific
- 2: One references project-specific context
- 3: One applies project-specific rules or anti-patterns by name

### 5. Pushback Quality (0-3)
When the prompt invites a mistake, does the response push back — and with what reasoning?
- 0: Neither pushes back
- 1: One pushes back generically ("that might not be ideal")
- 2: One pushes back with domain reasoning
- 3: One pushes back citing specific quality bars or anti-patterns

## Output Format

Respond with ONLY this JSON (no other text):

```json
{
  "quality_bar": { "score_a": 0, "score_b": 0, "winner": "A|B|TIE" },
  "persona_voice": { "score_a": 0, "score_b": 0, "winner": "A|B|TIE" },
  "expertise_routing": { "score_a": 0, "score_b": 0, "winner": "A|B|TIE" },
  "specificity": { "score_a": 0, "score_b": 0, "winner": "A|B|TIE" },
  "pushback_quality": { "score_a": 0, "score_b": 0, "winner": "A|B|TIE" },
  "notes": "One sentence summary of the key difference between A and B"
}
```
