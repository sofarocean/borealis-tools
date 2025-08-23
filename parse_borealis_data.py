#!/usr/bin/env python3
import argparse
import base64
import csv
import math
import sys
from typing import List, Optional


def calculate_ansi_midband_frequency(band_index: int) -> float:
    """Calculate ANSI S1.11 midband frequency from band index.

    Args:
        band_index: Zero-based index (0 corresponds to band 16)

    Returns:
        Frequency in Hz using formula 10^((band_index + 16)/10)
    """
    band_number = band_index + 16
    return 10 ** (band_number / 10)


# The 185.642 constant is specific to the first version of Borealis and may change in future hardware revisions
MIN_BOREALIS_SPL_DB: float = -192 + 185.642


def calculate_pgram_frequencies(df: float, bands_per_octave: int = 24) -> List[float]:
    """Calculate frequency bins for pgram data using hybrid linear/log spacing."""
    # Calculate transition point: N = ceil(bands_per_octave / log(2))
    N = math.ceil(bands_per_octave / math.log(2))

    # Linear bins (excluding first two DC bins): frequencies 2*df, 3*df, ..., (N-1)*df
    linear_freqs = [i * df for i in range(2, N)]

    # Log-spaced bins start at N*df
    log_freqs = []
    f_start = N * df

    # Generate log-spaced frequencies with 24 bands per octave
    # Each octave multiplies frequency by 2, so each band multiplies by 2^(1/24)
    factor = 2 ** (1 / bands_per_octave)
    f = f_start

    # Generate log frequencies up to reasonable acoustic range (e.g., 20 kHz)
    while f <= 20000 and len(log_freqs) < 200:  # Reasonable upper limits
        log_freqs.append(f)
        f *= factor

    return linear_freqs + log_freqs


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


def parse_borealis_pgram(base64_string: str, df: float) -> Optional[List[float]]:
    """Parse pgram (spectrogram) data with hybrid linear/log frequency spacing."""
    try:
        raw_bytes = base64.b64decode(base64_string)
    except:
        return None

    cstep: float = calc_db_step_for_bits(8)  # 0.75 dB steps

    # Extract single byte values, scale and shift
    spls_dB = [
        raw_bytes[i] * cstep + MIN_BOREALIS_SPL_DB for i in range(len(raw_bytes))
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
        choices=["spectrum", "statistics", "pgram"],
        help="type of data to parse. If not provided, it will be inferred from the length of the input line.",
    )
    parser.add_argument(
        "--df",
        type=float,
        default=7.629,
        help="frequency bin spacing in Hz for pgram data (default: 7.629, assumes 31250 Hz sample rate)",
    )
    args = parser.parse_args()

    writer = csv.writer(sys.stdout)
    for line in sys.stdin:
        line = line.rstrip()

        data_type = args.data_type
        if data_type is None:
            if len(line) < 100:
                data_type = "spectrum"
            elif len(line) < 200:
                data_type = "statistics"
            else:
                data_type = "pgram"

        if data_type == "statistics":
            result = parse_borealis_levels_stats(line)
            if result is not None:
                writer.writerow(["Frequency", "Q1", "Q2", "Q3", "Mean"])
                # Add frequency as first column and format each float to 2 decimal places
                for i, row in enumerate(result):
                    frequency = f"{calculate_ansi_midband_frequency(i):.2f}"
                    formatted_row = [frequency] + [f"{value:.2f}" for value in row]
                    writer.writerow(formatted_row)
        elif data_type == "spectrum":
            result = parse_borealis_spectrum(line)
            if result is not None:
                writer.writerow(["Frequency", "SPL (dB)"])
                for i, spl in enumerate(result):
                    frequency = f"{calculate_ansi_midband_frequency(i):.2f}"
                    writer.writerow([frequency, f"{spl:.2f}"])
        elif data_type == "pgram":
            result = parse_borealis_pgram(line, args.df)
            if result is not None:
                frequencies = calculate_pgram_frequencies(args.df)

                # Print assumption message to stderr if using default df
                if args.df == 7.629:
                    print(
                        "# Assuming default sample rate (31250 Hz) and df (7.629 Hz)",
                        file=sys.stderr,
                    )

                writer.writerow(["Frequency", "SPL (dB)"])
                for i, spl in enumerate(result):
                    if i < len(frequencies):
                        frequency = f"{frequencies[i]:.2f}"
                    else:
                        frequency = "Unknown"
                    writer.writerow([frequency, f"{spl:.2f}"])
