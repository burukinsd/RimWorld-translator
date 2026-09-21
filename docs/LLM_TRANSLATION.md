# Local & Remote Translation Model Landscape (EN→RU)

Research notes feeding the hybrid translation architecture in
`ARCHITECTURE.md`. Goal: neutral, comparative data for a **benchmark-driven**
model choice — this document deliberately does not declare a single "best"
model. Every model here is a candidate the benchmark subsystem (Epic 10)
must be able to slot in and measure; the actual production choice is a
Phase 13 decision made from real numbers, not from this document.

Confidence markers: **VERIFIED** (primary source, e.g. official
paper/blog/model card), **CORROBORATED** (consistent secondary sources),
**UNVERIFIED** (flagged explicitly by the research pass — treat as a
hypothesis to test in the benchmark harness, not a fact to design around).

## 1. TranslateGemma (Google)

**VERIFIED real and released.** Announced by Google (~Jan 2026, technical
report arXiv:2601.09012) as a family of open translation models built on the
**Gemma 3** foundation (fine-tuned decoder-only instruct LLM, not a
classic seq2seq encoder-decoder like Marian/NLLB).

- **Sizes:** 4B, 12B, 27B.
- **Training:** SFT on human + high-quality synthetic parallel data, then an
  RL phase against MetricX-QE and AutoMQM reward models plus a "naturalness"
  autorater.
- **Prompting:** instruction/chat format — expects a single user message
  ("You are a professional {SRC} to {TGT} translator...") followed by the
  source text, not a fixed source→target token pair the way NLLB/MADLAD are
  called.
- **Language coverage:** 55 "core" languages benchmarked against WMT24++.
  **Russian is explicitly one of the 55**, and en→ru is one of the evaluated
  pairs in the technical report.
- **Benchmarks:** WMT24++ scored with MetricX24/COMET22, plus human MQM on
  WMT25. Reported MetricX improvements over same-size untuned Gemma 3:
  27B 23.5% better, 12B 25.9% better, 4B 23.6% better (lower MetricX = better).
  **Notably, the 12B TranslateGemma checkpoint outperforms the untuned 27B
  Gemma 3 baseline** — a strong data point for a VRAM-constrained pipeline:
  bigger isn't automatically better once you compare a translation-tuned
  mid model against an untuned larger general model.
- **Context window:** **UNVERIFIED** for the translation-tuned checkpoint
  specifically. Gemma 3 base supports up to 128K; TranslateGemma may inherit
  this but no source directly confirms it. Ollama's default serving context
  (2048) is a serving-time default, not necessarily the trained max — verify
  empirically.
- **License:** Gemma Terms of Use (custom, includes a Prohibited Use Policy),
  **not** vanilla Apache-2.0 — Google's newer Gemma 4 line moved to
  Apache-2.0 (~March 2026), but TranslateGemma is Gemma-3-based and predates
  that shift. **UNVERIFIED** whether Google has since re-licensed it.
  **Action item:** confirm current license terms before shipping any
  TranslateGemma-derived output in a distributed product.
- **Self-hosting:** first-class — listed in the Ollama library
  (`translategemma:4b/12b/27b`) and available as community GGUF quantizations,
  runs on llama.cpp/Ollama like any Gemma 3 derivative.
- **Placeholder/structured-text handling:** **no formal published benchmark**
  exists for placeholder or XML-tag preservation specifically. Community
  prompt-engineering guidance recommends explicitly instructing the model to
  leave `{{...}}`/tag-like tokens untouched, implying this is not
  automatically guaranteed — needs prompt-level enforcement and our own
  validator, same as any instruct-LLM-based translator. **This is exactly
  the kind of gap our benchmark subsystem must fill (§6).**

**Verdict:** first-class local candidate. The 4B tier is the likely default
for bulk short UI strings (fast, cheap); 12B as a stronger default that still
fits a single consumer GPU; 27B as an optional local "hard string"
escalation tier before falling back to cloud. None of this is prescriptive —
it's exactly what Epic 10's benchmark harness should confirm or overturn.

## 2. Other candidate models

| Model | Sizes | EN-RU suitability | Ollama/llama.cpp | Approx. VRAM (4-bit) | License | One-line verdict |
|---|---|---|---|---|---|---|
| **NLLB-200** (Meta) | 600M / 1.3B / 3.3B / up to 54.5B MoE | Purpose-built for 200 languages incl. Russian; robust but flatter "naturalness" than modern instruct LLMs | Encoder-decoder; not a native Ollama chat model, runs via CTranslate2/transformers, GGUF/CT2 community ports exist | 600M ≈3GB · 1.3B ≈5.5GB · 3.3B ≈13GB (or ≈7.6GB CT2 int8) | **CC-BY-NC 4.0** | Cheap high-throughput comparator; NC license blocks commercial shipping as primary engine. |
| **MADLAD-400** (Google) | 3B-MT / 7.2B / 10B-MT (T5) | 450+ languages incl. Russian; 3B-MT "competitive with much larger models" per authors | T5 arch; GGUF community quantizations exist but not first-class Ollama citizens; custom `<2ru>` prompting | 3B ≈2–4GB Q4 | Research license (verify per HF card); Google's own card notes "not assessed for production use" | Good low-cost breadth comparator, not a primary-engine candidate as shipped. |
| **OPUS-MT** (Helsinki-NLP, Marian) | ~300MB per language pair | Dedicated `opus-mt-en-ru`; BLEU 23.5–31.1 (news), 48.4 (Tatoeba, short/colloquial — closer proxy to game UI strings) | Not native Ollama/GGUF — served via CTranslate2 or Marian/transformers; CPU-viable | <1GB | CC-BY 4.0 | See §3 — fast/cheap sanity-check baseline and disagreement-detection signal, not a quality leader. |
| **Aya 23 / Aya Expanse / Tiny Aya** (Cohere) | 8B / 35B / 13B / 3.35B | 23–101 languages incl. Russian; translation a named use case | Standard HF transformer, GGUF community ports, runs on llama.cpp/Ollama | 8B ≈5–6GB · 35B ≈20GB · Tiny ≈2GB | **CC-BY-NC 4.0 + Cohere AUP** (current-gen; older Aya-101 is Apache-2.0) | Good research/prototyping quality candidate; NC license makes current-gen Aya **risky to ship** in a commercial pipeline — verify before use. |
| **Qwen2.5 / Qwen3.x Instruct** (Alibaba) | 0.5B–72B+, 7B/14B/27–32B common locally | General multilingual instruct, strong reported Russian performance, not translation-specialized | First-class Ollama + llama.cpp GGUF | 7B ≈5.5GB · 27–32B ≈17–20GB | Apache 2.0 (most releases) | Strong general local fallback tier for tricky flavor text; needs careful placeholder-preservation prompting since it's not MT-tuned. |
| **Llama 3.x / 4** (Meta) | 8B–405B | Meta's officially supported language list does **not** include Russian (EN/DE/FR/IT/PT/HI/ES/TH only) — model has seen Russian data but without an official quality guarantee | Full Ollama/llama.cpp support | 8B ≈5.5GB · 70B ≈40GB | Llama Community License (custom, mostly permissive) | Usable fallback but not a first choice for EN-RU given no official Russian support. |
| **Mistral / Mixtral** | 7B, 8x7B, Small/Large | Generalizes to European languages reasonably; no particular EN-RU edge documented | Full Ollama/llama.cpp support | 7B ≈5GB · 8x7B ≈26GB (MoE) | Apache 2.0 (most open releases) | Reasonable general fallback, no documented advantage over Qwen3/Gemma3 for Russian specifically. |
| **DeepSeek V3 / R1** | 671B MoE (37B active) | One third-party benchmark reports DeepSeek-R1 leading a Russian-language eval (76.4%) ahead of GPT-4.1 (72.7%); DeepSeek's own documented strength is Chinese-English | Full size impractical to self-host (300GB+ even 4-bit); smaller distills lose the reported edge | n/a locally | MIT (weights) | Interesting **cloud-API** fallback candidate, impractical as a local model. Applicability of the cited 76.4% figure to short game-UI strings is **UNVERIFIED**. |
| **YandexGPT** | 5-Lite + larger closed tiers | Native Russian-first model; strong in principle for RU-as-target | Primarily closed/hosted API, not self-hostable at the large tier | n/a | Proprietary API | Plausible RU-quality cloud fallback; adds a non-Western vendor/compliance dependency — a business decision, not just technical. |
| **Vikhr family** (Vikhrmodels, RU open-source) | 7B/8B tier (`Vikhr-YandexGPT-5-Lite-8B-it`, Mistral-based variants) | Bilingual RU/EN, adapted (not just LoRA'd) tokenizer specifically for Russian | GGUF/Ollama-compatible | 8B ≈5.5GB | Open weights (verify per checkpoint; base derived from YandexGPT-5-Lite pretrain) | Strong RU-native candidate worth benchmarking directly against Gemma/TranslateGemma — built RU-first rather than RU-as-one-of-many. |
| **T-lite / T-pro** (T-Bank) | T-lite 7B (Qwen2.5-based) / T-pro 32B | RU-adapted continuation of Qwen2.5; claims top scores among RU-focused open models on MERA/ruMMLU/Ru Arena Hard/MT-Bench/AlpacaEval | Full GGUF/Ollama/llama.cpp (Qwen-architecture) | 7B ≈5.5GB · 32B ≈20GB | Apache 2.0 | Another strong RU-native benchmark candidate; Qwen-based, easy to slot alongside Qwen3 in tooling. |

## 3. OPUS-MT as lightweight baseline

- **Architecture:** classic Marian NMT transformer, SentencePiece tokenizer,
  trained per language-pair — `opus-mt-en-ru` is a dedicated pair model, not
  a multilingual model.
- **Size / speed:** ~300MB, very fast on CPU relative to any LLM (no
  sourced exact throughput number — must be benchmarked directly).
- **Quality:** BLEU 23.5–31.1 on WMT news test sets, 48.4 on Tatoeba (short,
  colloquial sentences — the closer proxy to RimWorld-style short strings).
- **Critical limitation:** no placeholder awareness or instruction-following
  whatsoever — it will treat `{0}` or `[PAWN_nameDef]` as arbitrary text to
  translate/reorder around, with no way to instruct it otherwise. This is the
  single biggest quality risk for RimWorld content specifically.
- **Serving:** directly compatible with **CTranslate2**, which applies
  quantization/layer-fusion/batch-reordering — a well-regarded
  high-throughput serving path for Marian-class models.
- **License:** CC-BY 4.0 — effectively unrestricted commercial use.
- **Verdict:** not a primary-quality candidate, but an excellent fast/cheap
  pre-filter or **disagreement-detection signal** — e.g. flag strings where
  OPUS-MT and the primary LLM disagree sharply as a proxy for "needs
  review," or use as a near-zero-cost first pass on bulk/low-value strings.

## 4. Local inference backends

- **Ollama wraps llama.cpp**; registry models are GGUF under the hood.
  Gemma 3/TranslateGemma, Qwen2.5/3.x, Llama 3.x, Mistral/Mixtral, and
  smaller DeepSeek distills all have first-class Ollama entries. NLLB-200,
  MADLAD-400, and OPUS-MT (Marian, encoder-decoder, non-chat-format) are
  **not** native Ollama citizens — they need CTranslate2/transformers or
  community GGUF ports with custom prompt handling instead of the standard
  Ollama chat API. **This is an architecture-relevant split**: the local
  provider abstraction needs at least two backend shapes (chat-style
  instruct models via Ollama's OpenAI-compatible API, and encoder-decoder
  MT models via a CTranslate2-style adapter).
- **API surface:** Ollama exposes both native `/api/generate`/`/api/chat`
  and an OpenAI-compatible `/v1/chat/completions` endpoint.
- **Structured output:** Ollama supports constrained JSON-schema output via
  `response_format`/`format`, through both APIs — directly usable to enforce
  a `{translation, preserved_placeholders}`-shaped response instead of
  trusting free-text output parsing.
- **Quantization tradeoffs** (general guidance, not translation-specific
  benchmarks — flagged as a gap our own benchmark harness should fill):
  - **Q4_K_M** — default "good enough" tier, smallest footprint, real but
    modest quality loss vs Q5/Q8.
  - **Q5_K_M** — meaningfully better fidelity at moderate size increase;
    candidate default for the local "hard string" escalation tier.
  - **Q8_0** — near-lossless vs full precision, largest of the three.
  - K-quants allocate precision non-uniformly and generally beat naive
    uniform quantization at the same bit-width.
  - **Open question for the benchmark harness:** does quantization degrade
    placeholder-copying accuracy disproportionately vs general fluency? No
    literature answers this for MT-style structured text — must be measured
    directly.
- **Throughput at scale:** Ollama is positioned (own docs/community
  consensus) for a handful of concurrent requests rather than max-throughput
  batch serving; `OLLAMA_NUM_PARALLEL` (default 1) and `OLLAMA_MAX_QUEUE`
  (default 512) govern concurrency. For genuinely high-throughput batch
  translation of a large string corpus (tens of thousands of strings across
  ~180 mods), dedicated serving stacks (vLLM for chat-format models,
  CTranslate2 for Marian/NLLB/MADLAD-class models) are commonly cited as
  more throughput-oriented. **No concrete strings/sec numbers were found for
  Ollama-served Gemma/TranslateGemma at any batch size — must be measured
  against our actual corpus size during Phase 6/7.**

## 5. Remote/cloud fallback options

| Provider | Class | EN-RU / localization notes | Structured output | Approx. pricing tier (2026, general) |
|---|---|---|---|---|
| **Claude** | General LLM | Strong at following precise constraints ("never alter text inside `{}`/`[]`") — good fit for the escalation tier on idiom/tone/ambiguous-gender strings (Russian case/gender agreement) | Native tool-use / JSON-schema-constrained output | Sonnet-class ≈$2/$10 per 1M in/out · Opus-class ≈$5/$25 · Haiku-class ≈$1/$5 |
| **GPT-4o / GPT-5.x class** | General LLM | Widely used industry translation fallback; mature JSON-mode/structured-outputs support | Native `response_format: json_schema` | GPT-5.x-class ≈$2/$10 per 1M in/out |
| **Gemini** | General LLM | One cited 2026 industry benchmark (Alconost) ranks Gemini ahead of Claude/GPT on an aggregate translation-quality index — **a single third-party source, not independently cross-verified here; treat as a hypothesis to check against our own benchmark, not a ranking to design around** | Native structured output / JSON mode | Flash-class ≈$0.75/$3.75 per 1M in/out — notably cheap, relevant for a high-volume fallback tier |
| **DeepL API** | Dedicated MT product (not an LLM) | Purpose-built for localization workflows; documented placeholder/"Mustache tag" handling — the most directly game-localization-aware product here, but its tag handling should be validated against RimWorld's specific `{0}`/`[PAWN_nameDef]` token styles, not assumed to work out of the box | No JSON/tool-call mode — relies on its own tag-handling feature | ≈$5.49/mo + ≈$25 per million characters (character-, not token-, based) |

General industry signal (single source, Alconost 2026, not independently
verified): general-purpose LLMs are reported to now outrank dedicated MT
engines on an aggregate quality index, with the gap reportedly widening
under professional-linguist evaluation. **Do not treat this as settled for
our domain** — short, structured, placeholder-heavy game strings are a
different distribution from the news/prose content typically benchmarked.
This is precisely why Epic 10 exists: measure it ourselves.

**Verdict:** no categorical "best" remote fallback. DeepL's placeholder-tag
feature is the most purpose-built for structured strings; general LLMs with
schema-enforced JSON output give a *programmatic* guarantee that placeholders
survive verbatim by construction, which may be more robust than trusting any
MT engine's internal tag heuristics. Benchmark both approaches directly.

## 6. Benchmark methodology precedent

- **BLEU** — n-gram precision vs. references. Poorly correlated with human
  judgment for short segments, penalizes valid paraphrase, and is not
  placeholder-aware (a translation with a moved-but-present placeholder
  scores as broken even though it may render fine, or vice versa).
- **chrF / chrF++** — character n-gram F-score, tokenization-independent,
  correlates better with human judgment than BLEU, and is specifically
  noted as more suitable for **morphologically complex/highly inflected
  languages** — directly relevant, since Russian's case system changes word
  *forms* in ways exact-token metrics over-penalize.
- **COMET / COMET22 / MetricX** — neural, (optionally reference-free "QE")
  metrics trained to correlate with human judgment; the current standard for
  *ranking* systems (and what TranslateGemma's own RL reward signal was
  built around), less useful as a raw diagnostic than BLEU/chrF. Best
  practice: report alongside chrF/BLEU, not alone.
- **MQM (Multidimensional Quality Metrics)** — the WMT human-evaluation gold
  standard: professional translators annotate specific errors
  (mistranslation, omission, grammar, terminology) with severities, giving
  an error-weighted score. Expensive/slow; the right tool for a small
  sampled tail, not full-corpus coverage at our volume.
- **No established precedent exists in the literature for short,
  placeholder-heavy game-UI string evaluation specifically** — this is a
  genuine gap our benchmark subsystem must fill, not something to adopt
  off-the-shelf. Recommended synthesis:
  1. **Placeholder-integrity check** as a hard pass/fail gate, run *before*
     any fluency scoring: every `{0}`/`{PAWN_x}`-style token from source
     must appear verbatim (same count, same spelling) in the output. A
     broken placeholder crashes or corrupts in-game string formatting — no
     prose-oriented metric flags this as the critical failure it is, so it
     cannot be left to a fluency score to catch.
  2. **chrF++** as the primary automatic lexical metric (short segments,
     Russian morphology).
  3. **A COMET/MetricX-class reference-free QE metric** as a secondary
     ranking signal, so full-corpus scoring doesn't require human reference
     translations for every string.
  4. **Sampled MQM-style human review**, targeted at strings with low
     automatic scores, placeholder failures, or cross-tier disagreement
     (e.g. OPUS-MT vs. TranslateGemma vs. cloud fallback) rather than full
     manual coverage.

This mirrors general MT-evaluation precedent (cheap automatic triage +
neural ranking metric + targeted expensive human review for the tail) while
adding the placeholder-integrity gate that general literature doesn't cover,
because it is specific to structured game-string translation.

## Summary (no declared winner, by design)

| Tier | Candidate(s) | Role in the hybrid pipeline |
|---|---|---|
| Fast/cheap local baseline | OPUS-MT | Bulk pre-pass, sanity check, disagreement-detection signal |
| Local primary, translation-specialized | TranslateGemma 4B/12B | Default local translation engine candidate — confirmed Russian support, RL-tuned for MT quality |
| Local comparator, general multilingual | NLLB-200, MADLAD-400 | Breadth/CPU-only comparators; NC license (NLLB) limits commercial shipping as primary |
| Local RU-specialized | Vikhr-YandexGPT-5-Lite-8B, T-lite-7B/T-pro-32B | Benchmark specifically for RU-target naturalness/idiom |
| Local escalation before cloud | Qwen2.5/3.x 7B–32B, Gemma 3 Instruct | Second local opinion on low-confidence strings before paying for cloud |
| Cloud fallback, dedicated MT | DeepL API | Best-in-class placeholder-tag handling, localization-workflow features |
| Cloud fallback, general LLM | Claude / GPT-5.x / Gemini | Contextual/idiomatic judgment, schema-enforced placeholder safety |

## Open items / UNVERIFIED flags to carry into the benchmark subsystem

1. TranslateGemma's exact trained context window.
2. Whether TranslateGemma has since been re-licensed under Apache-2.0.
3. No published placeholder/XML-tag preservation benchmark exists for any
   candidate model — our benchmark harness is the first to measure this.
4. Ollama-served throughput (strings/sec) for TranslateGemma at any given
   quantization/batch size — needs direct measurement against our corpus.
5. The Alconost "Gemini beats Claude/GPT" ranking is a single source, not
   independently cross-verified.
6. The cited DeepSeek-R1 76.4%-Russian figure's applicability to short
   game-UI strings vs. the benchmark content it was actually measured on.
7. Whether quantization (Q4_K_M vs Q5_K_M vs Q8_0) disproportionately
   degrades placeholder-copying accuracy vs. general fluency.
