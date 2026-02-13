#!/usr/bin/env python3

"""
Plot spectrograms from Sofar Ocean API JSON data containing SPL readings.

This script reads JSON data from an API response containing hydrophone data and plots
complete spectrograms showing all data at once with zoom/pan capabilities.

The script filters for data objects with "data_type_name": "bm_borealis_band_spls_reading"
and plots each hydrophone (identified by "bristlemouth_node_id") in a separate window.

Usage:
    # Read from file
    ./plot_spectrogram_from_json.py sensor-data.json

    # Read from stdin
    cat sensor-data.json | ./plot_spectrogram_from_json.py

    # Specify custom parameters
    ./plot_spectrogram_from_json.py --iband-start 16 --dt 0.983 sensor-data.json
"""

import sys
import json
import argparse
from typing import Any, Dict, List, Tuple, NamedTuple
from datetime import datetime
import math
import numpy as np
from numpy.typing import NDArray

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.axes import Axes
from matplotlib.figure import Figure


class SPLPacket(NamedTuple):
    """SPL data packet."""

    spls_dB: List[float]
    iband_start: int
    dt: float
    timestamp: str


window_closed: bool = False


def on_close(event: Any) -> None:  # noqa: ARG001
    """Handle plot window close event.

    Args:
        event: Matplotlib close event (unused but required by callback signature)
    """
    global window_closed
    window_closed = True


def frequency_given_bin_index(index: float, iband_start: int) -> float:
    """Calculate frequency in Hz for a given bin index.

    Args:
        index: Frequency bin index (can be fractional)
        iband_start: Starting band index offset

    Returns:
        Frequency in Hz
    """
    return math.pow(10.0, (index + iband_start) / 10.0)


def bin_index_given_frequency(frequency: float, iband_start: int) -> float:
    """Calculate bin index for a given frequency.

    Args:
        frequency: Frequency in Hz
        iband_start: Starting band index offset

    Returns:
        Bin index (may be fractional)
    """
    return 10.0 * math.log10(frequency) - iband_start


def load_json_data(input_source: str) -> Dict[str, Any]:
    """Load JSON data from file or stdin.

    Args:
        input_source: File path or '-' for stdin

    Returns:
        Parsed JSON data as dictionary
    """
    if input_source == "-":
        data = json.load(sys.stdin)
    else:
        with open(input_source, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data


def extract_spl_packets(
    json_data: Dict[str, Any], iband_start: int, dt: float
) -> Dict[str, List[SPLPacket]]:
    """Extract SPL packets from JSON data, grouped by hydrophone node ID.

    Args:
        json_data: Parsed JSON data containing sensor readings
        iband_start: Starting band index for frequency calculation
        dt: Time interval between samples in seconds

    Returns:
        Dictionary mapping node IDs to lists of SPL packets

    Raises:
        ValueError: If JSON data is missing required fields or contains no SPL data
    """
    if "data" not in json_data:
        raise ValueError("JSON data does not contain 'data' field")

    # Filter for SPL readings
    spl_items: List[Dict[str, Any]] = [
        item
        for item in json_data["data"]
        if item.get("data_type_name") == "bm_borealis_band_spls_reading"
    ]

    if not spl_items:
        raise ValueError("No 'bm_borealis_band_spls_reading' items found in JSON data")

    # Group by bristlemouth_node_id
    packets_by_node: Dict[str, List[SPLPacket]] = {}

    for item in spl_items:
        node_id = item.get("bristlemouth_node_id", "unknown")
        if node_id not in packets_by_node:
            packets_by_node[node_id] = []

        packet = SPLPacket(
            spls_dB=item["value"],
            iband_start=iband_start,
            dt=dt,
            timestamp=item.get("timestamp", ""),
        )
        packets_by_node[node_id].append(packet)

    return packets_by_node


def parse_and_filter_timestamps(
    packets: List[SPLPacket],
) -> Tuple[List[datetime], List[SPLPacket]]:
    """Parse timestamps and filter out invalid ones (epoch 0).

    Args:
        packets: List of SPL data packets

    Returns:
        Tuple of (timestamps, valid_packets) with invalid timestamps filtered out
    """
    timestamps: List[datetime] = []
    valid_packets: List[SPLPacket] = []
    for packet in packets:
        ts_str = packet.timestamp
        # Skip epoch 0 timestamps
        if ts_str and not ts_str.startswith("1970-01-01T00:00:00"):
            try:
                # Parse ISO format timestamp
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                timestamps.append(ts)
                valid_packets.append(packet)
            except Exception:
                pass
    return timestamps, valid_packets


def build_spectrogram_data(
    valid_packets: List[SPLPacket], num_bins: int
) -> NDArray[np.float64]:
    """Convert SPL packets to spectrogram dB array.

    Args:
        valid_packets: List of valid SPL packets
        num_bins: Number of frequency bins

    Returns:
        2D array of spectrogram data (time x frequency) in dB
    """
    num_valid = len(valid_packets)
    spectrogram_dB: NDArray[np.float64] = np.zeros((num_valid, num_bins))

    for i, packet in enumerate(valid_packets):
        # The JSON data has a hardware-specific offset applied (185.642)
        # Subtract it to get the actual dB values in the range [-192, 0]
        spls_dB_actual: NDArray[np.float64] = np.array(packet.spls_dB) - 185.642
        # Convert to linear intensity like the UART version does
        intensity: NDArray[np.float64] = np.power(10.0, spls_dB_actual * 0.1)
        # Convert back to dB for plotting
        spectrogram_dB[i, :] = 10.0 * np.log10(intensity + 2e-38)

    return spectrogram_dB


def create_time_grid_with_gaps(
    time_values: NDArray[np.float64],
    spectrogram_dB: NDArray[np.float64],
    dt: float,
    num_bins: int,
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Create full time grid at dt resolution and fill in data with NaN for gaps.

    Args:
        time_values: Matplotlib date numbers for each packet
        spectrogram_dB: Spectrogram data array
        dt: Time interval between samples in seconds
        num_bins: Number of frequency bins

    Returns:
        Tuple of (time_grid, full_spectrogram) with gaps filled with NaN
    """
    start_time: float = float(time_values[0])  # type: ignore
    end_time: float = float(time_values[-1])  # type: ignore

    # Create time grid with dt spacing (convert dt seconds to matplotlib days)
    dt_days: float = dt / 86400.0
    num_time_steps: int = int((end_time - start_time) / dt_days) + 1
    time_grid: NDArray[np.float64] = np.linspace(start_time, end_time, num_time_steps)

    # Create full spectrogram array filled with NaN (will show as gaps)
    full_spectrogram: NDArray[np.float64] = np.full((num_time_steps, num_bins), np.nan)

    # Fill in the actual data at the correct time positions
    for i, time_val in enumerate(time_values):
        # Find the closest time grid index
        time_idx: int = int(round((float(time_val) - start_time) / dt_days))
        if 0 <= time_idx < num_time_steps:
            full_spectrogram[time_idx, :] = spectrogram_dB[i, :]

    return time_grid, full_spectrogram


def create_grid_edges(
    time_grid: NDArray[np.float64], num_bins: int, dt: float
) -> Tuple[NDArray[Any], NDArray[Any]]:
    """Create frequency and time edges for pcolormesh.

    Args:
        time_grid: Time grid values
        num_bins: Number of frequency bins
        dt: Time interval between samples in seconds

    Returns:
        Tuple of (freq_edges, time_edges)
    """
    # For frequency, use bin edges
    freq_edges: NDArray[Any] = np.arange(num_bins + 1) - 0.5

    # Create time edges
    dt_days: float = dt / 86400.0
    num_time_steps = len(time_grid)
    time_edges: NDArray[Any] = np.zeros(num_time_steps + 1)
    time_edges[0] = time_grid[0] - dt_days / 2
    for i in range(num_time_steps):
        if i < num_time_steps - 1:
            time_edges[i + 1] = (time_grid[i] + time_grid[i + 1]) / 2
        else:
            time_edges[i + 1] = time_grid[i] + dt_days / 2

    return freq_edges, time_edges


def create_gray_colormap() -> Any:
    """Create custom colormap with gray for NaN values.

    Returns:
        Colormap with gray color for missing/NaN data
    """
    from matplotlib.colors import ListedColormap

    turbo = plt.get_cmap("turbo")
    turbo_with_gray = turbo(np.arange(turbo.N))
    turbo_with_gray_cmap = ListedColormap(turbo_with_gray)
    turbo_with_gray_cmap.set_bad(color="#808080")  # Gray for NaN/missing data
    return turbo_with_gray_cmap


def configure_time_axis(ax: Axes) -> None:
    """Configure y-axis (time) formatting and orientation.

    Args:
        ax: Matplotlib axes object
    """
    # Invert y-axis so newest data is at bottom, oldest at top
    ax.invert_yaxis()

    # Format y-axis to show dates/times with seconds
    ax.yaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M:%S"))
    ax.yaxis.set_major_locator(mdates.AutoDateLocator())

    # Rotate y-axis labels for better readability
    for label in ax.get_yticklabels():
        label.set_rotation(0)
        label.set_horizontalalignment("right")


def configure_frequency_axis(
    ax: Axes, bin_centres: List[float], iband_start: int
) -> None:
    """Configure x-axis (frequency) tick positions and labels.

    Args:
        ax: Matplotlib axes object
        bin_centres: List of frequency bin center values
        iband_start: Starting band index for frequency calculation
    """
    tick_positions_Hz: List[int] = [
        30,
        40,
        50,
        60,
        80,
        100,
        200,
        300,
        400,
        500,
        600,
        800,
        1000,
        1500,
        2000,
        3000,
        4000,
        5000,
        6000,
        8000,
        10000,
        15000,
        20000,
        30000,
    ]
    while tick_positions_Hz and tick_positions_Hz[0] < bin_centres[0]:
        tick_positions_Hz = tick_positions_Hz[1:]
    while tick_positions_Hz and tick_positions_Hz[-1] > bin_centres[-1]:
        tick_positions_Hz = tick_positions_Hz[0:-1]

    tick_positions_bins: List[float] = [
        bin_index_given_frequency(x, iband_start) for x in tick_positions_Hz
    ]
    ax.set_xticks(tick_positions_bins)  # type: ignore
    ax.set_xticklabels([str(x) for x in tick_positions_Hz], rotation=45)  # type: ignore


def plot_hydrophone(
    node_id: str, packets: List[SPLPacket], clim: Tuple[float, float]
) -> None:
    """Plot spectrogram for a single hydrophone showing all data at once.

    Args:
        node_id: Hydrophone node identifier
        packets: List of SPL data packets
        clim: Color scale limits as (min, max) in dB
    """
    if not packets:
        print(f"No packets for hydrophone {node_id}", file=sys.stderr)
        return

    print(f"Plotting hydrophone {node_id}...", file=sys.stderr)

    # Get dimensions from first packet
    first_packet = packets[0]
    num_bins = len(first_packet.spls_dB)
    num_packets = len(packets)
    iband_start = first_packet.iband_start
    dt = first_packet.dt

    print(
        f"{num_bins} frequency bins, {num_packets} time samples for node {node_id}",
        file=sys.stderr,
    )

    # Parse timestamps and filter out invalid ones
    timestamps, valid_packets = parse_and_filter_timestamps(packets)

    if not timestamps:
        print(f"No valid timestamps found for hydrophone {node_id}", file=sys.stderr)
        return

    print(
        f"Valid packets with timestamps: {len(valid_packets)} (filtered out {num_packets - len(valid_packets)} invalid)",
        file=sys.stderr,
    )

    # Convert timestamps to matplotlib date numbers
    time_values: NDArray[np.float64] = mdates.date2num(timestamps)  # type: ignore

    # Build the spectrogram data array
    spectrogram_dB = build_spectrogram_data(valid_packets, num_bins)

    # Create figure and axis
    fig: Figure
    ax: Axes
    fig, ax = plt.subplots(figsize=(12, 8))  # type: ignore
    fig.canvas.mpl_connect("close_event", on_close)

    # Calculate frequency bin centers
    bin_centres: List[float] = [
        frequency_given_bin_index(x, iband_start) for x in range(num_bins)
    ]

    # Calculate and print time span
    time_span: float = (timestamps[-1] - timestamps[0]).total_seconds()
    print(
        f"Time span: {time_span:.1f} seconds ({time_span/3600:.2f} hours, {time_span/86400:.2f} days)",
        file=sys.stderr,
    )
    print(f"First timestamp: {timestamps[0]}", file=sys.stderr)
    print(f"Last timestamp: {timestamps[-1]}", file=sys.stderr)

    # Create full time grid with gaps filled with NaN
    time_grid, full_spectrogram = create_time_grid_with_gaps(
        time_values, spectrogram_dB, dt, num_bins  # type: ignore
    )

    # Create grid edges for pcolormesh
    freq_edges, time_edges = create_grid_edges(time_grid, num_bins, dt)

    # Create meshgrid
    mesh_x: NDArray[Any]
    mesh_y: NDArray[Any]
    mesh_x, mesh_y = np.meshgrid(freq_edges, time_edges)

    # Create custom colormap with gray for NaN values
    turbo_with_gray_cmap = create_gray_colormap()

    # Plot using pcolormesh
    im = ax.pcolormesh(  # type: ignore
        mesh_x,
        mesh_y,
        full_spectrogram,
        cmap=turbo_with_gray_cmap,
        vmin=clim[0],
        vmax=clim[1],
        shading="flat",
    )

    # Configure plot labels and axes
    ax.set_title(f"Hydrophone {node_id}")  # type: ignore
    ax.set_ylabel("Time (UTC)")  # type: ignore
    ax.set_xlabel("Frequency (Hz)")  # type: ignore

    configure_time_axis(ax)
    configure_frequency_axis(ax, bin_centres, iband_start)

    # Customize status bar to show frequency and SPL value
    def format_coord(x: float, y: float) -> str:
        """Format coordinates for status bar display.

        Args:
            x: Frequency bin index
            y: Time value (matplotlib date number)

        Returns:
            Formatted string for status bar
        """
        # Convert bin index to frequency
        freq_Hz = frequency_given_bin_index(x, iband_start)

        # Format time using matplotlib date formatter
        time_str = mdates.num2date(y).strftime("%Y-%m-%d %H:%M:%S UTC")  # type: ignore

        # Get SPL value at this position
        # Find the closest grid indices
        x_idx = int(round(x))
        y_idx = int(round((y - float(time_grid[0])) / (dt / 86400.0)))

        if 0 <= x_idx < num_bins and 0 <= y_idx < len(time_grid):
            spl_value = full_spectrogram[y_idx, x_idx]
            if np.isnan(spl_value):
                spl_str = "no data"
            else:
                spl_str = f"{spl_value:.1f} dB"
        else:
            spl_str = "out of range"

        return f"Freq: {freq_Hz:.1f} Hz, Time: {time_str}, SPL: {spl_str}"

    ax.format_coord = format_coord  # type: ignore

    # Add colorbar
    plt.colorbar(im, ax=ax, label="SPL (dB re µPa²)")  # type: ignore

    fig.tight_layout()

    print(
        f"Displaying plot for {node_id}. Use zoom/pan tools to explore. Close window to exit.",
        file=sys.stderr,
    )
    plt.show()  # type: ignore


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Plot spectrograms from JSON data containing SPL readings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Read from stdin
  cat sensor-data.json | %(prog)s -

  # Read from file
  %(prog)s sensor-data.json

  # Specify custom parameters
  %(prog)s --iband-start 16 --dt 0.983 sensor-data.json
        """,
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help='JSON file to read (use "-" for stdin, default: stdin)',
    )
    parser.add_argument(
        "--iband-start",
        type=int,
        default=16,
        help="Starting band index for frequency calculation (default: 16)",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=0.983,
        help="Time interval between samples in seconds (default: 0.983)",
    )
    parser.add_argument(
        "--clim",
        type=float,
        nargs=2,
        default=(-123, -3),
        metavar=("MIN", "MAX"),
        help="Color scale limits in dB (default: -123 -3)",
    )

    args = parser.parse_args()

    # Load JSON data
    try:
        json_data: Dict[str, Any] = load_json_data(args.input)
    except Exception as e:
        print(f"Error loading JSON data: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract SPL packets grouped by node ID
    try:
        packets_by_node: Dict[str, List[SPLPacket]] = extract_spl_packets(
            json_data, args.iband_start, args.dt
        )
    except Exception as e:
        print(f"Error extracting SPL packets: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(packets_by_node)} hydrophone(s):", file=sys.stderr)
    for node_id, packets in packets_by_node.items():
        print(f"  {node_id}: {len(packets)} packets", file=sys.stderr)

    # Plot each hydrophone in a separate window
    if len(packets_by_node) == 0:
        print("No hydrophones found to plot", file=sys.stderr)
        sys.exit(1)

    for node_id, packets in packets_by_node.items():
        plot_hydrophone(node_id, packets, tuple(args.clim))


if __name__ == "__main__":
    main()
