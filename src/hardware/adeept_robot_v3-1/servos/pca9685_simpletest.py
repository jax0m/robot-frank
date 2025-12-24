# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Outputs a 50% duty cycle PWM single on the 0th channel.
# Connect an LED and resistor in series to the pin
# to visualize duty cycle changes and its impact on brightness.

import board
import time
from typing import Iterator, Tuple

from adafruit_pca9685 import PCA9685


def iterate_in_chunks(
    start: int = 7600,  # 1000@30, 3400@100
    chunk_size: int = 2000,
    limit: int = 14250,  # 5200@30, 16200@100
) -> Iterator[Tuple[int, int, int]]:
    """
    Iterate from ``start`` to ``limit`` (default 65535) in successive
    groups of ``chunk_size`` (default 500).

    For each group the function yields a tuple ``(first, last, count)``
    where ``first`` is the first number of the chunk, ``last`` is the
    last number (or ``limit`` if the final chunk is smaller), and
    ``count`` is the number of values actually yielded for that chunk.

    Parameters
    ----------
    start : int
        The first value to process. Must be ≤ ``limit``.
    chunk_size : int, optional
        How many numbers to include in each iteration step. Defaults to 500.
    limit : int, optional
        Upper bound of the iteration (inclusive). Defaults to 65535.

    Yields
    ------
    tuple[int, int, int]
        ``(first, last, count)`` for each completed chunk.

    Example
    -------
    # >>> for first, last, cnt in iterate_in_chunks(1000):
    # ...     print(f"Processing {first}‑{last} ({cnt} values)")
    Processing 1000‑1499 (500 values)
    Processing 1500‑1999 (500 values)
    …
    """
    if start > limit:
        raise ValueError("``start`` must be less than or equal to ``limit``.")

    current = start
    while current <= limit:
        # Determine the end of the current chunk; cap it at the limit.
        chunk_end = min(current + chunk_size - 1, limit)
        count = chunk_end - current + 1  # number of values in this chunk
        yield current, chunk_end, count
        current = chunk_end + 1  # move to the start of the next chunk


# Create the I2C bus interface.
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = busio.I2C(board.GP1, board.GP0)    # Pi Pico RP2040

# Create a simple PCA9685 class instance.
pca = PCA9685(i2c, address=0x5F)

# Set the PWM frequency to 60hz.
pca.frequency = 100


# Example: start at 1000 and handle each 500‑item block up to 65535
for first, last, cnt in iterate_in_chunks():
    # Place whatever work you need here (e.g., call another function)
    print(f"Chunk {first}‑{last} ({cnt} items)")
    pca.channels[0].duty_cycle = first
    time.sleep(1)
# Set the PWM duty cycle for channel zero to 50%. duty_cycle is 16 bits to match other PWM objects
# but the PCA9685 will only actually give 12 bits of resolution.
# try:
#     print("Run 24575")
#     pca.channels[2].duty_cycle = 26575
# except Exception as e:
#     print("exception caught:",e)
# time.sleep(5)
# try:
#     print("Run 32767")
#     pca.channels[2].duty_cycle = 32767
# except Exception as e:
#     print("exception caught:",e)
# time.sleep(5)
# try:
#     print("Run 40958")
#     pca.channels[2].duty_cycle = 35958
# except Exception as e:
#     print("exception caught:",e)
