#!/usr/bin/env python3
"""
Simple test runner for parse_borealis_data.py

This script runs all tests and provides a summary of results.
Uses only built-in Python modules.
"""

import subprocess
import sys
import os
import test_fixtures


def run_tests():
    """Run the test suite and return success status."""
    print("Running Borealis Data Parser Tests...")
    print("=" * 50)

    try:
        # Run the tests using unittest module
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "test_parse_borealis_data.py", "-v"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
        )

        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("✅ ALL TESTS PASSED!")
            print("=" * 50)
            return True
        else:
            print("\n" + "=" * 50)
            print("❌ SOME TESTS FAILED!")
            print("=" * 50)
            return False

    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def run_example_tests():
    """Run tests with all fixture data."""
    print("\nRunning fixture data validation...")
    print("-" * 30)

    fixtures = test_fixtures.get_all_fixtures()
    total_tests = 0
    success_count = 0

    for data_type, fixture_list in fixtures.items():
        print(f"\nTesting {data_type.upper()} data ({len(fixture_list)} fixtures)...")

        for fixture in fixture_list:
            total_tests += 1
            try:
                # Prepare command arguments
                cmd = [
                    sys.executable,
                    "parse_borealis_data.py",
                    "--data-type",
                    data_type,
                ]

                # Add df parameter for pgram data
                if data_type == "pgram" and "df" in fixture:
                    cmd.extend(["--df", str(fixture["df"])])

                result = subprocess.run(
                    cmd,
                    input=fixture["base64"],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(__file__),
                )

                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split("\n")
                    # Filter out comment lines (starting with #)
                    data_lines = [line for line in lines if not line.startswith("#")]

                    if len(data_lines) > 1:  # Header + at least one data line
                        print(
                            f"  ✅ {fixture['name']}: {len(data_lines)-1} data points"
                        )
                        success_count += 1
                    else:
                        print(f"  ❌ {fixture['name']}: No data returned")
                else:
                    print(f"  ❌ {fixture['name']}: Parsing failed")
                    if result.stderr:
                        print(f"     Error: {result.stderr.strip()}")

            except Exception as e:
                print(f"  ❌ {fixture['name']}: Test failed with exception: {e}")

    print(f"\nFixture validation: {success_count}/{total_tests} passed")
    return success_count == total_tests


if __name__ == "__main__":
    print("Borealis Data Parser Test Suite")
    print("================================")

    # Run unit tests
    unit_tests_passed = run_tests()

    # Run example validation tests
    example_tests_passed = run_example_tests()

    # Final summary
    print("\n" + "=" * 50)
    print("FINAL SUMMARY:")
    print(f"Unit Tests: {'PASSED' if unit_tests_passed else 'FAILED'}")
    print(f"Example Tests: {'PASSED' if example_tests_passed else 'FAILED'}")

    if unit_tests_passed and example_tests_passed:
        print("\n🎉 ALL TESTS PASSED! The parser is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED! Please check the output above.")
        sys.exit(1)
