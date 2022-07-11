# Copyright 2022 Mycroft AI Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import argparse
import json
import logging
import sys
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Tuple

import espeak_phonemizer

_LOGGER = logging.getLogger(__package__)


def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phonemizer",
        choices=["espeak", "characters"],
        required=True,
        help="Phonemizer to use",
    )
    parser.add_argument("--espeak-voice", help="Voice to use for eSpeak phonemizer")
    parser.add_argument(
        "--characters", help="JSON list of valid characters for characters phonemizer"
    )
    parser.add_argument(
        "--character-casing",
        choices=["keep", "lower", "upper"],
        default="keep",
        help="Apply case transformation",
    )
    parser.add_argument(
        "--map",
        action="append",
        default=[],
        nargs=2,
        metavar=("from", "to"),
        help="Map phonemes",
    )
    args = parser.parse_args()
    _LOGGER.debug(args)

    if args.phonemizer == "espeak":
        assert args.espeak_voice, "--espeak-voice is required"
    elif args.phonemizer == "characters":
        assert args.characters, "--characters is required"
        args.characters = set(json.loads(args.characters))

    normalized_map = normalize_map(args.map)
    if normalized_map:
        _LOGGER.debug("Map: %s", normalized_map)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        # { "text": "..."  }
        utterance = json.loads(line)

        if args.phonemizer == "espeak":
            phonemes = phonemize_espeak(utterance, args)
        elif args.phonemizer == "characters":
            phonemes = phonemize_characters(utterance, args)
        else:
            raise ValueError(args.phonemizer)

        phonemes = map_phonemes(phonemes, normalized_map)
        utterance["phonemes"] = phonemes
        json.dump(utterance, sys.stdout, ensure_ascii=False)
        print("", flush=True)


# -----------------------------------------------------------------------------

_ESPEAK_PHONEMIZER: Optional[espeak_phonemizer.Phonemizer] = None


def phonemize_espeak(utterance: Dict[str, Any], args: argparse.Namespace) -> List[str]:
    global _ESPEAK_PHONEMIZER

    text = utterance["text"]
    voice = utterance.get("espeak", {}).get("voice", args.espeak_voice)

    if _ESPEAK_PHONEMIZER is None:
        _ESPEAK_PHONEMIZER = espeak_phonemizer.Phonemizer()

    phonemes_str = _ESPEAK_PHONEMIZER.phonemize(
        text=text, voice=voice, keep_clause_breakers=True
    )
    codepoints = list(unicodedata.normalize("NFD", phonemes_str))
    return codepoints


def phonemize_characters(
    utterance: Dict[str, Any], args: argparse.Namespace
) -> List[str]:
    text = utterance["text"]
    if args.character_casing == "lower":
        text = text.lower()
    elif args.character_casing == "upper":
        text = text.upper()

    codepoints = list(unicodedata.normalize("NFD", text))
    return [c for c in codepoints if c in args.characters]


# -----------------------------------------------------------------------------


def normalize_map(
    phoneme_map: Iterable[Tuple[str, str]]
) -> List[Tuple[List[str], List[str]]]:
    normalized_map: List[Tuple[List[str], List[str]]] = []
    for map_from, map_to in phoneme_map:
        if map_from[0] == "[":
            # List
            map_from_list = json.loads(map_from)
        else:
            # String
            map_from_list = [map_from]

        if map_to[0] == "[":
            # List
            map_to_list = json.loads(map_to)
        else:
            # String
            map_to_list = [map_to]

        normalized_map.append((map_from_list, map_to_list))

    # Sort by "from" length, descending
    normalized_map = sorted(
        normalized_map, key=lambda from_to: len(from_to[0]), reverse=True
    )

    return normalized_map


def map_phonemes(
    phonemes: List[str], normalized_map: List[Tuple[List[str], List[str]]]
) -> List[str]:
    for map_from, map_to in normalized_map:
        if len(map_from) > len(phonemes):
            continue

        has_changes = True
        while has_changes:
            has_changes = False
            for start_idx in range(len(phonemes) - len(map_from)):
                end_idx = start_idx + len(map_from)
                if phonemes[start_idx:end_idx] == map_from:
                    phonemes = phonemes[:start_idx] + map_to + phonemes[end_idx:]
                    has_changes = True
                    break

    return phonemes


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
