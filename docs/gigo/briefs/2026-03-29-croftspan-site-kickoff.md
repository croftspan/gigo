# Croftspan.com — Site Kickoff Packet

## What This Is

Build the Croftspan company site. Product (GIGO) already exists. Now work backwards: company wraps the product.

## The Play

Croftspan is a consultancy. The short-term offering:

**Intake, prediscovery, and discovery as a service.** For a setup fee + monthly retainer, Eaven comes in and gets your company/org set up with AI processes. Scales out your internal AI or AI offering. GIGO is the tool. Eaven is the operator who knows how to wield it.

This isn't "install our plugin." This is "hire the person who built the plugin to set up your organization."

## Who Is Eaven

Full resume at `~/Downloads/me/Profile (2).pdf`. Key points:

- Blockfolio ($150M exit) — built from MVP, scaled team 7→50+ in 4 months
- ToppsNFTs ($500M exit) — NFT marketplace with fiat on/off ramp
- Sortium — $14M raise, AI + Web3 + XR
- Authorly — converted 40+ children's books to apps, worked with NYT bestselling authors
- Self-taught. U-Haul regional manager → directing app dev → founding companies
- Pattern: figure out the new thing, build the process, do it myself, then scale it

The PE reviewer said: "Your credibility IS the product differentiation. Every other Claude Code prompt library is made by someone who read a blog post. Yours is made by someone who's actually run teams, shipped products."

## What Croftspan.com Needs

### Pages

1. **Homepage** — What Croftspan does, for whom, the transformation. Not "we're an AI consultancy." The problem → transformation → how.
2. **About/Founder** — Eaven's story. Not the full resume. The pattern: figure it out, build the process, scale it. Track record that earns trust.
3. **Services** — The enterprise play. Setup + retainer. What they get. What changes. NOT a laundry list of deliverables.
4. **GIGO** — Link to the product. "Built by the same person who'll set up your org."
5. **Contact** — Simple.

### Voice

The GIGO site voice (Dunford/Wiebe/Dry) applies here but elevated. This isn't a developer tool page. This is a consultancy. The audience is CTOs, VPs of Engineering, founders who need their AI workflows fixed. They've tried vibe-coding. They've tried prompt libraries. They need someone who's done this before.

From the Croftspan messaging framework:
- Core message: "One team. Full context. Work that ships."
- Supporting: Cross-domain coherence, context that compounds, speed without shortcuts, quality with a name on it
- Tagline: "One team. Full picture." (or evolve this)

### Pillars to Carry Forward

From PILLARS.md (the 10 pillars). Not all need to be on the site, but the DNA should be:
- **Craftsmanship** — every deliverable is a signed piece of work
- **Reputation** — the only asset that compounds forever
- **Intellectual Honesty** — if we can't do it at our standard, we turn it down
- **Excellence as Identity** — not a value we aspire to, it's who we are

### What NOT to Do

- Don't make it look like an agency portfolio site (it's not an agency anymore, it's a consultancy)
- Don't list AI personas as "team members" (the PE reviewer flagged this as misleading)
- Don't oversell. The track record speaks. Let it.
- Don't duplicate GIGO content. Link to it.
- No "proven." Use "validated" or "battle-tested."
- No em dashes in copy.
- No jargon the customer wouldn't use.

### Design

The GIGO site design system is clean (Space Grotesk, dark-first, steel blue accent, section/container pattern). Croftspan could share the design language or differentiate. Consultancy sites tend to be warmer than developer tools. Consider:
- Same font (Space Grotesk) for brand consistency
- Warmer accent color? Or keep steel blue as the Croftspan family color
- The 義剛 kanji watermark is GIGO-specific, don't reuse

## Existing Brand Assets

All in `~/croftspan/croftspan-app/executive/brand/`:
- `brand-strategy.md` — full brand strategy
- `messaging-framework.md` — core messages, supporting messages, proof points
- `voice-guide.md` — voice attributes, tone spectrum, writing samples
- `visual-identity.md` — color palette, typography, photography direction
- `style-guide.md` — usage guidelines
- `business-model.md` — pricing, tiers, unit economics
- `outreach-strategy.md` — go-to-market

Also:
- `~/Downloads/me/how-it-started/PILLARS.md` — the 10 pillars
- `~/Downloads/me/how-it-started/STANDARDS.md` — quality standards, banned phrases
- `~/Downloads/me/how-it-started/SERVICES.md` — full service catalog (for reference, not to replicate)

## How to Start

1. Create `~/projects/croftspan-site/` (new project, fresh Claude session)
2. Run `gigo:gigo` to assemble a team. The domain: "consultancy website for an AI operations expert. The audience is CTOs and engineering leaders. The tone is confident, warm, specific. The site needs to sell expertise, not software."
3. Then `/gigo:blueprint` to plan the site
4. The voice session's Dunford/Wiebe/Dry context is the foundation but this site needs its own team since the domain is consultancy marketing, not developer tools

## The Prompt

```
gigo

Building the Croftspan company website. Croftspan is a consultancy run by a solo founder (Eaven) with $650M+ in exits who builds AI operational processes for companies. The product is GIGO (a Claude Code plugin for expert team assembly and pipeline management) but the service is the human expertise — setup, training, ongoing retainer.

The audience is CTOs, VPs of Engineering, and founders who need their AI workflows to actually produce consistent, reviewable output. They've tried vibe-coding. They've tried prompt libraries. They need someone who's done this before.

The site needs: homepage, about/founder page, services page, link to GIGO, contact. The voice should be confident but warm. Not a developer tool page. A consultancy that happens to have built the best tool in the space.

Existing brand assets are at ~/croftspan/croftspan-app/executive/brand/ (messaging framework, voice guide, brand strategy, visual identity). The credibility review findings are at ~/projects/gigo/docs/gigo/briefs/2026-03-29-credibility-overhaul.md. The founder's resume is at ~/Downloads/me/Profile (2).pdf.

The PE reviewer said: "You're not building a developer tool. You're building the operational playbook for how one person runs an AI-native company." That's the positioning for this site.
```
