# JLPT — Anki card factory

This repo turns the user's study annotations on **JLPT study materials** into
high-quality Anki flashcards. It is built to handle **many source documents**
over time (listening 聴解 transcripts, reading 読解 passages, vocab/grammar
lists, etc.), not just one PDF.

## What this project is

The user is studying for the JLPT. For each source they take a PDF (a 聴解
transcript, a reading passage, …), annotate it in Zotero, and export the
annotations to a `notes.md`. Each annotation is either a word/phrase they don't
know, a grammar/conjugation point they want explained, or a sentence/paragraph
they want broken down. **Our job: turn those annotations into beautiful,
practical study cards** and deliver them to the user's Anki.

Each source lives in its own folder under `sources/`. New material = a new
folder; the workflow below is the same every time.

## Environment (read carefully)

- We run inside **WSL (Linux)**. **Anki is installed on the user's Windows
  machine**, not here.
- Delivery is via a generated **`.apkg`** file, built with **`genanki`** in
  `.venv/`. We copy it to `/mnt/c/Users/isolino/Downloads/` and the user
  double-clicks it in Windows to import.
- **Decks are additive — NEVER replace or overwrite an existing deck.** Importing
  an `.apkg` never deletes cards. We keep deck/model IDs and per-card GUIDs
  stable so re-imports update in place rather than duplicate. Do not change the
  fixed IDs in `anki/models.py`.

## Decks

- The default deck is **`JLPT N3`** (keeps its pinned ID; the user's existing
  deck is preserved).
- Route a source to its own **subdeck** with `::`, e.g.
  `JLPT N3::N3 Choukai Script`. Subdecks are additive and let the user study one
  source or everything at once.
- Other levels are fine too — just name the deck accordingly, e.g.
  `JLPT N2::Reading 1`. A card file names its deck via the object form (below).

## Layout

```
jlpt/
├── CLAUDE.md                  # this file
├── sources/                   # source material, one folder per PDF (read-only)
│   └── <source-name>/
│       ├── <something>.pdf     # the annotated document
│       └── notes.md            # exported Zotero annotations = the task list
├── .venv/                     # python venv with genanki (not in git)
└── anki/
    ├── models.py              # note types (models) + shared CSS + deck IDs
    ├── build.py               # reads cards/**/*.json -> builds & copies JLPT_N3.apkg
    ├── cards/                 # card CONTENT, grouped in a subfolder per source
    │   ├── <source-name>/*.json
    │   └── EXAMPLE.json.sample # format reference (NOT built; *.json only)
    └── dist/                  # generated .apkg output (not in git)
```

## Workflow

1. Pick the source folder in `sources/<source-name>/`. Read its `notes.md` (and
   check the sentence in the PDF for context — page numbers are in the Zotero
   links, `...page=N...`).
2. Write card data as JSON into `anki/cards/<source-name>/<section>.json`, with
   `"deck"` set for that source (see format below).
3. Build & deliver:
   ```bash
   .venv/bin/python anki/build.py        # builds ALL cards/**/*.json and copies to Downloads
   ```
   `build.py` always rebuilds the single `JLPT_N3.apkg` from every card file, so
   one import carries every source's decks; re-imports update, never duplicate.
4. Tell the user it's in their Downloads and to double-click `JLPT_N3.apkg`.
5. **Commit & push.** After every significant change or completed pass (a batch
   of new cards, a round of fixes, a CLAUDE.md edit, etc.), `git add` the work,
   commit it with a clear message, and `git push`. The card JSON is the only
   record of the deck's progress, so don't leave finished work uncommitted. The
   generated `.apkg`/`dist/` and `.venv/` stay out of git. Commit the source
   change and the build together so the repo always matches what was delivered.

If `genanki` is ever missing, recreate the venv:
`python3 -m venv .venv && .venv/bin/python -m ensurepip --upgrade && .venv/bin/python -m pip install genanki`

## Build modes

**A. Single-batch mode (DEFAULT).** One session handles one source page / one
section (問題). Cheap, simple, easy to review. Use this unless the user
explicitly asks for the orchestrated run below. Do **not** spawn subagents in
this mode.

**B. Orchestrated mode (parallel subagents).** ONLY when the user explicitly asks
to "do the whole source" / "do all pages" / "spin up the workflow". Act as an
orchestrator for the source the user named:

1. Split that source's work by page (or 問題). Each annotation in the source's
   `notes.md` carries its page in the Zotero link (`...page=N...`); group by it.
2. Spawn one subagent per page (Agent tool, `run_in_background: true` to run them
   in parallel). Give each subagent: the source folder, its page number, the
   verbatim annotations for that page, the deck name to use, and an instruction
   to read `CLAUDE.md` first.
3. Each subagent **only writes its own** `anki/cards/<source>/<NN>-<section>.json`
   and returns a one-line summary. Subagents must **NOT** run `build.py` and must
   **NOT** copy anything.
4. When all subagents finish, the orchestrator runs `.venv/bin/python
   anki/build.py` **once** to merge every `cards/**/*.json` into the single
   `JLPT_N3.apkg` and copy it to Downloads. Then report per-page coverage.

Rules that keep parallelism safe:
- **Namespaced IDs.** Every card `id` MUST be globally unique; prefix it with the
  source + page, e.g. `n3cs-p1-jimusho`, `n3cs-p7-yousoo`. `build.py` aborts on
  any duplicate `id`, so collisions are caught at merge time.
- **One file per agent**, distinct filename — no two agents touch the same file.
- **Same `deck` in every file** for one source, so the cards land together.
- **Only the orchestrator builds** — never the subagents — to avoid racing on
  `dist/JLPT_N3.apkg` and the Windows copy.
- Distinct filenames are sufficient isolation (no worktrees needed).

Tradeoff: orchestrated mode is faster wall-clock but uses more tokens (each
subagent re-derives context from cold). Prefer it for a full source; use
single-batch mode for one-offs and careful style review.

## Card design principles

These came from the user — honor them, but **stay flexible**: different
annotations need different layouts. Pick the note type (or invent a better one)
that teaches the point best.

- **Japanese-first, English on click.** The back shows the explanation in
  Japanese (`ExplainJP`). English (`ExplainEN`) is hidden behind a native
  `<details>` toggle (`英語の説明を見る`) so the user *chooses* to reveal it.
  Always provide both; the user can lean on English while it's still needed.
- **Furigana, no romaji.** Never use romaji. Use Anki's built-in furigana
  notation in fields: a space, then `漢字[かな]`, e.g. ` 事務所[じむしょ]`.
  Templates render it with `{{furigana:...}}`. Only put readings on kanji.
  **Bracket notation ONLY in furigana-rendered fields** (see list below):
  `Word`, `ExampleJP`, `Point`, `Structure`, `Examples`, `Sentence`,
  `Breakdown`. In the prose/English fields the templates render *plain*
  (`ExplainJP`, `ExplainEN`, `Meaning`, `Translation`, `Question`, `ExampleEN`)
  bracket notation is NOT rendered and shows up as ugly inline `必要[ひつよう]`
  clutter — **never put it there.** Write `ExplainJP` as clean kanji prose; if a
  specific kanji's reading is genuinely needed mid-explanation, use a small
  parenthetical like `事務（じむ）`, not bracket notation.
- **Vocab gets two cards:** Recognition (JP→meaning) and Production
  (meaning→JP). Both come free from the `vocab` note type.
- **NEVER leak the answer onto the front.** This is the most common bug. Know
  what each card's *front* shows and keep the thing being tested out of it:
  - **Vocab Production (meaning→JP)** front = `Meaning` + `PartOfSpeech`; the
    answer is the Japanese `Word`. So `Meaning` and `PartOfSpeech` must contain
    **no Japanese** that gives the word away — not the word itself, not one of
    its kanji, not its dictionary/related form (e.g. for `泊まり` don't write
    "連用形 of 泊まる"; for `汚れ` don't write "from 汚れる / 汚す"; for `意識`
    don't write "意識する = …"; for `ぺこぺこ` don't write "(おなかがぺこぺこ)").
    Keep these fields English-only — `Meaning` is a plain English gloss and
    `PartOfSpeech` is a plain English/grammatical label (`noun`, `する-verb`,
    `い-adjective`, `mimetic adverb`…). Grammar-class kana like the `する` in
    "する-verb" is fine; the *target word's* characters are not.
  - **Vocab Recognition (JP→meaning)** front = `Word` + `PartOfSpeech`; the
    answer is the English `Meaning`, so don't put the English meaning in
    `PartOfSpeech`.
  - All the derivation/nuance you'd want to put in `Meaning`/`PartOfSpeech`
    belongs on the **back** instead — `ExplainJP` / `ExplainEN`, which only
    render after the answer. That's where "泊まる の名詞形", "汚れる / 汚す", etc.
    go.
  - `grammar` (`Point` shown on front) and `sentence` (`Sentence` shown on
    front) are *meant* to show the prompt; just keep the back-only explanation
    out of `Question`/the fixed prompt.
- **Explanations must be genuinely good.** Don't just translate — explain the
  *why*: break compounds into their kanji, show the dictionary form behind a
  conjugation, name the grammar pattern, note casual contractions
  (〜とく←〜ておく, 〜ちゃう←〜てしまう, なくって, んだ, etc.), and give the nuance.
  This is the whole point of the deck.
- **Real examples.** Prefer the actual sentence from the source as the example so
  the card is anchored to something the user studied.
- **Tag every card** with at least `N3` (or the level), a skill tag
  (`choukai`/`dokkai`/…), and a type tag (`vocab`/`grammar`/`sentence`); add the
  section (e.g. `1番`) when useful.
- **`Source`** should locate the card in the material, e.g. `N3 Choukai · 1番`.

## Note types (defined in `anki/models.py`)

| type       | use for                              | key fields |
|------------|--------------------------------------|------------|
| `vocab`    | single words / set phrases           | `Word`, `Reading`, `Meaning`, `PartOfSpeech`, `ExplainJP`, `ExplainEN`, `ExampleJP`, `ExampleEN`, `Source` |
| `grammar`  | grammar / conjugation / expressions  | `Point`, `Question`, `Structure`, `ExplainJP`, `ExplainEN`, `Examples`, `Source` |
| `sentence` | breaking down a full sentence/block  | `Sentence`, `Translation`, `Breakdown` (HTML table), `ExplainJP`, `ExplainEN`, `Source` |

## Card data format (`anki/cards/**/*.json`)

A file is EITHER:
- a JSON **array** of card objects → they go to the default deck `JLPT N3`, or
- a JSON **object** `{"deck": "JLPT N3::Some Source", "cards": [ ... ]}` → they
  go to the named deck/subdeck. **Use the object form** so each source lands in
  its own deck.

Every card object needs:
- `type`: `"vocab"` | `"grammar"` | `"sentence"`
- `id`: a short **stable, globally-unique** string (becomes the Anki GUID).
  Editing a card's content later updates the same card; **never reuse an `id`**
  for a different card or you'll overwrite it. Prefix with the source (e.g.
  `n3cs-p1-...`) to keep ids unique across sources.
- the fields for that type (see table above); omitted fields render as empty and
  are hidden (templates guard with `{{#Field}}`).
- optional `tags`: array of strings.

See `anki/cards/EXAMPLE.json.sample` for a worked example of all three types.
(`build.py` globs `*.json` recursively, so the `.sample` file is never built.)

### HTML helpers available in fields
- Word-by-word breakdowns: a `<table class="breakdown">` with
  `<td class="part">…</td>` for the chunk and a plain `<td>` for the gloss.
- Furigana notation (` 漢字[かな]`) works ONLY inside the fields a template runs
  through `{{furigana:…}}`: `Word`, `ExampleJP`, `Point`, `Structure`,
  `Examples`, `Sentence`, `Breakdown`. Everywhere else (`ExplainJP`, `ExplainEN`,
  `Meaning`, `Translation`, `Question`, `ExampleEN`) it is shown verbatim, so the
  brackets become unreadable inline clutter — keep those fields as plain text.

## Conventions / gotchas

- Don't edit the source PDFs or `notes.md` files — they're the source material.
- Keep the IDs in `anki/models.py` frozen once cards have shipped.
- When you finish a batch, note in your reply which annotations were covered so
  the user can track progress against that source's `notes.md`.
