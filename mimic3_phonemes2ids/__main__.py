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
import itertools
import json
import logging
import sys
from typing import List


_LOGGER = logging.getLogger(__package__)

PAD = 0
BOS = 1
EOS = 2


def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--id-map", required=True, help="JSON object from phonemes to ids",
    )
    args = parser.parse_args()
    _LOGGER.debug(args)

    args.id_map = json.loads(args.id_map)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        # { "phonemes": ["p1", "p2", ...]  }
        utterance = json.loads(line)
        phonemes = utterance.get("phonemes", [])

        ids: List[int] = [BOS]
        for phoneme in phonemes:
            ids.extend(args.id_map.get(phoneme, []))

        # Intersperse pad
        ids = list(
            itertools.chain.from_iterable(
                itertools.zip_longest(ids, itertools.repeat(PAD, len(ids)))
            )
        )
        ids.append(EOS)

        utterance["phoneme_ids"] = ids
        json.dump(utterance, sys.stdout, ensure_ascii=False)
        print("", flush=True)


# -----------------------------------------------------------------------------


if __name__ == "__main__":
    main()
