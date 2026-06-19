#!/usr/bin/env python3
"""
Build the JLPT N3 .apkg from card data files.

Usage
-----
    .venv/bin/python anki/build.py                 # build from all anki/cards/*.json
    .venv/bin/python anki/build.py --no-copy       # don't copy to Windows Downloads

Card data
---------
Each file in ``anki/cards/`` is JSON: a list of card objects. Every object has
a ``type`` ("vocab" | "grammar" | "sentence") and an ``id`` (a short stable
string, unique across ALL files). The ``id`` becomes the Anki GUID, so editing a
card's content updates the existing card on re-import instead of duplicating it.
Remaining keys map to that note type's fields (see anki/models.py).

The output .apkg only ADDS to / updates the existing "JLPT N3" deck on import.
Importing an .apkg never deletes cards, so the existing deck is safe.
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


def build():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-copy", action="store_true",
                        help="do not copy the .apkg to the Windows Downloads folder")
    args = parser.parse_args()

    deck = genanki.Deck(models.DECK_ID, models.DECK_NAME)
    files = sorted(glob.glob(os.path.join(CARDS_DIR, "*.json")))
    if not files:
        print(f"No card files found in {CARDS_DIR} — nothing to build yet.")
        return

    seen_ids = set()
    count = 0
    for path in files:
        with open(path, encoding="utf-8") as fh:
            cards = json.load(fh)
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
            note = GuidNote(model=model, fields=fields, tags=tags, stable_id=cid)
            deck.add_note(note)
            count += 1

    os.makedirs(DIST_DIR, exist_ok=True)
    out_path = os.path.join(DIST_DIR, OUTPUT_NAME)
    genanki.Package(deck).write_to_file(out_path)
    print(f"Built {count} notes -> {out_path}")

    if not args.no_copy and os.path.isdir(WIN_DOWNLOADS):
        dest = os.path.join(WIN_DOWNLOADS, OUTPUT_NAME)
        shutil.copy2(out_path, dest)
        print(f"Copied to {dest}  (double-click in Windows to import)")


if __name__ == "__main__":
    build()
