# Titan LifeMap — IP Boundary

> Read this before adding or editing any discovery question, prompt, or scoring content.

---

## Why This Document Exists

Patrick raised the same concern twice during this project's development — first regarding Stephen Covey's 7 Habits and ActionCoach's goal-setting/Focus Sheet methodology, then again regarding CEG Worldwide's Total Client Profile (TCP) Interview Guide. The concern is legitimate and the rule is consistent both times: **draw on universal underlying concepts, never copy or closely paraphrase someone else's specific proprietary expression of those concepts.**

## What CEG's Total Client Profile Guide Actually Contains

Patrick shared the actual document (`T10 TCP Interview Guide-PDF.pdf`, Tactic 10 of CEG's "Adopt Consultative Client Relationship Management," sourced from Prince & Associates research). It contains seven categories — Values, Goals, Relationships, Assets, Advisors, Process, Interests — each with a specific set of verbatim interview questions.

**This is licensed, copyrighted, proprietary content.** The category labels, the specific question wording, and the particular set/sequence of categories are CEG's creative expression. Nobody owns the general idea of "ask a financial planning client about their values" — but CEG's specific execution of that idea is protected.

## Why Titan LifeMap Is Distinct, Not a Rename

Titan LifeMap does not reorganize or reword CEG's seven categories. It is built on an entirely different philosophical architecture:

- **CEG's sequencing** moves through Values → Goals → Relationships → Assets → Advisors → Process → Interests — broadly values-first but with no explicit philosophy preventing early financial framing.
- **Titan LifeMap's sequencing** is explicitly Visionary → Sage → Builder → Steward → Guardian — financial data is deliberately the *last* thing captured, anchored in Patrick's own Seven Titans framework, which predates and is independent of this project.
- **Titan LifeMap's categories** (Life Vision, Definition of Enough, Core Values, Family and Relationships, Relationship With Money, Behavioural Patterns, Health-Wealth-Happiness, Purpose and Legacy) are a different set, mapped to the Seven Titans archetypes, not a relabeling of CEG's seven.
- **Every question in `apps/titan_lifemap/config/stages.yaml`** is written fresh, without consulting CEG's specific wording while writing.

## The Rule for Any Future Content Addition

Before adding or editing any question, prompt, or scoring content in this system:

1. Did you write this fresh, or did you paraphrase a specific source (CEG, Covey, ActionCoach, or any other named methodology)?
2. If you're unsure whether a phrase is "too close" to a known source, rewrite it from the underlying concept rather than editing the close paraphrase.
3. The category *concepts* (values, goals, relationships, money history, behavioural patterns) are universal and safe to reference by name. The specific wording, structure, and sequencing of someone else's proprietary methodology is not.
4. When in doubt, ask Patrick directly — he has read the source materials and can confirm whether something is safe.

## Verification

Per the implementation plan's Success Criteria: *"No content in `config/stages.yaml` can be traced to CEG's Total Client Profile guide, Covey's 7 Habits, or ActionCoach materials — verified by Patrick's own review, since he is the one with direct knowledge of those source materials."* This review should happen before Titan LifeMap goes live with real users, not just at initial build time.
