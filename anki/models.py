"""
Anki note-type (model) and deck definitions for the JLPT N3 deck.

Design notes
------------
* Furigana uses Anki's BUILT-IN notation: write fields as ``事務所[じむしょ]``
  (a space before the kanji run, reading in square brackets). Templates render
  it with the ``{{furigana:Field}}`` filter, so the same field can also be shown
  as plain kanji (``{{kanji:Field}}``) or kana only (``{{kana:Field}}``).
* English explanations are hidden behind a native ``<details>`` toggle so the
  card is Japanese-first and the learner *clicks* to reveal English. Works
  offline on desktop, AnkiDroid and AnkiMobile (no JavaScript required).
* IDs below are fixed. NEVER change them once the deck has shipped, or Anki will
  treat the model/deck as new and you will get duplicates. Adding cards is safe.

Keep this file focused on *structure + styling*. Card CONTENT lives in
``anki/cards/*`` and is assembled by ``anki/build.py``.
"""

import genanki

# --- Fixed IDs (do not change) ------------------------------------------------
DECK_ID = 1622500001
MODEL_VOCAB_ID = 1622500011
MODEL_GRAMMAR_ID = 1622500012
MODEL_SENTENCE_ID = 1622500013

DECK_NAME = "JLPT N3"

# --- Shared styling -----------------------------------------------------------
# One stylesheet shared by every note type for a consistent look. Tuned for
# Japanese readability and friendly to Anki's automatic night mode.
CSS = """
.card {
  font-family: "Hiragino Mincho ProN", "Yu Mincho", "Noto Serif JP", serif;
  font-size: 22px;
  line-height: 1.7;
  color: #1a1a1a;
  background: #fbfbf9;
  text-align: center;
  padding: 22px 18px;
}
.nightMode.card { color: #e8e8e8; background: #1f1f22; }

/* The prompt word / sentence */
.headword { font-size: 40px; font-weight: 600; margin: 6px 0 2px; }
.sentence { font-size: 27px; line-height: 1.9; margin: 8px 0; text-align: left; }
.reading  { font-size: 21px; color: #2b6cb0; margin: 2px 0; }
.nightMode .reading { color: #7fb0e0; }
.pos { font-size: 15px; color: #888; letter-spacing: .05em; }

/* Meaning / translation blocks */
.meaning   { font-size: 24px; font-weight: 600; margin: 10px 0; }
.translation { font-size: 19px; color: #444; text-align: left; margin: 6px 0; }
.nightMode .translation { color: #bbb; }

/* Japanese-first explanation (always visible on the back) */
.explain-jp {
  font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", "Noto Sans JP", sans-serif;
  font-size: 18px; line-height: 1.8; text-align: left;
  margin: 12px 0; padding: 12px 14px;
  background: #f0f4ef; border-radius: 10px;
}
.nightMode .explain-jp { background: #26282b; }

/* Click-to-reveal English */
details.en {
  text-align: left; margin: 10px 0; font-family: sans-serif; font-size: 17px;
}
details.en > summary {
  cursor: pointer; color: #2b6cb0; font-weight: 600; list-style: none;
  padding: 6px 0; user-select: none;
}
details.en > summary::before { content: "▸ "; }
details.en[open] > summary::before { content: "▾ "; }
.nightMode details.en > summary { color: #7fb0e0; }
.en-body {
  margin-top: 6px; padding: 10px 14px; line-height: 1.7;
  background: #eef2f8; border-radius: 10px; color: #333;
}
.nightMode .en-body { background: #24262b; color: #ddd; }

/* Word-by-word breakdown table for sentence cards */
.breakdown { text-align: left; margin: 10px auto; border-collapse: collapse; }
.breakdown td { padding: 5px 10px; vertical-align: top; font-size: 17px; }
.breakdown td.part { font-weight: 600; white-space: nowrap; }
.breakdown tr { border-bottom: 1px solid #e3e3e0; }
.nightMode .breakdown tr { border-bottom: 1px solid #34363a; }

/* Furigana sizing */
ruby rt { font-size: .55em; color: #666; }
.nightMode ruby rt { color: #9a9a9a; }

hr#answer { border: none; border-top: 2px solid #d9d9d4; margin: 16px 0; }
.nightMode hr#answer { border-top-color: #3a3c40; }

.source { font-size: 13px; color: #aaa; margin-top: 14px; }
.tag { font-size: 13px; color: #b0883a; letter-spacing: .04em; }
"""


# --- Note type: Vocabulary ----------------------------------------------------
# Produces TWO cards: Recognition (JP -> meaning) and Production (meaning -> JP).
VOCAB_MODEL = genanki.Model(
    MODEL_VOCAB_ID,
    "JLPT N3 Vocab (recog+prod)",
    fields=[
        {"name": "Word"},        # furigana notation, e.g.  事務所[じむしょ]
        {"name": "Reading"},     # kana only, e.g. じむしょ
        {"name": "Meaning"},     # English meaning (concise)
        {"name": "PartOfSpeech"},# e.g. noun / godan verb / な-adjective
        {"name": "ExplainJP"},   # short Japanese gloss / nuance
        {"name": "ExplainEN"},   # English nuance (revealed on click)
        {"name": "ExampleJP"},   # example sentence, furigana notation
        {"name": "ExampleEN"},   # example translation
        {"name": "Source"},      # e.g. N3 Choukai 1番
    ],
    templates=[
        {
            "name": "Recognition (JP→EN)",
            "qfmt": """
<div class="headword">{{furigana:Word}}</div>
<div class="pos">{{PartOfSpeech}}</div>
""",
            "afmt": """
{{FrontSide}}
<hr id="answer">
<div class="reading">{{Reading}}</div>
<div class="meaning">{{Meaning}}</div>
{{#ExplainJP}}<div class="explain-jp">{{ExplainJP}}</div>{{/ExplainJP}}
{{#ExampleJP}}<div class="sentence">{{furigana:ExampleJP}}</div>{{/ExampleJP}}
{{#ExampleEN}}<div class="translation">{{ExampleEN}}</div>{{/ExampleEN}}
{{#ExplainEN}}<details class="en"><summary>英語の説明を見る</summary>
<div class="en-body">{{ExplainEN}}</div></details>{{/ExplainEN}}
{{#Source}}<div class="source">{{Source}}</div>{{/Source}}
""",
        },
        {
            "name": "Production (EN→JP)",
            "qfmt": """
<div class="meaning">{{Meaning}}</div>
<div class="pos">{{PartOfSpeech}}</div>
""",
            "afmt": """
{{FrontSide}}
<hr id="answer">
<div class="headword">{{furigana:Word}}</div>
<div class="reading">{{Reading}}</div>
{{#ExplainJP}}<div class="explain-jp">{{ExplainJP}}</div>{{/ExplainJP}}
{{#ExampleJP}}<div class="sentence">{{furigana:ExampleJP}}</div>{{/ExampleJP}}
{{#ExampleEN}}<div class="translation">{{ExampleEN}}</div>{{/ExampleEN}}
{{#ExplainEN}}<details class="en"><summary>英語の説明を見る</summary>
<div class="en-body">{{ExplainEN}}</div></details>{{/ExplainEN}}
{{#Source}}<div class="source">{{Source}}</div>{{/Source}}
""",
        },
    ],
    css=CSS,
)


# --- Note type: Grammar / expression ------------------------------------------
# Single card. Front = the point + a triggering question; back = JP-first
# explanation, examples, and click-to-reveal English.
GRAMMAR_MODEL = genanki.Model(
    MODEL_GRAMMAR_ID,
    "JLPT N3 Grammar/Expression",
    fields=[
        {"name": "Point"},       # e.g. 〜ておく / 〜とく
        {"name": "Question"},    # prompt shown on front, e.g. "意味と使い方は?"
        {"name": "Structure"},   # formation, e.g. Vて + おく
        {"name": "ExplainJP"},   # Japanese explanation
        {"name": "ExplainEN"},   # English explanation (revealed on click)
        {"name": "Examples"},    # HTML; one or more example sentences + translations
        {"name": "Source"},
    ],
    templates=[
        {
            "name": "Grammar",
            "qfmt": """
<div class="headword">{{furigana:Point}}</div>
<div class="pos">{{Question}}</div>
""",
            "afmt": """
{{FrontSide}}
<hr id="answer">
{{#Structure}}<div class="reading">{{furigana:Structure}}</div>{{/Structure}}
{{#ExplainJP}}<div class="explain-jp">{{ExplainJP}}</div>{{/ExplainJP}}
{{#Examples}}<div class="sentence">{{furigana:Examples}}</div>{{/Examples}}
{{#ExplainEN}}<details class="en"><summary>英語の説明を見る</summary>
<div class="en-body">{{ExplainEN}}</div></details>{{/ExplainEN}}
{{#Source}}<div class="source">{{Source}}</div>{{/Source}}
""",
        },
    ],
    css=CSS,
)


# --- Note type: Sentence breakdown --------------------------------------------
# Front = full Japanese sentence + "意味は?/ 分解して". Back = translation,
# word-by-word breakdown, JP notes, click-to-reveal English notes.
SENTENCE_MODEL = genanki.Model(
    MODEL_SENTENCE_ID,
    "JLPT N3 Sentence Breakdown",
    fields=[
        {"name": "Sentence"},     # full sentence, furigana notation
        {"name": "Translation"},  # English translation
        {"name": "Breakdown"},    # HTML, word-by-word (use .breakdown table)
        {"name": "ExplainJP"},    # Japanese grammar notes
        {"name": "ExplainEN"},    # English notes (revealed on click)
        {"name": "Source"},
    ],
    templates=[
        {
            "name": "Breakdown",
            "qfmt": """
<div class="sentence">{{furigana:Sentence}}</div>
<div class="pos">意味と文法を確認</div>
""",
            "afmt": """
<div class="sentence">{{furigana:Sentence}}</div>
<hr id="answer">
<div class="translation">{{Translation}}</div>
{{#Breakdown}}{{furigana:Breakdown}}{{/Breakdown}}
{{#ExplainJP}}<div class="explain-jp">{{ExplainJP}}</div>{{/ExplainJP}}
{{#ExplainEN}}<details class="en"><summary>英語の説明を見る</summary>
<div class="en-body">{{ExplainEN}}</div></details>{{/ExplainEN}}
{{#Source}}<div class="source">{{Source}}</div>{{/Source}}
""",
        },
    ],
    css=CSS,
)
