# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`GLOSSARY.md`** at the repo root.
- **`docs/DECISIONS.md`**: the project's decision log (this repo's equivalent of ADRs). Read the entries that touch the area you're about to work in.

If `GLOSSARY.md` doesn't exist, **proceed silently**. Don't flag its absence; don't suggest creating it upfront. The `/domain-modeling` skill creates it lazily when terms actually get resolved.

## File structure

Single-context repo:

```
/
├── GLOSSARY.md
├── docs/DECISIONS.md     ← numbered decision log
└── src/
```

## Recording decisions

Do not create `docs/adr/`. New decisions are appended to the bottom of `docs/DECISIONS.md` as the next numbered `## N. Title` section, using the existing **Context / Decision / Alternatives / Trade-off** fields. When a skill says "write an ADR", it means this.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `GLOSSARY.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag decision conflicts

If your output contradicts an entry in `docs/DECISIONS.md`, surface it explicitly rather than silently overriding:

> _Contradicts Decision 2 (kerf is modelled exactly), but worth reopening because…_
