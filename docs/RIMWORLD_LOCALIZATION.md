# RimWorld 1.6 Localization Structure — Research Notes

This document records what we could verify about how RimWorld 1.6 stores and
loads localization data, based on primary-source evidence (Ludeon's own
official translation repositories, real community translation mods) and
corroborating wiki summaries. It is the factual foundation for
`ARCHITECTURE.md`. Claims are marked **VERIFIED** (primary-sourced, high
confidence), **CORROBORATED** (multiple independent secondary sources agree,
not directly primary-sourced), or **UNVERIFIED** (best-guess / inferred from
convention — must be confirmed against a real RimWorld install or the wiki
before the extractor hard-codes it).

> Research method note: `rimworldwiki.com`, `rimworldmodding.wiki.gg`,
> `rjw.miraheze.org` and `steamcommunity.com` were unreachable from the
> research sandbox, so wiki claims here come from search-result snippets
> rather than fetched pages. Primary evidence instead comes from raw XML
> fetched directly from Ludeon's own `RimWorld-<Language>` GitHub repos and
> several real community translation-mod repos. Before Phase 2 implementation
> begins, the extraction Def-field list and the full language-folder-name
> table should be re-derived **at runtime from an actual RimWorld
> installation** (`Data/Core/Languages/`) rather than trusted as a static
> list — the tool has that install available to it anyway, which sidesteps
> the whole verification problem.

## 1. Languages folder structure

**VERIFIED.** A mod (or RimWorld's `Core`) carries localization under:

```
<Mod or Core>/
└─ Languages/
   ├─ English/
   │  ├─ DefInjected/<DefTypeName>/<file>.xml
   │  ├─ Keyed/<file>.xml
   │  ├─ Strings/<file>.txt
   │  ├─ Backstories/            (exists in Core; internal format not investigated)
   │  └─ LanguageInfo.xml        (present on full language packs, optional on translation add-ons)
   └─ Russian/
      ├─ DefInjected/<DefTypeName>/<file>.xml
      ├─ Keyed/<file>.xml
      └─ Strings/<file>.txt
```

Mods that target multiple RimWorld versions may instead nest this under a
version folder, e.g. `1.6/Languages/English/...` — the extractor must resolve
the correct version scope the same way RimWorld's own `LoadFolders.xml`
resolution does.

**The folder name is the load-bearing identifier.** RimWorld resolves a
language by the literal folder name under `Languages/` (case-sensitive,
English word form: `Russian`, `German`, `ChineseSimplified`,
`PortugueseBrazilian`, …), **not** by `LanguageInfo.xml` contents.
`LanguageInfo.xml`'s `friendlyNameNative` / `friendlyNameEnglish` fields are
purely for the in-game language-selector UI.

**VERIFIED** — Ludeon's own `RimWorld-ru` repo's `Core/LanguageInfo.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LanguageInfo>
    <friendlyNameNative>Русский</friendlyNameNative>
    <friendlyNameEnglish>Russian / Русский</friendlyNameEnglish>
    <canBeTiny>true</canBeTiny>
    <languageWorkerClass>LanguageWorker_Russian</languageWorkerClass>
    <credits>
        <li Class="CreditRecord_Role">
            <roleKey>Credit_Translator</roleKey>
            <creditee>Андрей 'Elevator89' Лёмин</creditee>
        </li>
    </credits>
</LanguageInfo>
```

For our target language, `Languages/Russian/` with `languageWorkerClass =
LanguageWorker_Russian` is confirmed correct. **A translation-only mod cannot
introduce a new `languageWorkerClass`** — it must reuse the one shipped with
base RimWorld.

**UNVERIFIED (design implication):** we do not have a fully verified,
exhaustive table of every language folder's exact spelling. Rather than
hard-coding one, the scanner should **read the ground-truth folder names
directly from the user's local RimWorld installation** (`Data/Core/Languages/`
and each mod's own `Languages/`), which is strictly more robust and removes
the need for a static list altogether.

## 2. `DefInjected/` format

**VERIFIED.** Root element is always `<LanguageData>`. Each translatable Def
field is addressed by `<DefName.fieldPath>value</DefName.fieldPath>`, and the
**immediate parent folder name must equal the C# Def type name**
(`ThingDef`, `HediffDef`, `PawnRelationDef`, `ThoughtDef`, `TaleDef`, …). The
XML filename itself is arbitrary — RimWorld merges every file under a given
`DefInjected/<DefType>/` folder — but convention mirrors the source `Defs/`
filename for maintainability.

Example (Ludeon `RimWorld-ChineseSimplified`,
`Core/DefInjected/ThingDef/Buildings_Art.xml`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LanguageData>

  <!-- EN: grand sculpture -->
  <SculptureGrand.label>宏伟雕塑</SculptureGrand.label>
  <!-- EN: A huge sculpture sized to dominate a room. -->
  <SculptureGrand.description>一个几乎可以填满房间的巨大雕塑。</SculptureGrand.description>

</LanguageData>
```

**Every entry is preceded by an `<!-- EN: original English text -->`
comment.** This is universal across every fetched Ludeon/community file (both
`DefInjected/` and `Keyed/`) — it is the mechanism translators rely on for
context, and the mechanism our generated Russian mod must reproduce so a
human reviewer editing the output XML directly still has the English
reference alongside it.

**Gendered field suffixes** (not list-indexed — a plain second field on the
Def): e.g. `.label` / `.labelFemale`:

```xml
<Spouse.label>husband</Spouse.label>
<Spouse.labelFemale>wife</Spouse.labelFemale>
```

**List-valued fields** (`List<T>` C# fields such as `stages`, `verbs`,
`comps`): addressed by inserting a zero-based `.N.` segment into the path,
e.g. `HediffGiveIn.stages.0.label`. **UNVERIFIED — reconstructed from
RimWorld's general XML-list-addressing convention**; no literal example was
retrieved verbatim. Must be confirmed against a real vanilla multi-stage
HediffDef DefInjected file before the parser hard-codes this shape.

**RulePack / `rulesStrings`** (used by `TaleDef`, interaction defs, some
backstory/quest generation text): a numbered array of grammar-generation
rule strings. Inside the rule text, substitution uses **square-bracket**
symbols (`[pawn_nameFull]`, `[circumstance_group]`), which is a *distinct*
mechanism from the curly-brace tags used in already-resolved Keyed strings
(§4). This is the GrammarResolver's own rule-authoring syntax, and it is
explicitly called out by existing prior-art tooling as one of the hardest
things to auto-translate safely (rules can reference/expand each other, and
reordering rule words breaks Russian grammatical agreement in ways a naive
per-string translation cannot fix). **Treat RulePack content as an advanced,
lower-priority extraction target, not MVP table-stakes.**

**No evidence of a "PlaceholderLabel" feature.** This term does not appear to
be real RimWorld terminology; do not build tooling around it.

**Built-in QA tooling:** RimWorld has a "Translation report" feature
(language-selection screen) that surfaces load errors and missing-key
coverage — this is a **report**, not a file generator. With Dev Mode
enabled, missing Keyed/DefInjected translations render visibly "glitched" in
game so modders can spot gaps during playtesting. There is no confirmed
official one-click "Generate DefInjected" command in vanilla RimWorld;
that capability comes from third-party tools (RimTrans and similar — §7),
which combine `Defs/` XML scanning with C# reflection over the mod's
compiled assemblies to discover which fields are actually translatable
(pure XML-text scanning under-discovers fields that a Def type marks
translatable in code).

## 3. `Keyed/` format

**VERIFIED.** Same `<LanguageData>` root, but keys are **flat identifiers**
with no dotted Def-path (`JumpToLocation`, `RecruitSuccess`) — this is the
structural way to distinguish a Keyed key from a DefInjected key. Used for
code-referenced UI text, letters, and messages that have no XML Def backing
them.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LanguageData>

  <!-- EN: Jump to location -->
  <JumpToLocation>Jump to location</JumpToLocation>

  <!-- EN: {0} successfully recruited {1} ({2} chance). -->
  <RecruitSuccess>{0} successfully recruited {1} ({2} chance).</RecruitSuccess>

</LanguageData>
```

**File organization:** many small topic-named files (`Letters.xml`,
`Enums.xml`, `Misc.xml`, …), not one giant file. The filename is arbitrary to
the engine — this is a human-organization convention. The tool should mirror
"one output file per logical source group" (e.g. per source-file basename)
for diffability, without needing to match the exact filenames used upstream.

**Community convention (not engine-enforced):** untranslated entries are
sometimes left with the literal value `TODO` as a progress marker. RimWorld's
engine does not treat `TODO` specially — it is just community practice, and
our tool should use its own review-status field in Translation Memory rather
than relying on magic string values in the XML.

## 4. `Strings/` format

**CORROBORATED**, not directly primary-sourced. `Strings/` holds plain
`.txt` files, **one string per line, no XML, no keys** — used for
procedurally-sampled text pools (name generator word lists, tribal name
banks, art/tale description fragments), not fixed lookup entries.

| | `Keyed/` | `Strings/` |
|---|---|---|
| Format | XML key → value | Plain `.txt`, one value per line |
| Purpose | Fixed UI/message/letter text | Word/phrase pools sampled randomly |
| Addressed by | Explicit string key | File identity + line position only |

**Design implication:** `Strings/` content has **no stable per-entry key** —
only file identity and line order. This makes incremental re-translation
much harder to anchor than `Keyed/`/`DefInjected/` (a source-file diff can
tell you a line changed, but not which "logical" entry it corresponds to if
lines are inserted/reordered upstream). The extractor should treat
`Strings/` as a lower-priority, position-indexed special case, not force it
through the same key-based Translation Memory model without adaptation.

## 5. Placeholder / token conventions

Three genuinely distinct mechanisms exist. Conflating them is a real
correctness risk for the validator:

**a) Positional `{0}`, `{1}`, `{2}` — VERIFIED.** Standard .NET
`string.Format` placeholders. The *set and order* of numeric tokens must
survive translation unchanged (Russian word order may legitimately reorder
surrounding text, but the tokens themselves and their total count/identity
must be preserved).

**b) Named GrammarResolver tags, curly-brace form — VERIFIED.** E.g.
`{PAWN_nameDef}`, `{RELATIVE_labelShort}`, resolved against live game-object
data (a pawn, a faction, a relative) rather than positional args. Common
tags include `PAWN_nameDef` (pawn's name), `PAWN_pronoun` (he/she/they,
gender-resolved), `PAWN_possessive` (his/her/their). Confirmed verbatim in
Ludeon's own `RimWorld-ar`:

```xml
<RelatedPawnInvolvedInQuest>{PAWN_nameDef} is {RELATIVE_labelShort}'s {1}. If {PAWN_nameDef} dies, {RELATIVE_labelShort} will suffer...</RelatedPawnInvolvedInQuest>
```

These must pass through translation **verbatim, exact casing** — they are
not natural-language content.

**c) Square-bracket RulePack symbols — VERIFIED, distinct mechanism.**
`[pawn_nameFull]`, `[circumstance_group]` etc. inside `rulePack.rulesStrings`
only (§2). Narrower scope than (a)/(b); do not conflate with the curly-brace
tags — a validator matching `{...}` will not see these, and vice versa.

**d) Rich text tags — CORROBORATED.** RimWorld renders labels/descriptions
via Unity's rich-text system: `<b>`, `<i>`, `<color=NAME>` /
`<color=#HEX>`. Unity rich text has **no escape mechanism for literal
angle brackets**, so a translation introducing a stray `<`/`>` can visibly
break rendering. The validator should check that the *set* of rich-text
tags (open/close pairs, tag names) in a translation matches the source,
the same way it checks `{0}`/`{PAWN_x}` tokens.

**e) Escaping — VERIFIED.** Newlines are written as the literal two-character
sequence `\n` in the XML text content (not an embedded real newline, not an
XML entity):

```xml
<FirstSummerWarning>Summer has begun! But winter is coming.\n\nYour food crops won't grow...</FirstSummerWarning>
```

RimWorld's string loader converts `\n` → real newline at runtime. The
pipeline must treat `\n` as an opaque two-character token to preserve
exactly — never let an LLM "helpfully" turn it into a real newline, and
never double-escape when writing XML back out. Standard XML entity escaping
(`&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`) applies as normal XML content
rules. **UNVERIFIED** whether RimWorld's XML parser tolerates `CDATA`
sections — no fetched example used one; assume plain escaped text only
unless proven otherwise.

## 6. `About.xml` for a translation-only mod

**VERIFIED.** RimWorld fully supports a mod containing **only**
`About/About.xml` + `Languages/`, with **no `Defs/` folder at all**. This is
long-established, standard community practice (multiple real Workshop
translation-only mods confirmed).

Modern minimal example (`ElHanko/rimworld-mod-translation-mod`):

```xml
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <name>RimWorld Mod Translations</name>
  <author>ElHanko</author>
  <packageId>elhanko.rimworld.modtranslations</packageId>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
  <description>
Translations for RimWorld mods, generated and maintained with the bundled translation workflow.
  </description>
</ModMetaData>
```

Full field reference used by well-formed translation add-ons:

```xml
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <name>Awesome Mod [RU]</name>
  <author>YourName</author>
  <packageId>yourname.awesomemod.ru</packageId>
  <description>Russian translation for "Awesome Mod".</description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
  <modDependencies>
    <li>
      <packageId>author.awesomemod</packageId>
      <displayName>Awesome Mod</displayName>
    </li>
  </modDependencies>
  <loadAfter>
    <li>author.awesomemod</li>
  </loadAfter>
</ModMetaData>
```

Key points:

- **`loadAfter` (not `loadBefore`) is the core mechanism** the whole
  "standalone translation mod" strategy depends on. RimWorld merges
  same-language localization data across all active mods in load order;
  later mods' entries win for identical keys. A translation mod loaded after
  the original mod (and after any other translation mods targeting the same
  content) correctly overrides/supplements it.
- **`modDependencies` is a soft correctness aid**, not a hard requirement —
  it improves auto-sort and shows a warning if the target mod is missing,
  but a translation mod still functions without it as long as load order is
  correct. We should always emit it: it makes the generated mod
  self-describing and safer for end users.
- **Naming convention** (community standard, not engine-enforced): append a
  tag to `<name>`, e.g. `"ModName [RU]"`, so it's visually distinguishable
  in the mod list.
- The translation mod's `packageId` is **independent** of the original
  mod's `packageId** — confirming the "never modify the original mod, always
  ship a separate mod" design goal is not just safe but the standard,
  supported pattern.

## 7. Prior art

| Tool | Approach | Relevance / limitation |
|---|---|---|
| **RimTrans** (`RimWorld-zh/RimTrans`, fork `Aironsoft/RimTrans`) | Electron+Vue GUI over a .NET Core extractor that combines `Defs/` XML scanning with **C# reflection over compiled mod assemblies** to discover translatable fields. Produces the canonical `RimWorld-English` template repo. | Proves reflection-assisted extraction works and is trusted enough to be the community's canonical source-template generator. Its own "Translator"/"Modder"/cloud "Translation Workshop" components were largely unshipped (WIP/TODO) — treat as architectural inspiration, not a reference implementation to copy. |
| **`winterheart/RimTranslate`** | Uses **Gettext (`.po`/`.pot`)** as the intermediate translation format instead of round-tripping RimWorld XML directly, gaining `msgmerge`'s mature "fuzzy" stale-entry detection for free. | Interesting alternative to bespoke diffing for the incremental-update problem (§8); we choose SQLite TM instead per the product spec, but its change-detection strategy (hash the source value, not just key presence) is directly worth adopting. |
| **`DrizztGaming/Mod-Translation-Toolkit`** | **Closest prior art to this exact project.** Scans Workshop + local mods (including version-scoped `1.6/Languages/English`), falls back to `Defs/`-only inference when no English DefInjected ships, pluggable translation providers (Google/DeepL/LibreTranslate), only translates still-missing entries (non-destructive incremental), CSV export/import for human review, placeholder-mismatch detection (`{0}`, `%s`, `\n`) without auto-rewriting, generates a full standalone mod with dependency metadata. | Self-reported limitations: custom XML formats, RulesStrings, some quest structures, DLL-embedded/C#-generated strings, and mods with custom localization loaders "typically require manual handling." This directly scopes our own MVP: budget a "cannot auto-extract" bucket for DLL-embedded strings, and treat RulePack/`rulesStrings` as a harder, lower-priority target rather than table-stakes. |
| **`ElHanko/rimworld-mod-translation-mod`** | Not a GUI tool — a reproducible pipeline pattern. Keeps hand-authored translation state in versioned JSON "source of truth" files, generates `Languages/<Language>/` deterministically (never hand-edited). Each entry tracks `text`, `needed`/`review` flags, and critically a **`previous_english`** field retaining the prior source text until a human explicitly reviews a change. Build has an "atomic validation" gate (package identity, entry uniqueness, placeholder preservation, checksum integrity) that fails the build on unresolved/stale entries. | **Strongest confirmed precedent for our stale-detection design**: key the incremental cache on `(DefType/key, hash-of-current-English-value)`, not just key presence, so a reworded English string (Def unchanged) is caught even though key-diffing alone would miss it. |

Other tools noted but not deep-dived: `csh1668/RimworldExtractor`,
`TokcDK/RimworldModTranslator`, `kelvinauta/Rimworld-Mod-Translator`.

## 8. Incremental / versioning concerns

When a source mod updates, DefInjected coverage can go stale in three ways:

1. **Def removed/renamed** → its key(s) become orphaned (harmless to leave,
   but should be reported so the translation mod can be cleaned up).
2. **Def added** → new key(s) needed, currently untranslated (coverage gap).
3. **English field text reworded, but the Def/key itself unchanged** — the
   hardest case: plain key-presence diffing does not catch this. Requires
   diffing the **English value**, not just key existence.

**Design decision, following the `ElHanko` precedent (§7):** the Translation
Memory's `source_hash` column (see `ARCHITECTURE.md` §5) is a hash of the
*current* extracted English value per key. A rebuild that finds a live
English value whose hash no longer matches the TM's `source_hash` for that
key marks the entry stale and routes it back through translation +
validation, rather than silently reusing a now-incorrect cached translation.
This is the single mechanism that generalizes all three staleness cases
above: an orphaned key simply never gets re-emitted; a new key has no TM row
so it is untranslated by definition; a reworded key fails the hash
comparison.

## Open items to verify during Phase 2 implementation

1. Exact literal DefInjected list-index key syntax (`.stages.0.label` etc.)
   against a real vanilla multi-stage HediffDef.
2. Full, authoritative table of `Languages/<X>` folder names — derive at
   runtime from a real RimWorld installation instead of hard-coding.
3. Confirm `Strings/` `.txt` format against an actual shipped file.
4. Investigate `Backstories/` internal format if backstory translation is
   ever in scope.
5. Confirm exact `rulePack.rulesStrings.N` key-path spelling against a real
   vanilla/community TaleDef DefInjected file.
6. Confirm whether RimWorld's XML parser tolerates `CDATA` sections.
7. Confirm which Unity rich-text tags beyond `<b>`/`<color>` actually appear
   in shipped RimWorld content (e.g. `<i>`).
