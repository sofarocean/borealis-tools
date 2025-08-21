import argparse
import base64
import csv
import sys
from typing import List, Optional

ANSI_S1_11_MIDBAND_FREQUENCIES: List[int] = [
    40,
    50,
    63,
    80,
    100,
    125,
    160,
    200,
    250,
    315,
    400,
    500,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3150,
    4000,
    5000,
    6300,
    8000,
    10000,
    12500,
    16000,
    20000,
]

MIN_BOREALIS_SPL_DB: float = -192 + 185.642


def unpack_nibble(bytes: bytes, inibble_abs: int) -> int:
    ibyte: int = inibble_abs // 2
    inibble: int = inibble_abs % 2
    return (int)(bytes[ibyte] >> (4 * inibble)) & 0xF


def unpack_three_nibbles(bytes: bytes, inibble_abs: int) -> int:
    return (
        unpack_nibble(bytes, inibble_abs + 0) << 0
        | unpack_nibble(bytes, inibble_abs + 1) << 4
        | unpack_nibble(bytes, inibble_abs + 2) << 8
    )


def calc_db_step_for_bits(bits_per_datum: int) -> float:
    data_range: int = 2**bits_per_datum
    return 192 / data_range


def parse_borealis_spectrum(base64_string: str) -> Optional[List[float]]:
    try:
        raw_bytes = base64.b64decode(base64_string)
    except:
        return None

    cstep: float = calc_db_step_for_bits(12)

    # number of decidecade bands
    D: int = (len(raw_bytes) * 2) // 3

    # extract number between 0 and 4095 inclusive from packed bytes, scale and shift
    spls_dB = [
        unpack_three_nibbles(raw_bytes, 3 * id) * cstep + MIN_BOREALIS_SPL_DB
        for id in range(D)
    ]
    return spls_dB


def parse_borealis_levels_stats(base64_string: str) -> Optional[List[List[float]]]:
    try:
        raw_bytes: bytes = base64.b64decode(base64_string)
    except:
        return None

    cstep: float = calc_db_step_for_bits(8)

    # number of stats (3 quartiles and mean)
    K: int = 4

    # number of decidecade bands
    D: int = len(raw_bytes) // K

    # extract single byte values, scale and shift
    tmp: List[float] = [
        raw_bytes[id] * cstep + MIN_BOREALIS_SPL_DB for id in range(D * K)
    ]

    # reshape into length-D list of length-K lists
    reshaped: List[List[float]] = [tmp[i : (i + K)] for i in range(0, K * D, K)]
    return reshaped


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse Borealis base64 encoded acoustic data from stdin."
    )
    parser.add_argument(
        "--data-type",
        choices=["spectrum", "statistics"],
        help="type of data to parse. If not provided, it will be inferred from the length of the input line.",
    )
    args = parser.parse_args()

    writer = csv.writer(sys.stdout)
    for line in sys.stdin:
        line = line.rstrip()

        data_type = args.data_type
        if data_type is None:
            if len(line) < 100:
                data_type = "spectrum"
            else:
                data_type = "statistics"

        if data_type == "statistics":
            result = parse_borealis_levels_stats(line)
            if result is not None:
                writer.writerow(["Frequency", "Q1", "Q2", "Q3", "Mean"])
                # Add frequency as first column and format each float to 2 decimal places
                for i, row in enumerate(result):
                    frequency = (
                        ANSI_S1_11_MIDBAND_FREQUENCIES[i]
                        if i < len(ANSI_S1_11_MIDBAND_FREQUENCIES)
                        else "Unknown"
                    )
                    formatted_row = [frequency] + [f"{value:.2f}" for value in row]
                    writer.writerow(formatted_row)
        elif data_type == "spectrum":
            result = parse_borealis_spectrum(line)
            if result is not None:
                writer.writerow(["Frequency", "SPL (dB)"])
                for i, spl in enumerate(result):
                    frequency = (
                        ANSI_S1_11_MIDBAND_FREQUENCIES[i]
                        if i < len(ANSI_S1_11_MIDBAND_FREQUENCIES)
                        else "Unknown"
                    )
                    writer.writerow([frequency, f"{spl:.2f}"])
