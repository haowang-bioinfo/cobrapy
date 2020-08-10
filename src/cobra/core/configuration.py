"""Provide a global configuration object."""


import logging
import types
from numbers import Number
from os import cpu_count
from textwrap import dedent
from typing import Optional, Tuple

from cobra.core.singleton import Singleton
from cobra.exceptions import SolverNotFound
from cobra.util.solver import interface_to_str
from cobra.util.solver import solvers as SOLVERS


__all__ = ("Configuration",)


logger = logging.getLogger(__name__)


class Configuration(metaclass=Singleton):
    """
    Define a global configuration object.

    The attributes of this singleton object are used as default values by cobra
    functions.

    Attributes
    ----------
    solver : {"glpk", "cplex", "gurobi", "glpk_exact"}
        The default solver for new models. The solver choices are the ones
        provided by `optlang` and depend on solvers installed in your environment.
    tolerance: float
        The default tolerance for the solver being used (default 1E-07).
    lower_bound : float, optional
        The standard lower bound for reversible reactions (default -1000).
    upper_bound : float, optional
        The standard upper bound for all reactions (default 1000).
    bounds : tuple of floats
        The default reaction bounds for newly created reactions. The bounds
        are in the form of lower_bound, upper_bound (default -1000.0, 1000.0).
    processes : int
        A default number of processes to use where multiprocessing is
        possible. The default number corresponds to the number of available
        cores (hyperthreads) minus one.

    """

    def __init__(self, **kwargs) -> None:
        """Initialize the configuration with its default attribute values."""
        super().__init__(**kwargs)
        self._solver = None
        self.tolerance = 1e-07
        self.lower_bound = None
        self.upper_bound = None
        self.processes = None

        self.bounds = -1000.0, 1000.0
        self._set_default_solver()
        self._set_default_processes()

    def _set_default_solver(self) -> None:
        """Set the default solver from a preferred order."""
        for name in ["gurobi", "cplex", "glpk"]:
            try:
                self.solver = name
            except SolverNotFound:
                continue
            else:
                break

    def _set_default_processes(self) -> None:
        """Set the default number of processes."""
        self.processes = cpu_count()
        if self.processes is None:
            logger.warning("The number of cores could not be detected - assuming one.")
            self.processes = 1
        if self.processes > 1:
            self.processes -= 1

    @property
    def solver(self) -> types.ModuleType:
        """Return the optlang solver interface."""
        return self._solver

    @solver.setter
    def solver(self, value) -> None:
        """Set the optlang solver interface."""
        not_valid_interface = SolverNotFound(
            f"'{value}' is not a valid solver interface. "
            f" Please pick one from {', '.join(SOLVERS)}."
        )
        if isinstance(value, str):
            if value not in SOLVERS:
                raise not_valid_interface
            interface = SOLVERS[value]
        elif isinstance(value, types.ModuleType) and hasattr(value, "Model"):
            interface = value
        else:
            raise not_valid_interface
        self._solver = interface

    @property
    def bounds(self) -> Tuple[Optional[Number], Optional[Number]]:
        """Return the lower, upper reaction bound pair."""
        return self.lower_bound, self.upper_bound

    @bounds.setter
    def bounds(self, bounds: Tuple[Optional[Number], Optional[Number]]) -> None:
        """Set the lower, upper reaction bound pair."""
        if None not in bounds:
            assert bounds[0] <= bounds[1]
        self.lower_bound = bounds[0]
        self.upper_bound = bounds[1]

    def __repr__(self) -> str:
        """Return a string representation of the current configuration values."""
        return dedent(
            f"""
            solver: {interface_to_str(self.solver)}
            tolerance: {self.tolerance}
            lower_bound: {self.lower_bound}
            upper_bound: {self.upper_bound}
            processes: {self.processes}
            """
        )

    def _repr_html_(self) -> str:
        """
        Return a rich HTML representation of the current configuration values.

        Notes
        -----
        This special method is used automatically in Jupyter notebooks to display a
        result from a cell.

        """
        return dedent(
            f"""
            <table>
              <thead>
                <tr>
                  <td><strong>Attribute</strong></td>
                  <td><strong>Description</strong></td>
                  <td><strong>Value</strong></td>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><pre>solver</pre></td>
                  <td>Mathematical optimization solver</td>
                  <td>{interface_to_str(self.solver)}</td>
                </tr>
                <tr>
                    <td><pre>tolerance</pre></td>
                    <td>General solver tolerance (feasibility, integrality, etc.)</td>
                    <td>{self.tolerance}</td>
                </tr>
                <tr>
                    <td><pre>lower_bound</pre></td>
                    <td>Default reaction lower bound</td>
                    <td>{self.lower_bound}</td>
                </tr>
                <tr>
                    <td><pre>upper_bound</pre></td>
                    <td>Default reaction upper bound</td>
                    <td>{self.upper_bound}</td>
                </tr>
                <tr>
                    <td><pre>processes</pre></td>
                    <td>Number of parallel processes</td>
                    <td>{self.processes}</td>
                </tr>
              </tbody>
            </table>
            """
        )