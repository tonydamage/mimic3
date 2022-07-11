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
from typing import Dict, List, Optional, Set

_LOGGER = logging.getLogger(__package__)

PAD = "_"
BOS = "^"
EOS = "$"


def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--map",
        action="append",
        default=[],
        nargs=2,
        metavar=("from", "to"),
        help="Map phonemes to ids",
    )
    args = parser.parse_args()
    _LOGGER.debug(args)

    id_map: Dict[str, List[int]] = {}

    # Allocate meta phonemes
    next_id = allocate_phoneme(id_map, PAD)
    next_id = allocate_phoneme(id_map, BOS, next_id)
    next_id = allocate_phoneme(id_map, EOS, next_id)

    all_phonemes: Set[str] = set()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        # { "phonemes": ["p1", "p2", ...]  }
        utterance = json.loads(line)
        phonemes = utterance.get("phonemes", [])
        all_phonemes.update(phonemes)

    # Learn mapping
    for phoneme in sorted(all_phonemes):
        next_id = allocate_phoneme(id_map, phoneme, next_id)

    json.dump(id_map, sys.stdout, ensure_ascii=False)
    print("", flush=True)


# -----------------------------------------------------------------------------


def allocate_phoneme(
    id_map: Dict[str, List[int]], phoneme: str, next_id: Optional[int] = None,
) -> int:
    if next_id is None:
        if id_map:
            next_id = max(id for ids in id_map.values() for id in ids) + 1
        else:
            next_id = 0

    if phoneme not in id_map:
        id_map[phoneme] = [next_id]
        next_id += 1

    return next_id


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
