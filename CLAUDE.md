# JLPT N3 — Anki card factory

This repo turns the user's study annotations on a JLPT **N3 listening (聴解)**
transcript into high-quality Anki flashcards.

## What this project is

The user is studying for the JLPT N3. They read a 聴解 transcript
(`N3script.pdf`), annotated it in Zotero, and exported the annotations to
`script_notes.md`. Each annotation is either a word/phrase they don't know, a
grammar/conjugation point they want explained, or a sentence/paragraph they want
broken down. **Our job: turn those annotations into beautiful, practical study
cards** and deliver them to the user's Anki.

## Environment (read carefully)

- We run inside **WSL (Linux)**. **Anki is installed on the user's Windows
  machine**, not here.
- Delivery is via a generated **`.apkg`** file (chosen by the user), built with
  **`genanki`** in `.venv/`. We copy it to `/mnt/c/Users/isolino/Downloads/` and
  the user double-clicks it in Windows to import.
- **The deck is named `JLPT N3`.** If it already exists in the user's Anki, the
  import **adds to / updates** it. **NEVER replace or overwrite the existing
  deck.** Importing an `.apkg` never deletes cards, and we keep deck/model IDs
  and per-card GUIDs stable so re-imports update in place rather than duplicate.
  Do not change the fixed IDs in `anki/models.py`.

## Layout

```
jlpt/
├── CLAUDE.md            # this file
├── N3script.pdf         # the 聴解 transcript (source, read-only)
├── script_notes.md      # the user's annotations (source, read-only) — the task list
├── .venv/               # python venv with genanki (not in git)
└── anki/
    ├── models.py        # note types (models) + shared CSS. Structure/styling live here.
    ├── build.py         # reads cards/*.json -> builds & copies JLPT_N3.apkg
    ├── cards/           # card CONTENT, one JSON file per batch/section
    │   └── EXAMPLE.json.sample   # format reference (NOT built; *.json only)
    └── dist/            # generated .apkg output (not in git)
```

## Workflow

1. Read the relevant annotations in `script_notes.md` (and check the sentence in
   `N3script.pdf` for context — page numbers are in the Zotero links).
2. Write card data as JSON into `anki/cards/<section>.json` (see format below).
3. Build & deliver:
   ```bash
   .venv/bin/python anki/build.py        # builds and copies to Windows Downloads
   ```
4. Tell the user it's in their Downloads and to double-click `JLPT_N3.apkg`.

If `genanki` is ever missing, recreate the venv:
`python3 -m venv .venv && .venv/bin/python -m ensurepip --upgrade && .venv/bin/python -m pip install genanki`

## Build modes

**A. Single-page mode (DEFAULT).** One session handles one page / one 問題. Cheap,
simple, easy to review. Use this unless the user explicitly asks for the
orchestrated run below. Do **not** spawn subagents in this mode.

**B. Orchestrated mode (parallel subagents).** ONLY when the user explicitly asks
to "do all pages" / "spin up the workflow". Act as an orchestrator:

1. Split the work by page (or 問題). The transcript is pages 1–13 of
   `N3script.pdf`; each annotation in `script_notes.md` carries its page in the
   Zotero link (`...page=N...`). Group annotations by that page.
2. Spawn one subagent per page (Agent tool, `run_in_background: true` to run them
   in parallel). Give each subagent: its page number, the verbatim annotations
   for that page, and an instruction to read `CLAUDE.md` first.
3. Each subagent **only writes its own** `anki/cards/<NN>-<section>.json` and
   returns a one-line summary of what it covered. Subagents must **NOT** run
   `build.py` and must **NOT** copy anything.
4. When all subagents finish, the orchestrator runs `.venv/bin/python
   anki/build.py` **once** to merge every `cards/*.json` into the single
   `JLPT_N3.apkg` and copy it to Downloads. Then report the per-page coverage.

Rules that keep parallelism safe:
- **Namespaced IDs.** Every card `id` MUST start with its page, e.g. `p1-jimusho`,
  `p7-yousoo`. Guarantees global uniqueness across agents; `build.py` aborts on
  any duplicate `id`, so collisions are caught at merge time.
- **One file per agent**, distinct filename (`01-rei-1ban.json`, `07-7ban.json`,
  …) — no two agents touch the same file.
- **Only the orchestrator builds** — never the subagents — to avoid racing on
  `dist/JLPT_N3.apkg` and the Windows copy.
- Not a git repo, so no worktrees; distinct filenames are sufficient isolation.

Tradeoff: orchestrated mode is faster wall-clock but uses more tokens (each
subagent re-derives context from cold). Prefer it for a full run; use single-page
mode for one-offs and careful style review.

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
- **Vocab gets two cards:** Recognition (JP→meaning) and Production
  (meaning→JP). Both come free from the `vocab` note type.
- **Explanations must be genuinely good.** Don't just translate — explain the
  *why*: break compounds into their kanji, show the dictionary form behind a
  conjugation, name the grammar pattern, note casual contractions
  (〜とく←〜ておく, 〜ちゃう←〜てしまう, なくって, んだ, etc.), and give the nuance.
  This is the whole point of the deck.
- **Real examples.** Prefer the actual sentence from the transcript as the
  example so the card is anchored to something the user heard.
- **Tag every card** with at least `N3`, `choukai`, and a type tag
  (`vocab`/`grammar`/`sentence`); add the section (e.g. `1番`) when useful.
- **`Source`** should locate the card in the material, e.g. `N3 Choukai · 1番`.

## Note types (defined in `anki/models.py`)

| type       | use for                              | key fields |
|------------|--------------------------------------|------------|
| `vocab`    | single words / set phrases           | `Word`, `Reading`, `Meaning`, `PartOfSpeech`, `ExplainJP`, `ExplainEN`, `ExampleJP`, `ExampleEN`, `Source` |
| `grammar`  | grammar / conjugation / expressions  | `Point`, `Question`, `Structure`, `ExplainJP`, `ExplainEN`, `Examples`, `Source` |
| `sentence` | breaking down a full sentence/block  | `Sentence`, `Translation`, `Breakdown` (HTML table), `ExplainJP`, `ExplainEN`, `Source` |

## Card data format (`anki/cards/*.json`)

A file is a JSON array of card objects. Every object needs:
- `type`: `"vocab"` | `"grammar"` | `"sentence"`
- `id`: a short **stable, globally-unique** string (becomes the Anki GUID).
  Editing a card's content later updates the same card; **never reuse an `id`**
  for a different card or you'll overwrite it.
- the fields for that type (see table above); omitted fields render as empty and
  are hidden (templates guard with `{{#Field}}`).
- optional `tags`: array of strings.

See `anki/cards/EXAMPLE.json.sample` for a worked example of all three types.
(`build.py` globs `*.json`, so the `.sample` file is never built into the deck.)

### HTML helpers available in fields
- Word-by-word breakdowns: a `<table class="breakdown">` with
  `<td class="part">…</td>` for the chunk and a plain `<td>` for the gloss.
- Furigana notation (` 漢字[かな]`) works inside any field that a template runs
  through `{{furigana:…}}` (Word, Example, Point, Structure, Examples,
  Sentence, Breakdown).

## Conventions / gotchas

- Don't edit `N3script.pdf` or `script_notes.md` — they're the source material.
- Keep IDs in `anki/models.py` frozen once cards have shipped.
- When you finish a batch, note in your reply which annotations were covered so
  the user can track progress against `script_notes.md`.
