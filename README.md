# BOREALIS Data Parser

A Python tool for parsing base64-encoded acoustic data from BOREALIS devices into human-readable CSV format.

## Overview

This tool processes base64-encoded acoustic spectra and statistical data from BOREALIS underwater acoustic monitoring devices. It decodes the binary data and outputs structured CSV data with frequency bands and corresponding sound pressure levels (SPL) in dB re µPa².

More technical details about BOREALIS can be found in AOS's github organization:

- [BOREALIS Wiki](https://github.com/appliedoceansciences/borealis/wiki)
- [SCARI Wiki](https://github.com/appliedoceansciences/scari/wiki)
- [scari_tools](https://github.com/appliedoceansciences/scari_tools)

## Features

- Parses two types of Borealis acoustic data:
  - **Spectrum data**: RMS SPL measurements per decidecade frequency band at one time point
  - **Statistics data**: Statistical quartiles (Q1, Q2, Q3) and mean per decidecade band over a longer sample period
- Supports ANSI S1.11 nominal midband frequencies (40 Hz to 20 kHz)
- Automatic data type detection based on input length
- CSV output format for easy data analysis
- Takes input from stdin and writes to stdout, enabling scripted usage

## Requirements

- Any recent version of python
- No external dependencies (uses only standard library)

## Usage

### Basic Usage

The tool reads base64-encoded data from stdin and outputs CSV to stdout:

```bash
echo "<base64_string>" | python parse_borealis_data.py
```

### Data Type Detection

The tool automatically detects the data type based on input length:
- Short strings (< 100 characters): Treated as spectrum data
- Longer strings (≥ 100 characters): Treated as statistics data

### Manual Data Type Selection

You can explicitly specify the data type using the `--data-type` argument:

```bash
echo "<base64_string>" | python parse_borealis_data.py --data-type spectrum
echo "<base64_string>" | python parse_borealis_data.py --data-type statistics
```

## Examples

### Spectrum Data Example

Input:
```bash
echo YcurqkquiRqphlqpS5qe15madRmXexmUYMmUaCmRIqmSIbmRUDmRnyiJ | python parse_borealis_data.py
```

Output:
```csv
Frequency,SPL (dB)
40,130.19
50,122.45
63,121.61
80,124.33
100,120.06
125,120.44
160,119.92
200,120.63
250,117.16
315,112.56
400,111.72
500,109.56
630,107.13
800,106.94
1000,107.41
1250,104.69
1600,106.14
2000,105.20
2500,106.52
3150,102.49
4000,103.24
5000,103.61
6300,103.19
8000,102.91
10000,105.39
12500,102.53
16000,97.10
20000,96.49
```

### Statistics Data Example

Input:
```bash
echo oKetrZiiqamUnqallpuiopean5+XmZycmJqcm5qcnp2UlpeWjo+Rj4mLjIuEhoeGgoSFhIOEhYSBgoODgoOEg4OEhYSFhYaGh4eIh4mJiYmKiouLjY2NjY2NjY2Ki4uLioqKiouLjIw= | python parse_borealis_data.py
```

Output:
```csv
Frequency,Q1,Q2,Q3,Mean
40,113.64,118.89,123.39,123.39
50,107.64,115.14,120.39,120.39
63,104.64,112.14,118.14,117.39
80,106.14,109.89,115.14,115.14
100,106.89,109.14,112.89,112.89
125,106.89,108.39,110.64,110.64
160,107.64,109.14,110.64,109.89
200,109.14,110.64,112.14,111.39
250,104.64,106.14,106.89,106.14
315,100.14,100.89,102.39,100.89
400,96.39,97.89,98.64,97.89
500,92.64,94.14,94.89,94.14
630,91.14,92.64,93.39,92.64
800,91.89,92.64,93.39,92.64
1000,90.39,91.14,91.89,91.89
1250,91.14,91.89,92.64,91.89
1600,91.89,92.64,93.39,92.64
2000,93.39,93.39,94.14,94.14
2500,94.89,94.89,95.64,94.89
3150,96.39,96.39,96.39,96.39
4000,97.14,97.14,97.89,97.89
5000,99.39,99.39,99.39,99.39
6300,99.39,99.39,99.39,99.39
8000,97.14,97.89,97.89,97.89
10000,97.14,97.14,97.14,97.14
12500,97.89,97.89,98.64,98.64
```

## Output Format

### Spectrum Data
- **Frequency**: Frequency band in Hz (ANSI S1.11 midband frequencies)
- **SPL (dB)**: Sound pressure level in decibels

### Statistics Data
- **Frequency**: Frequency band in Hz (ANSI S1.11 midband frequencies)
- **Q1**: First quartile (25th percentile) SPL in dB
- **Q2**: Second quartile (median, 50th percentile) SPL in dB
- **Q3**: Third quartile (75th percentile) SPL in dB
- **Mean**: Mean SPL in dB

## Frequency Bands

The tool supports the following ANSI S1.11 standard nominal midband frequencies:
40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000 Hz

## Technical Details

- **Data Encoding**: 12-bit precision for spectrum data, 8-bit for statistics
- **Dynamic Range**: 192 dB

## Command Line Options

```
usage: parse_borealis_data.py [-h] [--data-type {spectrum,statistics}]

Parse Borealis base64 encoded acoustic data from stdin.

optional arguments:
  -h, --help            show this help message and exit
  --data-type {spectrum,statistics}
                        type of data to parse. If not provided, it will be
                        inferred from the length of the input line.
```

## Error Handling

- Invalid base64 input will be silently ignored (returns None)
- Malformed data will not produce output
- The tool continues processing multiple lines even if some fail

## Integration

The tool is designed to work well in Unix pipelines and can be easily integrated into data processing workflows:

```bash
# Process multiple lines from a file
cat data.txt | python parse_borealis_data.py > output.csv

# Combine with other tools
echo "base64_data" | python parse_borealis_data.py | head -10
```