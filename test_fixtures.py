#!/usr/bin/env python3
"""
Test fixtures for Borealis data parser.

This module contains example base64 data for testing all three data types:
- spectrum: Short base64 strings for spectrum data
- statistics: Medium base64 strings for statistics data
- pgram: Long base64 strings for pgram data

Each fixture includes the base64 input and optionally expected output samples
for validation testing.
"""

SPECTRUM_FIXTURES = [
    {
        "name": "spectrum_example_1",
        "base64": "YcurqkquiRqphlqpS5qe15madRmXexmUYMmUaCmRIqmSIbmRUDmRnyiJ",
        "expected_samples": [
            (0, 40, 130.19),  # (index, frequency, spl)
            (1, 50, 122.45),
            (-1, 20000, 96.49),  # Last entry
        ],
    },
    {
        "name": "spectrum_example_2",
        "base64": "3KqppxqlW0qkLuqg7dmXYQmOngiEFriAM2iGlZiOHzmN8TiP7liS",
        "expected_samples": [
            (0, 40, 123.95),
            (1, 50, 120.86),
            (7, 200, 114.30),
            (15, 1250, 90.16),
        ],
    },
    {
        "name": "spectrum_example_3",
        "base64": "uOqoO1qkQoqmI8qgAsqYcmmOajiBD0iAJ+iFmxiPISmN7UiP26iS",
        "expected_samples": [
            (0, 40, 122.27),
            (5, 125, 118.52),
            (10, 400, 106.99),
            (20, 4000, 103.19),
        ],
    },
    # Add more spectrum examples here:
    # {
    #     "name": "spectrum_example_2",
    #     "base64": "YOUR_BASE64_STRING_HERE",
    #     "expected_samples": [
    #         (0, 40, expected_spl_value),
    #         (1, 50, expected_spl_value),
    #     ]
    # },
]

# Statistics test fixtures (100-199 characters)
STATISTICS_FIXTURES = [
    {
        "name": "statistics_example_1",
        "base64": "oKetrZiiqamUnqallpuiopean5+XmZycmJqcm5qcnp2UlpeWjo+Rj4mLjIuEhoeGgoSFhIOEhYSBgoODgoOEg4OEhYSFhYaGh4eIh4mJiYmKiouLjY2NjY2NjY2Ki4uLioqKiouLjIw=",
        "expected_samples": [
            # (index, frequency, [Q1, Q2, Q3, Mean])
            (0, 40, [113.64, 118.89, 123.39, 123.39]),
            (1, 50, [107.64, 115.14, 120.39, 120.39]),
            (-1, 12500, [97.89, 97.89, 98.64, 98.64]),  # Last entry
        ],
    },
    {
        "name": "statistics_example_2",
        "base64": "lZykp5iboaOfoKKjpaanp6Wmp6alpqemp6ipqKanqKehoaKim5ydnJeYmJiQkJGQiYmKioKCg4N/gICAfn9/f4CAgYGDg4SDh4iIiIuLi4uNjY6NjIyNjI6Ojo6Pj4+PjY2OjpOUlJQ=",
        "expected_samples": [
            (0, 40, [105.39, 110.64, 116.64, 118.89]),
            (1, 50, [107.64, 109.89, 114.39, 115.89]),
            (20, 4000, [99.39, 99.39, 100.14, 99.39]),
        ],
    },
    {
        "name": "statistics_example_3",
        "base64": "r7a9wquyur+nr7e8o6qzuZ6nr7Waoqyylp6orpCZo6qMk56mio+ZoomMlJ6JipCaiYqNlYmKi5KIiYuOiImKjIiJioqKiouMjI2Njo6Pj4+QkJGRjo+Pj4+QkJCQkJCQjIyNjJSUlJQ=",
        "expected_samples": [
            (8, 250, [98.64, 103.89, 112.14, 118.14]),
            (16, 1600, [95.64, 96.39, 97.14, 97.14]),
            (-1, 12500, [104.64, 104.64, 104.64, 104.64]),
        ],
    },
    # Add more statistics examples here:
    # {
    #     "name": "statistics_example_2",
    #     "base64": "YOUR_BASE64_STRING_HERE",
    #     "expected_samples": [
    #         (0, 40, [q1, q2, q3, mean]),
    #         (1, 50, [q1, q2, q3, mean]),
    #     ]
    # },
]

# Pgram test fixtures (>= 200 characters)
PGRAM_FIXTURES = [
    {
        "name": "pgram_example_1",
        "base64": "iYR/mpCzua+KfHl1fZaZjXJxb2tsf4FzbmxpaGp1dGdpaGdreIWBbGdobnp4aWZpcXNqZ2hwbmdoZ2ZnZ2poZWZnZGhoZWdnaGpnZ2dpZ2RkZ2ZlZWZmZWhoZ2ZlZWVmZ2ZmZmdnZ2ZmZmZnaGlpZ2dnaGhoaGhpaWlqanJxamppaWpqampra2pqa2tra2tsbGxsbG1sbW1tbm5ubm5ubm5vb29vcHBwcG9ubW1t",
        "df": 7.629,  # Default df value
        "expected_samples": [
            # (index, frequency, spl)
            (0, 15.26, 96.39),
            (1, 22.89, 92.64),
            (2, 30.52, 88.89),
            (10, 91.55, 84.39),
            (50, 436.28, 73.14),
            (100, 1848.89, 70.89),
            (150, 7835.32, 75.39),
            (-1, 19743.78, 75.39),  # Last entry
        ],
    },
    {
        "name": "pgram_example_2",
        "base64": "iYSCg5Czua+KfHl5e5aZjXJzcnBvf4F0bm1rbW50c2toZmpteYaBa2hpbnt4a2hpcHNrZ2pxb2ZmaGdlZ2toZ2dnZ2lnZWlnZmlmZ2ZnZmZnZ2ZlZWZmZmVlZmdnZmVmZmdmZmdnZmZmZ2dnZ2hoaGhoaGhoaGlpaGlpanJxamlqampqa2tra2pra2xsa2xsbGxtbG1tbW1tbm5vbm5ubm5ub29vb3FxcG9ubW5t",
        "df": 7.629,  # Default df value
        "expected_samples": [
            (0, 15.26, 96.39),
            (1, 22.89, 92.64),
            (2, 30.52, 91.14),
            (10, 91.55, 84.39),
            (50, 436.28, 73.89),
            (-1, 19743.78, 75.39),  # Last entry
        ],
    },
    {
        "name": "pgram_example_3",
        "base64": "iYOBgZCzua+KfXh4fJWZjHR0cnBxf4BybW5tbGp0dGxpampoeIWBbGhrbnt4a2hocHJraWlwbWdnZmRnaGlnZmhnZWdmZ2poZ2dmaGZoZWVmaGdmZ2hmZmdmZmZmZmZlZmZnZ2ZmZ2ZnZ2doaGhnaGhoZ2hoaGhoaWlpanFxamppampqampqamtra2tsbGxsbGxsbG1tbW1tbm5tbm5ub29vb29vcHBwcG9ubm1t",
        "df": 7.629,  # Default df value
        "expected_samples": [
            (0, 15.26, 96.39),
            (1, 22.89, 91.89),
            (2, 30.52, 90.39),
            (10, 91.55, 83.64),
            (50, 436.28, 73.89),
            (-1, 19743.78, 75.39),  # Last entry
        ],
    },
    # Add more pgram examples here:
    # {
    #     "name": "pgram_example_2",
    #     "base64": "YOUR_BASE64_STRING_HERE",
    #     "df": 7.629,  # or custom df value
    #     "expected_samples": [
    #         (0, expected_freq, expected_spl),
    #         (1, expected_freq, expected_spl),
    #     ]
    # },
]


def get_all_fixtures():
    """Return all test fixtures organized by type."""
    return {
        "spectrum": SPECTRUM_FIXTURES,
        "statistics": STATISTICS_FIXTURES,
        "pgram": PGRAM_FIXTURES,
    }


def get_fixtures_by_type(data_type):
    """Get all fixtures for a specific data type."""
    all_fixtures = get_all_fixtures()
    return all_fixtures.get(data_type, [])


def validate_fixture_lengths():
    """Validate that fixture lengths match expected data type detection."""
    issues = []

    for fixture in SPECTRUM_FIXTURES:
        length = len(fixture["base64"])
        if length >= 100:
            issues.append(
                f"Spectrum fixture '{fixture['name']}' is too long ({length} chars)"
            )

    for fixture in STATISTICS_FIXTURES:
        length = len(fixture["base64"])
        if length < 100 or length >= 200:
            issues.append(
                f"Statistics fixture '{fixture['name']}' wrong length ({length} chars, should be 100-199)"
            )

    for fixture in PGRAM_FIXTURES:
        length = len(fixture["base64"])
        if length < 200:
            issues.append(
                f"Pgram fixture '{fixture['name']}' is too short ({length} chars)"
            )

    return issues


if __name__ == "__main__":
    """Run basic validation when called directly."""
    print("Borealis Test Fixtures")
    print("=" * 30)

    fixtures = get_all_fixtures()
    for data_type, fixture_list in fixtures.items():
        print(f"\n{data_type.upper()} fixtures: {len(fixture_list)}")
        for fixture in fixture_list:
            length = len(fixture["base64"])
            print(f"  - {fixture['name']}: {length} chars")

    # Validate fixture lengths
    issues = validate_fixture_lengths()
    if issues:
        print(f"\n⚠️  VALIDATION ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ All fixture lengths are valid for automatic data type detection")

    print(f"\nTo add new fixtures:")
    print(f"1. Add entries to the appropriate list in this file")
    print(f"2. Include base64 string and expected output samples")
    print(f"3. Run 'python test_fixtures.py' to validate")
    print(f"4. Run 'python run_tests.py' to test with new fixtures")
