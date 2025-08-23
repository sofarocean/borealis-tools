#!/usr/bin/env python3
"""
Test suite for parse_borealis_data.py using example data from README.

Uses only built-in Python modules for testing.
"""

import unittest
import sys
import io
from unittest.mock import patch
import parse_borealis_data
import test_fixtures


class TestParseBorealisData(unittest.TestCase):
    """Test cases for Borealis data parsing functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Get fixtures from test_fixtures module
        self.fixtures = test_fixtures.get_all_fixtures()

        # Keep original single examples for backward compatibility
        self.spectrum_input = self.fixtures["spectrum"][0]["base64"]
        self.statistics_input = self.fixtures["statistics"][0]["base64"]
        self.pgram_input = self.fixtures["pgram"][0]["base64"]

    def test_spectrum_parsing(self):
        """Test spectrum data parsing."""
        result = parse_borealis_data.parse_borealis_spectrum(self.spectrum_input)
        self.assertIsNotNone(result)

        if result is not None:
            self.assertIsInstance(result, list)

            # Test some specific expected values from README
            self.assertAlmostEqual(result[0], 130.19, places=1)  # ~39.81 Hz
            self.assertAlmostEqual(result[1], 122.45, places=1)  # ~50.12 Hz
            self.assertAlmostEqual(result[-1], 96.49, places=1)  # ~19952.62 Hz

    def test_statistics_parsing(self):
        """Test statistics data parsing."""
        result = parse_borealis_data.parse_borealis_levels_stats(self.statistics_input)
        self.assertIsNotNone(result)

        if result is not None:
            self.assertIsInstance(result, list)

            # Each entry should be a list of 4 values (Q1, Q2, Q3, Mean)
            for row in result:
                self.assertIsInstance(row, list)
                self.assertEqual(len(row), 4)

            # Test some specific expected values from README
            self.assertAlmostEqual(result[0][0], 113.64, places=1)  # 40 Hz Q1
            self.assertAlmostEqual(result[0][1], 118.89, places=1)  # 40 Hz Q2
            self.assertAlmostEqual(result[0][2], 123.39, places=1)  # 40 Hz Q3
            self.assertAlmostEqual(result[0][3], 123.39, places=1)  # 40 Hz Mean

    def test_pgram_parsing(self):
        """Test pgram data parsing."""
        df = 7.629  # Default df value
        result = parse_borealis_data.parse_borealis_pgram(self.pgram_input, df)
        self.assertIsNotNone(result)

        if result is not None:
            self.assertIsInstance(result, list)

            # Test that we get a reasonable number of frequency bins
            self.assertGreater(len(result), 100)  # Should have many bins

            # Test some specific expected values from README
            self.assertAlmostEqual(result[0], 96.39, places=1)
            self.assertAlmostEqual(result[1], 92.64, places=1)
            self.assertAlmostEqual(result[2], 88.89, places=1)

    def test_pgram_frequency_calculation(self):
        """Test pgram frequency calculation."""
        df = 7.629
        frequencies = parse_borealis_data.calculate_pgram_frequencies(df)

        self.assertIsInstance(frequencies, list)
        self.assertGreater(len(frequencies), 100)

        # Test that frequencies are increasing
        for i in range(1, len(frequencies)):
            self.assertGreater(frequencies[i], frequencies[i - 1])

        # Test linear portion (first few frequencies)
        self.assertAlmostEqual(frequencies[0], 2 * df, places=2)  # 2*df
        self.assertAlmostEqual(frequencies[1], 3 * df, places=2)  # 3*df

        # Test that linear portion ends around N-1 where N = ceil(24/ln(2))
        import math

        N = math.ceil(24 / math.log(2))
        linear_count = N - 2  # Excluding first two DC bins

        # Check transition point
        self.assertAlmostEqual(frequencies[linear_count - 1], (N - 1) * df, places=2)

    def test_data_type_detection(self):
        """Test automatic data type detection based on input length."""
        # Test spectrum detection (short string)
        self.assertLess(len(self.spectrum_input), 100)

        # Test statistics detection (medium string)
        self.assertGreaterEqual(len(self.statistics_input), 100)
        self.assertLess(len(self.statistics_input), 200)

        # Test pgram detection (long string)
        self.assertGreaterEqual(len(self.pgram_input), 200)

    def test_invalid_base64_handling(self):
        """Test handling of invalid base64 input."""
        invalid_input = "invalid_base64_string!"

        result_spectrum = parse_borealis_data.parse_borealis_spectrum(invalid_input)
        self.assertIsNone(result_spectrum)

        result_stats = parse_borealis_data.parse_borealis_levels_stats(invalid_input)
        self.assertIsNone(result_stats)

        result_pgram = parse_borealis_data.parse_borealis_pgram(invalid_input, 7.629)
        self.assertIsNone(result_pgram)

    def test_calc_db_step_for_bits(self):
        """Test dB step calculation for different bit depths."""
        # Test 8-bit (used for statistics and pgram)
        step_8bit = parse_borealis_data.calc_db_step_for_bits(8)
        self.assertAlmostEqual(step_8bit, 0.75, places=3)

        # Test 12-bit (used for spectrum)
        step_12bit = parse_borealis_data.calc_db_step_for_bits(12)
        self.assertAlmostEqual(step_12bit, 192 / (2**12), places=3)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_main_spectrum_output(self, mock_stderr, mock_stdout):
        """Test main function output for spectrum data."""
        test_input = self.spectrum_input + "\n"

        # Test the parsing logic directly since there's no main function
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        line = test_input.strip()
        data_type = (
            "spectrum"
            if len(line) < 100
            else ("statistics" if len(line) < 200 else "pgram")
        )

        if data_type == "spectrum":
            result = parse_borealis_data.parse_borealis_spectrum(line)
            if result is not None:
                writer.writerow(["Frequency", "SPL (dB)"])
                for i, spl in enumerate(result):
                    frequency = (
                        f"{parse_borealis_data.calculate_ansi_midband_frequency(i):.2f}"
                    )
                    writer.writerow([frequency, f"{spl:.2f}"])

        output_str = output.getvalue()
        self.assertIn("Frequency,SPL (dB)", output_str)
        self.assertIn("39.81,130.19", output_str)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_main_statistics_output(self, mock_stderr, mock_stdout):
        """Test main function output for statistics data."""
        test_input = self.statistics_input + "\n"

        # Simulate the main logic for statistics
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        line = test_input.strip()
        data_type = (
            "spectrum"
            if len(line) < 100
            else ("statistics" if len(line) < 200 else "pgram")
        )

        if data_type == "statistics":
            result = parse_borealis_data.parse_borealis_levels_stats(line)
            if result is not None:
                writer.writerow(["Frequency", "Q1", "Q2", "Q3", "Mean"])
                for i, row in enumerate(result):
                    frequency = (
                        f"{parse_borealis_data.calculate_ansi_midband_frequency(i):.2f}"
                    )
                    formatted_row = [frequency] + [f"{value:.2f}" for value in row]
                    writer.writerow(formatted_row)

        output_str = output.getvalue()
        self.assertIn("Frequency,Q1,Q2,Q3,Mean", output_str)
        self.assertIn("39.81,113.64,118.89,123.39,123.39", output_str)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_main_pgram_output(self, mock_stderr, mock_stdout):
        """Test main function output for pgram data."""
        test_input = self.pgram_input + "\n"

        # Simulate the main logic for pgram
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        line = test_input.strip()
        data_type = (
            "spectrum"
            if len(line) < 100
            else ("statistics" if len(line) < 200 else "pgram")
        )
        df = 7.629  # Default df

        if data_type == "pgram":
            result = parse_borealis_data.parse_borealis_pgram(line, df)
            if result is not None:
                frequencies = parse_borealis_data.calculate_pgram_frequencies(df)
                writer.writerow(["Frequency", "SPL (dB)"])
                for i, spl in enumerate(result):
                    if i < len(frequencies):
                        frequency = f"{frequencies[i]:.2f}"
                    else:
                        frequency = "Unknown"
                    writer.writerow([frequency, f"{spl:.2f}"])

        output_str = output.getvalue()
        self.assertIn("Frequency,SPL (dB)", output_str)
        self.assertIn("15.26,96.39", output_str)

    def test_ansi_frequency_calculation(self):
        """Test that ANSI frequency calculation is correct."""
        # Test first few frequencies
        self.assertAlmostEqual(
            parse_borealis_data.calculate_ansi_midband_frequency(0), 39.811, places=2
        )  # 10^(16/10)
        self.assertAlmostEqual(
            parse_borealis_data.calculate_ansi_midband_frequency(1), 50.119, places=2
        )  # 10^(17/10)
        self.assertAlmostEqual(
            parse_borealis_data.calculate_ansi_midband_frequency(2), 63.096, places=2
        )  # 10^(18/10)

        # Test some middle frequencies
        self.assertAlmostEqual(
            parse_borealis_data.calculate_ansi_midband_frequency(10), 398.107, places=1
        )  # 10^(26/10)
        self.assertAlmostEqual(
            parse_borealis_data.calculate_ansi_midband_frequency(20), 3981.072, places=0
        )  # 10^(36/10)

        # Test last frequency (index 27 = band 43)
        self.assertAlmostEqual(
            parse_borealis_data.calculate_ansi_midband_frequency(27),
            19952.623,
            places=0,
        )  # 10^(43/10)

    def test_min_borealis_spl_constant(self):
        """Test that MIN_BOREALIS_SPL_DB constant is correct."""
        expected_value = -192 + 185.642
        self.assertAlmostEqual(
            parse_borealis_data.MIN_BOREALIS_SPL_DB, expected_value, places=3
        )

    def test_all_spectrum_fixtures(self):
        """Test all spectrum fixtures."""
        spectrum_fixtures = test_fixtures.get_fixtures_by_type("spectrum")
        self.assertGreater(len(spectrum_fixtures), 0, "No spectrum fixtures found")

        for fixture in spectrum_fixtures:
            with self.subTest(fixture=fixture["name"]):
                result = parse_borealis_data.parse_borealis_spectrum(fixture["base64"])
                self.assertIsNotNone(result, f"Failed to parse {fixture['name']}")

                if result is not None:
                    # Test specific expected samples if provided
                    if "expected_samples" in fixture:
                        for index, expected_frequency, expected_spl in fixture[
                            "expected_samples"
                        ]:
                            # Handle negative indices (e.g., -1 for last element)
                            actual_index = index if index >= 0 else len(result) + index

                            # Check that index is within bounds of the actual result
                            if 0 <= actual_index < len(result):
                                actual_spl = result[actual_index]
                                actual_frequency = parse_borealis_data.calculate_ansi_midband_frequency(
                                    actual_index
                                )

                                # Validate frequency matches expected ANSI frequency (within tolerance)
                                # Use higher tolerance since we changed from hardcoded to calculated values
                                self.assertAlmostEqual(
                                    actual_frequency,
                                    expected_frequency,
                                    delta=expected_frequency * 0.05,  # 5% tolerance
                                    msg=f"Fixture {fixture['name']}: Expected frequency {expected_frequency} at index {index}, got {actual_frequency}",
                                )

                                # Validate SPL value
                                self.assertAlmostEqual(
                                    actual_spl,
                                    expected_spl,
                                    places=1,
                                    msg=f"Fixture {fixture['name']}: Expected {expected_spl} dB at {expected_frequency} Hz (index {index}), got {actual_spl}",
                                )

    def test_all_statistics_fixtures(self):
        """Test all statistics fixtures."""
        statistics_fixtures = test_fixtures.get_fixtures_by_type("statistics")
        self.assertGreater(len(statistics_fixtures), 0, "No statistics fixtures found")

        for fixture in statistics_fixtures:
            with self.subTest(fixture=fixture["name"]):
                result = parse_borealis_data.parse_borealis_levels_stats(
                    fixture["base64"]
                )
                self.assertIsNotNone(result, f"Failed to parse {fixture['name']}")

                if result is not None:
                    # Each entry should be a list of 4 values
                    for row in result:
                        self.assertIsInstance(row, list)
                        self.assertEqual(len(row), 4)

                    # Test specific expected samples if provided
                    if "expected_samples" in fixture:
                        for index, expected_frequency, expected_values in fixture[
                            "expected_samples"
                        ]:
                            # Handle negative indices properly
                            actual_index = index if index >= 0 else len(result) + index

                            # Check that index is within bounds of the actual result
                            if 0 <= actual_index < len(result):
                                actual_values = result[actual_index]
                                actual_frequency = parse_borealis_data.calculate_ansi_midband_frequency(
                                    actual_index
                                )

                                # Validate frequency matches expected frequency (within tolerance)
                                # Use higher tolerance since we changed from hardcoded to calculated values
                                self.assertAlmostEqual(
                                    actual_frequency,
                                    expected_frequency,
                                    delta=expected_frequency * 0.05,  # 5% tolerance
                                    msg=f"Fixture {fixture['name']}: Expected frequency {expected_frequency} at index {index}, got {actual_frequency}",
                                )

                                # Validate statistical values
                                self.assertEqual(len(actual_values), 4)
                                for i, (actual, expected) in enumerate(
                                    zip(actual_values, expected_values)
                                ):
                                    stat_names = ["Q1", "Q2", "Q3", "Mean"]
                                    self.assertAlmostEqual(
                                        actual,
                                        expected,
                                        places=1,
                                        msg=f"Fixture {fixture['name']}: Expected {stat_names[i]}={expected} at {expected_frequency} Hz (index {index}), got {actual}",
                                    )

    def test_all_pgram_fixtures(self):
        """Test all pgram fixtures."""
        pgram_fixtures = test_fixtures.get_fixtures_by_type("pgram")
        self.assertGreater(len(pgram_fixtures), 0, "No pgram fixtures found")

        for fixture in pgram_fixtures:
            with self.subTest(fixture=fixture["name"]):
                df = fixture.get("df", 7.629)
                result = parse_borealis_data.parse_borealis_pgram(fixture["base64"], df)
                self.assertIsNotNone(result, f"Failed to parse {fixture['name']}")

                if result is not None:
                    # Should have many frequency bins
                    self.assertGreater(len(result), 50)

                    # Test specific expected samples if provided
                    if "expected_samples" in fixture:
                        # Calculate frequencies for this fixture
                        frequencies = parse_borealis_data.calculate_pgram_frequencies(
                            df
                        )

                        for index, expected_freq, expected_spl in fixture[
                            "expected_samples"
                        ]:
                            if index < len(result) and index < len(frequencies):
                                actual_spl = result[index]
                                actual_frequency = frequencies[index]

                                # Validate frequency matches expected frequency
                                self.assertAlmostEqual(
                                    actual_frequency,
                                    expected_freq,
                                    places=2,
                                    msg=f"Fixture {fixture['name']}: Expected frequency {expected_freq} Hz at index {index}, got {actual_frequency} Hz",
                                )

                                # Validate SPL value
                                self.assertAlmostEqual(
                                    actual_spl,
                                    expected_spl,
                                    places=1,
                                    msg=f"Fixture {fixture['name']}: Expected {expected_spl} dB at {expected_freq} Hz (index {index}), got {actual_spl}",
                                )

    def test_fixture_data_type_detection(self):
        """Test that all fixtures have correct lengths for automatic detection."""
        issues = test_fixtures.validate_fixture_lengths()
        self.assertEqual(len(issues), 0, f"Fixture length validation failed: {issues}")

        # Test each fixture type is detected correctly
        for data_type, fixtures in self.fixtures.items():
            for fixture in fixtures:
                length = len(fixture["base64"])
                with self.subTest(fixture=fixture["name"], data_type=data_type):
                    if data_type == "spectrum":
                        self.assertLess(length, 100)
                    elif data_type == "statistics":
                        self.assertGreaterEqual(length, 100)
                        self.assertLess(length, 200)
                    elif data_type == "pgram":
                        self.assertGreaterEqual(length, 200)


if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestParseBorealisData)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)
