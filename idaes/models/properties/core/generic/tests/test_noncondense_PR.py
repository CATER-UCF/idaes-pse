#################################################################################
# The Institute for the Design of Advanced Energy Systems Integrated Platform
# Framework (IDAES IP) was produced under the DOE Institute for the
# Design of Advanced Energy Systems (IDAES), and is copyright (c) 2018-2021
# by the software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia University
# Research Corporation, et al.  All rights reserved.
#
# Please see the files COPYRIGHT.md and LICENSE.md for full copyright and
# license information.
#################################################################################
"""
Integration tests for generic property package framework

Author: Andrew Lee
"""
# Import Python libraries
import pytest

# Import Pyomo components
from pyomo.environ import (
    check_optimal_termination,
    ConcreteModel,
    Set,
    value,
    units as pyunits,
)

# Import IDAES cores
from idaes.core import LiquidPhase, VaporPhase, Component, PhaseType as PT
from idaes.models.properties.core.generic.generic_property import GenericParameterBlock

from idaes.core.util.model_statistics import (
    degrees_of_freedom,
    fixed_variables_set,
    activated_constraints_set,
)
from idaes.core.util import get_solver

from idaes.models.properties.core.state_definitions import FTPx
from idaes.models.properties.core.eos.ceos import Cubic, CubicType
from idaes.models.properties.core.phase_equil import SmoothVLE
from idaes.models.properties.core.phase_equil.bubble_dew import LogBubbleDew
from idaes.models.properties.core.phase_equil.forms import log_fugacity

import idaes.models.properties.core.pure.RPP4 as RPP4

import idaes.logger as idaeslog

# Set up logger
_log = idaeslog.getLogger(__name__)
solver = get_solver()


# -----------------------------------------------------------------------------
configuration = {
    # Specifying components
    "components": {
        "benzene": {
            "type": Component,
            "enth_mol_ig_comp": RPP4,
            "entr_mol_ig_comp": RPP4,
            "pressure_sat_comp": RPP4,
            "phase_equilibrium_form": {("Vap", "Liq"): log_fugacity},
            "parameter_data": {
                "mw": 78.1136e-3,  # [1]
                "pressure_crit": 48.9e5,  # [1]
                "temperature_crit": 562.2,  # [1]
                "omega": 0.212,  # [1]
                "cp_mol_ig_comp_coeff": {
                    "A": -3.392e1,  # [1]
                    "B": 4.739e-1,
                    "C": -3.017e-4,
                    "D": 7.130e-8,
                },
                "enth_mol_form_vap_comp_ref": 82.9e3,  # [3]
                "entr_mol_form_vap_comp_ref": -269,  # [3]
                "pressure_sat_comp_coeff": {
                    "A": -6.98273,  # [1]
                    "B": 1.33213,
                    "C": -2.62863,
                    "D": -3.33399,
                },
            },
        },
        "toluene": {
            "type": Component,
            "enth_mol_ig_comp": RPP4,
            "entr_mol_ig_comp": RPP4,
            "pressure_sat_comp": RPP4,
            "phase_equilibrium_form": {("Vap", "Liq"): log_fugacity},
            "parameter_data": {
                "mw": 92.1405e-3,  # [1]
                "pressure_crit": 41e5,  # [1]
                "temperature_crit": 591.8,  # [1]
                "omega": 0.263,  # [1]
                "cp_mol_ig_comp_coeff": {
                    "A": -2.435e1,
                    "B": 5.125e-1,
                    "C": -2.765e-4,
                    "D": 4.911e-8,
                },
                "enth_mol_form_vap_comp_ref": 50.1e3,  # [3]
                "entr_mol_form_vap_comp_ref": -321,  # [3]
                "pressure_sat_comp_coeff": {
                    "A": -7.28607,  # [1]
                    "B": 1.38091,
                    "C": -2.83433,
                    "D": -2.79168,
                },
            },
        },
        "N2": {
            "type": Component,
            "valid_phase_types": PT.vaporPhase,
            "enth_mol_ig_comp": RPP4,
            "parameter_data": {
                "mw": 92.1405e-3,
                "pressure_crit": 41e5,
                "temperature_crit": 591.8,
                "omega": 0.263,
                "cp_mol_ig_comp_coeff": {
                    "A": -2.435e1,
                    "B": 5.125e-1,
                    "C": -2.765e-4,
                    "D": 4.911e-8,
                },
                "enth_mol_form_vap_comp_ref": 50.1e3,
            },
        },
    },
    # Specifying phases
    "phases": {
        "Liq": {
            "type": LiquidPhase,
            "equation_of_state": Cubic,
            "equation_of_state_options": {"type": CubicType.PR},
        },
        "Vap": {
            "type": VaporPhase,
            "equation_of_state": Cubic,
            "equation_of_state_options": {"type": CubicType.PR},
        },
    },
    # Specifying state definition
    "state_definition": FTPx,
    "state_bounds": {
        "flow_mol": (0, 100, 1000),
        "temperature": (273.15, 300, 450),
        "pressure": (5e4, 1e5, 1e6),
    },
    "pressure_ref": 1e5,
    "temperature_ref": 300,
    # Declare a base units dict to save code later
    "base_units": {
        "time": pyunits.s,
        "length": pyunits.m,
        "mass": pyunits.kg,
        "amount": pyunits.mol,
        "temperature": pyunits.K,
    },
    # Defining phase equilibria
    "phases_in_equilibrium": [("Vap", "Liq")],
    "phase_equilibrium_state": {("Vap", "Liq"): SmoothVLE},
    "bubble_dew_method": LogBubbleDew,
    "parameter_data": {
        "PR_kappa": {
            ("benzene", "benzene"): 0.000,
            ("benzene", "toluene"): 0.000,
            ("benzene", "N2"): 0.000,
            ("toluene", "benzene"): 0.000,
            ("toluene", "toluene"): 0.000,
            ("toluene", "N2"): 0.000,
            ("N2", "benzene"): 0.000,
            ("N2", "toluene"): 0.000,
            ("N2", "N2"): 0.000,
        }
    },
}


class TestParamBlock(object):
    @pytest.mark.unit
    def test_build(self):
        model = ConcreteModel()
        model.params = GenericParameterBlock(default=configuration)

        assert isinstance(model.params.phase_list, Set)
        assert len(model.params.phase_list) == 2
        for i in model.params.phase_list:
            assert i in ["Liq", "Vap"]
        assert model.params.Liq.is_liquid_phase()
        assert model.params.Vap.is_vapor_phase()

        assert isinstance(model.params.component_list, Set)
        assert len(model.params.component_list) == 3
        for i in model.params.component_list:
            assert i in ["benzene", "toluene", "N2"]
            assert isinstance(model.params.get_component(i), Component)

        assert isinstance(model.params._phase_component_set, Set)
        assert len(model.params._phase_component_set) == 5
        for i in model.params._phase_component_set:
            assert i in [
                ("Liq", "benzene"),
                ("Liq", "toluene"),
                ("Vap", "benzene"),
                ("Vap", "toluene"),
                ("Vap", "N2"),
            ]

        assert model.params.config.state_definition == FTPx

        assert model.params.config.state_bounds == {
            "flow_mol": (0, 100, 1000),
            "temperature": (273.15, 300, 450),
            "pressure": (5e4, 1e5, 1e6),
        }

        assert model.params.config.phase_equilibrium_state == {
            ("Vap", "Liq"): SmoothVLE
        }

        assert isinstance(model.params.phase_equilibrium_idx, Set)
        assert len(model.params.phase_equilibrium_idx) == 2
        for i in model.params.phase_equilibrium_idx:
            assert i in ["PE1", "PE2"]

        assert model.params.phase_equilibrium_list == {
            "PE1": {"benzene": ("Vap", "Liq")},
            "PE2": {"toluene": ("Vap", "Liq")},
        }

        assert model.params.pressure_ref.value == 1e5
        assert model.params.temperature_ref.value == 300


class TestNonCondensable_Liquid(object):
    @pytest.fixture(scope="class")
    def model(self):
        model = ConcreteModel()
        model.params = GenericParameterBlock(default=configuration)

        model.props = model.params.build_state_block(
            [1], default={"defined_state": True}
        )

        # Fix state
        model.props[1].flow_mol.fix(1)
        model.props[1].temperature.fix(360)
        model.props[1].pressure.fix(101325)
        model.props[1].mole_frac_comp["benzene"].fix(0.4)
        model.props[1].mole_frac_comp["toluene"].fix(0.4)
        model.props[1].mole_frac_comp["N2"].fix(0.2)

        return model

    @pytest.mark.unit
    def test_dof(self, model):
        assert degrees_of_freedom(model.props[1]) == 0

    @pytest.mark.component
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_initialize(self, model):
        orig_fixed_vars = fixed_variables_set(model)
        orig_act_consts = activated_constraints_set(model)

        model.props.initialize(optarg={"tol": 1e-6}, outlvl=idaeslog.DEBUG)

        assert degrees_of_freedom(model) == 0

        fin_fixed_vars = fixed_variables_set(model)
        fin_act_consts = activated_constraints_set(model)

        assert len(fin_act_consts) == len(orig_act_consts)
        assert len(fin_fixed_vars) == len(orig_fixed_vars)

        for c in fin_act_consts:
            assert c in orig_act_consts
        for v in fin_fixed_vars:
            assert v in orig_fixed_vars

    @pytest.mark.component
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_solve(self, model):
        results = solver.solve(model)

        # Check for optimal solution
        assert check_optimal_termination(results)

    @pytest.mark.component
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_solution(self, model):
        # Check phase equilibrium results
        assert model.props[1].mole_frac_phase_comp[
            "Liq", "benzene"
        ].value == pytest.approx(0.3424, abs=1e-4)
        assert model.props[1].mole_frac_phase_comp[
            "Liq", "toluene"
        ].value == pytest.approx(0.6576, abs=1e-4)

        assert pytest.approx(1, abs=1e-4) == (
            model.props[1].mole_frac_phase_comp["Liq", "benzene"].value
            + model.props[1].mole_frac_phase_comp["Liq", "toluene"].value
        )

        assert model.props[1].mole_frac_phase_comp[
            "Vap", "benzene"
        ].value == pytest.approx(0.4164, abs=1e-4)
        assert model.props[1].mole_frac_phase_comp[
            "Vap", "toluene"
        ].value == pytest.approx(0.3266, abs=1e-4)
        assert model.props[1].mole_frac_phase_comp["Vap", "N2"].value == pytest.approx(
            0.2570, abs=1e-4
        )

        assert pytest.approx(1, abs=1e-4) == value(
            model.props[1].mole_frac_phase_comp["Vap", "benzene"]
            + model.props[1].mole_frac_phase_comp["Vap", "toluene"]
            + model.props[1].mole_frac_phase_comp["Vap", "N2"]
        )

        assert model.props[1].phase_frac["Vap"].value == pytest.approx(0.7782, abs=1e-4)
        assert model.props[1].phase_frac["Liq"].value == pytest.approx(0.2218, abs=1e-4)

        assert pytest.approx(
            model.props[1].mole_frac_comp["benzene"].value, abs=1e-4
        ) == value(
            model.props[1].mole_frac_phase_comp["Vap", "benzene"]
            * model.props[1].phase_frac["Vap"]
            + model.props[1].mole_frac_phase_comp["Liq", "benzene"]
            * model.props[1].phase_frac["Liq"]
        )
        assert pytest.approx(
            model.props[1].mole_frac_comp["toluene"].value, abs=1e-4
        ) == value(
            model.props[1].mole_frac_phase_comp["Vap", "toluene"]
            * model.props[1].phase_frac["Vap"]
            + model.props[1].mole_frac_phase_comp["Liq", "toluene"]
            * model.props[1].phase_frac["Liq"]
        )
        assert pytest.approx(
            model.props[1].mole_frac_comp["N2"].value, abs=1e-4
        ) == value(
            model.props[1].mole_frac_phase_comp["Vap", "N2"]
            * model.props[1].phase_frac["Vap"]
        )

    @pytest.mark.unit
    @pytest.mark.ui
    def test_report(self, model):
        model.props[1].report()


class TestNonCondensable_Vapour(object):
    @pytest.fixture(scope="class")
    def model(self):
        model = ConcreteModel()
        model.params = GenericParameterBlock(default=configuration)

        model.props = model.params.build_state_block(
            [1], default={"defined_state": True}
        )

        # Fix state
        model.props[1].flow_mol.fix(1)
        model.props[1].temperature.fix(380)
        model.props[1].pressure.fix(101325)
        model.props[1].mole_frac_comp["benzene"].fix(0.4)
        model.props[1].mole_frac_comp["toluene"].fix(0.4)
        model.props[1].mole_frac_comp["N2"].fix(0.2)

        return model

    @pytest.mark.unit
    def test_dof(self, model):
        assert degrees_of_freedom(model.props[1]) == 0

    @pytest.mark.component
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_initialize(self, model):
        orig_fixed_vars = fixed_variables_set(model)
        orig_act_consts = activated_constraints_set(model)

        model.props.initialize(optarg={"tol": 1e-6}, outlvl=idaeslog.DEBUG)

        assert degrees_of_freedom(model) == 0

        fin_fixed_vars = fixed_variables_set(model)
        fin_act_consts = activated_constraints_set(model)

        assert len(fin_act_consts) == len(orig_act_consts)
        assert len(fin_fixed_vars) == len(orig_fixed_vars)

        for c in fin_act_consts:
            assert c in orig_act_consts
        for v in fin_fixed_vars:
            assert v in orig_fixed_vars

    @pytest.mark.component
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_solve(self, model):
        results = solver.solve(model)

        # Check for optimal solution
        assert check_optimal_termination(results)

    @pytest.mark.component
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_solution(self, model):
        # Check phase equilibrium results
        assert model.props[1].mole_frac_phase_comp[
            "Liq", "benzene"
        ].value == pytest.approx(0.2931, abs=1e-4)
        assert model.props[1].mole_frac_phase_comp[
            "Liq", "toluene"
        ].value == pytest.approx(0.7069, abs=1e-4)

        assert pytest.approx(1, abs=1e-4) == (
            model.props[1].mole_frac_phase_comp["Liq", "benzene"].value
            + model.props[1].mole_frac_phase_comp["Liq", "toluene"].value
        )

        assert model.props[1].mole_frac_phase_comp[
            "Vap", "benzene"
        ].value == pytest.approx(0.4, abs=1e-4)
        assert model.props[1].mole_frac_phase_comp[
            "Vap", "toluene"
        ].value == pytest.approx(0.4, abs=1e-4)
        assert model.props[1].mole_frac_phase_comp["Vap", "N2"].value == pytest.approx(
            0.2, abs=1e-4
        )

        assert pytest.approx(1, abs=1e-4) == value(
            model.props[1].mole_frac_phase_comp["Vap", "benzene"]
            + model.props[1].mole_frac_phase_comp["Vap", "toluene"]
            + model.props[1].mole_frac_phase_comp["Vap", "N2"]
        )

        assert model.props[1].phase_frac["Vap"].value == pytest.approx(1, abs=1e-4)
        assert model.props[1].phase_frac["Liq"].value == pytest.approx(0, abs=1e-4)

        assert pytest.approx(
            model.props[1].mole_frac_comp["benzene"].value, abs=1e-4
        ) == value(
            model.props[1].mole_frac_phase_comp["Vap", "benzene"]
            * model.props[1].phase_frac["Vap"]
            + model.props[1].mole_frac_phase_comp["Liq", "benzene"]
            * model.props[1].phase_frac["Liq"]
        )
        assert pytest.approx(
            model.props[1].mole_frac_comp["toluene"].value, abs=1e-4
        ) == value(
            model.props[1].mole_frac_phase_comp["Vap", "toluene"]
            * model.props[1].phase_frac["Vap"]
            + model.props[1].mole_frac_phase_comp["Liq", "toluene"]
            * model.props[1].phase_frac["Liq"]
        )
        assert pytest.approx(
            model.props[1].mole_frac_comp["N2"].value, abs=1e-4
        ) == value(
            model.props[1].mole_frac_phase_comp["Vap", "N2"]
            * model.props[1].phase_frac["Vap"]
        )

    @pytest.mark.unit
    @pytest.mark.ui
    def test_report(self, model):
        model.props[1].report()