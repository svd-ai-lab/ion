"""Driver registry for ion."""
from __future__ import annotations

from ion.driver import DriverProtocol
from ion.drivers.pybamm import PyBaMMLDriver
from ion.drivers.fluent import PyFluentDriver
from ion.drivers.matlab import MatlabDriver

DRIVERS: list[DriverProtocol] = [
    PyBaMMLDriver(),
    PyFluentDriver(),
    MatlabDriver(),
]


def get_driver(name: str) -> DriverProtocol | None:
    """Get a driver by name."""
    for d in DRIVERS:
        if d.name == name:
            return d
    return None
