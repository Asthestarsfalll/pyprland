" Unit conversion & co "
from typing import Any


def convert_monitor_dimension(
    size: int | str, ref_value, monitor: dict[str, Any]
) -> int:
    """Convert `size` into pixels (given a reference value applied to a `monitor`)
    if size is an integer, assumed pixels & return it
    if size is a string, expects a "%" or "px" suffix
    else throws an error
    """

    if isinstance(size, int):
        return size

    if isinstance(size, str):
        if size.endswith("%"):
            p = int(size[:-1])
            return int(ref_value / monitor["scale"] * p / 100)
        if size.endswith("px"):
            return int(size[:-2])

    raise ValueError(f"Unsupported format: {size} (applied to {ref_value})")


def convert_coords(coords: str, monitor: dict[str, Any]):
    """
    Converts a string like "X Y" to coordinates relative to monitor
    Supported formats for X, Y:
    - Percentage: "V%". V in [0; 100]
    - Pixels: "Vpx". V should fit in your screen and not be zero

    Example:
    "10% 20%", monitor 800x600 => 80, 120
    """

    return [
        convert_monitor_dimension(name, monitor[ref], monitor)
        for (name, ref) in zip(
            [coord.strip() for coord in coords.split()],
            (
                ("height", "width")
                if monitor["transform"] in (1, 3)
                else ("width", "height")
            ),
        )
    ]
