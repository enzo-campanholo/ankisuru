#!/usr/bin/env python3
"""
Build the JLPT .apkg from card data files.

Usage
-----
    .venv/bin/python anki/build.py                 # build from all anki/cards/**/*.json
    .venv/bin/python anki/build.py --no-copy       # don't copy to Windows Downloads

Card data
---------
Each ``*.json`` file under ``anki/cards/`` (any subfolder) holds the cards for
one batch. A file is EITHER:

  * a JSON array of card objects        -> they go to the default deck "JLPT N3", or
  * a JSON object ``{"deck": "...", "cards": [ ... ]}`` -> they go to that deck.

Use the object form to route a source to its own deck or subdeck, e.g.
``"deck": "JLPT N3::N3 Choukai Script"`` (``::`` makes an Anki subdeck) or a
different level like ``"deck": "JLPT N2::Reading 1"``.

Every card object has a ``type`` ("vocab" | "grammar" | "sentence") and an
``id`` (a short stable string, unique across ALL files). The ``id`` becomes the
Anki GUID, so editing a card updates the existing card on re-import instead of
duplicating it. Remaining keys map to that note type's fields (see models.py).

The output .apkg only ADDS to / updates existing decks on import — importing an
.apkg never deletes cards, so existing decks are safe.
"""

import argparse
import glob
import json
import os
import shutil
import sys

import genanki

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.join(HERE, "cards")
DIST_DIR = os.path.join(HERE, "dist")
WIN_DOWNLOADS = "/mnt/c/Users/isolino/Downloads"
OUTPUT_NAME = "JLPT_N3.apkg"

# type -> (model, ordered field names)
TYPES = {
    "vocab": (models.VOCAB_MODEL,
              ["Word", "Reading", "Meaning", "PartOfSpeech",
               "ExplainJP", "ExplainEN", "ExampleJP", "ExampleEN", "Source"]),
    "grammar": (models.GRAMMAR_MODEL,
                ["Point", "Question", "Structure",
                 "ExplainJP", "ExplainEN", "Examples", "Source"]),
    "sentence": (models.SENTENCE_MODEL,
                 ["Sentence", "Translation", "Breakdown",
                  "ExplainJP", "ExplainEN", "Source"]),
}


class GuidNote(genanki.Note):
    """Note whose GUID is fixed by the data file's stable ``id``."""

    def __init__(self, *args, stable_id, **kwargs):
        super().__init__(*args, **kwargs)
        self._stable_id = stable_id

    @property
    def guid(self):
        return genanki.guid_for(self._stable_id)


def _load(path):
    """Return (deck_name, cards) for a card file (array or object form)."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        return data.get("deck", models.DEFAULT_DECK), data.get("cards", [])
    return models.DEFAULT_DECK, data


def build():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-copy", action="store_true",
                        help="do not copy the .apkg to the Windows Downloads folder")
    args = parser.parse_args()

    files = sorted(glob.glob(os.path.join(CARDS_DIR, "**", "*.json"), recursive=True))
    if not files:
        print(f"No card files found under {CARDS_DIR} — nothing to build yet.")
        return

    decks = {}          # deck name -> genanki.Deck
    seen_ids = set()
    per_deck_counts = {}

    def deck_for(name):
        if name not in decks:
            decks[name] = genanki.Deck(models.deck_id_for(name), name)
            per_deck_counts[name] = 0
        return decks[name]

    for path in files:
        deck_name, cards = _load(path)
        deck = deck_for(deck_name)
        for card in cards:
            ctype = card.get("type")
            cid = card.get("id")
            if ctype not in TYPES:
                raise ValueError(f"{path}: unknown card type {ctype!r}")
            if not cid:
                raise ValueError(f"{path}: a {ctype} card is missing 'id'")
            if cid in seen_ids:
                raise ValueError(f"duplicate card id {cid!r} (must be unique)")
            seen_ids.add(cid)

            model, field_names = TYPES[ctype]
            fields = [card.get(name, "") for name in field_names]
            tags = card.get("tags", [])
            deck.add_note(GuidNote(model=model, fields=fields, tags=tags, stable_id=cid))
            per_deck_counts[deck_name] += 1

    os.makedirs(DIST_DIR, exist_ok=True)
    out_path = os.path.join(DIST_DIR, OUTPUT_NAME)
    genanki.Package(list(decks.values())).write_to_file(out_path)

    total = sum(per_deck_counts.values())
    print(f"Built {total} notes across {len(decks)} deck(s) -> {out_path}")
    for name in sorted(per_deck_counts):
        print(f"  • {name}: {per_deck_counts[name]}")

    if not args.no_copy and os.path.isdir(WIN_DOWNLOADS):
        dest = os.path.join(WIN_DOWNLOADS, OUTPUT_NAME)
        shutil.copy2(out_path, dest)
        print(f"Copied to {dest}  (double-click in Windows to import)")


if __name__ == "__main__":
    build()
