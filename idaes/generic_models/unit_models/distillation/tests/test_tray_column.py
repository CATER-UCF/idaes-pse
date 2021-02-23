##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Tests for tray column unit model (single feed tray, no side draws).

Author: Jaffer Ghouse
"""
import pytest
from pyomo.environ import (ConcreteModel, TerminationCondition,
                           SolverStatus, value)

from idaes.core import FlowsheetBlock
from idaes.generic_models.unit_models.distillation import TrayColumn
from idaes.generic_models.unit_models.distillation.condenser \
    import CondenserType, TemperatureSpec
from idaes.generic_models.properties.activity_coeff_models.\
    BTX_activity_coeff_VLE import BTXParameterBlock
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes.core.util.testing import \
    PhysicalParameterTestBlock, initialization_tester
from idaes.core.util import get_default_solver

from idaes.generic_models.properties.core.generic.generic_property \
    import GenericParameterBlock

from idaes.generic_models.properties.core.examples.BT_ideal \
    import configuration

# -----------------------------------------------------------------------------
# Get default solver for testing
solver = get_default_solver()


@pytest.mark.unit
def test_config():

    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})
    m.fs.properties = PhysicalParameterTestBlock()

    m.fs.unit = TrayColumn(default={
                           "number_of_trays": 10,
                           "feed_tray_location": 5,
                           "condenser_type": CondenserType.totalCondenser,
                           "condenser_temperature_spec":
                               TemperatureSpec.customTemperature,
                           "property_package": m.fs.properties,
                           "has_heat_transfer": False,
                           "has_pressure_change": False})

    assert len(m.fs.unit.config) == 12

    assert m.fs.unit.feed_tray.config.is_feed_tray

    assert hasattr(m.fs.unit, "condenser")
    assert hasattr(m.fs.unit, "reboiler")

    assert hasattr(m.fs.unit, "rectification_section")
    assert hasattr(m.fs.unit, "stripping_section")


class TestBTXIdeal():
    @pytest.fixture(scope="class")
    def btx_ftpz(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})
        m.fs.properties = BTXParameterBlock(default={"valid_phase":
                                                     ('Liq', 'Vap'),
                                                     "activity_coeff_model":
                                                     "Ideal"})

        m.fs.unit = TrayColumn(default={
                               "number_of_trays": 10,
                               "feed_tray_location": 5,
                               "condenser_type": CondenserType.totalCondenser,
                               "condenser_temperature_spec":
                                   TemperatureSpec.atBubblePoint,
                               "property_package": m.fs.properties,
                               "has_heat_transfer": False,
                               "has_pressure_change": False})

        # Inlet feed conditions
        m.fs.unit.feed.flow_mol.fix(40)
        m.fs.unit.feed.temperature.fix(368)
        m.fs.unit.feed.pressure.fix(101325)
        m.fs.unit.feed.mole_frac_comp[0, "benzene"].fix(0.5)
        m.fs.unit.feed.mole_frac_comp[0, "toluene"].fix(0.5)

        # unit level inputs
        m.fs.unit.condenser.reflux_ratio.fix(1.4)
        m.fs.unit.condenser.condenser_pressure.fix(101325)

        m.fs.unit.reboiler.boilup_ratio.fix(1.3)

        assert degrees_of_freedom(m.fs.unit) == 0

        return m

    @pytest.fixture(scope="class")
    def btx_fctp(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})
        m.fs.properties = BTXParameterBlock(default={"valid_phase":
                                                     ('Liq', 'Vap'),
                                                     "activity_coeff_model":
                                                     "Ideal",
                                                     "state_vars": "FcTP"})

        m.fs.unit = TrayColumn(default={
                               "number_of_trays": 10,
                               "feed_tray_location": 5,
                               "condenser_type": CondenserType.totalCondenser,
                               "condenser_temperature_spec":
                                   TemperatureSpec.atBubblePoint,
                               "property_package": m.fs.properties,
                               "has_heat_transfer": False,
                               "has_pressure_change": False})

        # Inlet feed conditions
        m.fs.unit.feed.flow_mol_comp[0, "benzene"].fix(20)
        m.fs.unit.feed.flow_mol_comp[0, "toluene"].fix(20)
        m.fs.unit.feed.temperature.fix(368)
        m.fs.unit.feed.pressure.fix(101325)

        # unit level inputs
        m.fs.unit.condenser.reflux_ratio.fix(1.4)
        m.fs.unit.condenser.condenser_pressure.fix(101325)

        m.fs.unit.reboiler.boilup_ratio.fix(1.3)

        assert degrees_of_freedom(m) == 0

        return m

    @pytest.mark.unit
    def test_build(self, btx_ftpz, btx_fctp):
        assert len(btx_ftpz.fs.unit.config) == 12

        assert btx_ftpz.fs.unit.feed_tray.config.is_feed_tray

        assert hasattr(btx_ftpz.fs.unit, "condenser")
        assert hasattr(btx_ftpz.fs.unit, "reboiler")

        assert hasattr(btx_ftpz.fs.unit, "rectification_section")
        assert hasattr(btx_ftpz.fs.unit, "stripping_section")

        assert len(btx_fctp.fs.unit.config) == 12

        assert btx_fctp.fs.unit.feed_tray.config.is_feed_tray

        assert hasattr(btx_fctp.fs.unit, "condenser")
        assert hasattr(btx_fctp.fs.unit, "reboiler")

        assert hasattr(btx_fctp.fs.unit, "rectification_section")
        assert hasattr(btx_fctp.fs.unit, "stripping_section")

    @pytest.mark.solver
    @pytest.mark.component
    def test_initialize(self, btx_ftpz, btx_fctp):
        initialization_tester(btx_ftpz)
        initialization_tester(btx_fctp)

    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.component
    def test_solve(self, btx_ftpz, btx_fctp):
        results = solver.solve(btx_ftpz)

        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

        results = solver.solve(btx_fctp)

        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.component
    def test_solution(self, btx_ftpz, btx_fctp):

        # Distillate port - btx_ftpz
        assert (pytest.approx(18.978, rel=1e-2) ==
                value(btx_ftpz.fs.unit.condenser.distillate.flow_mol[0]))
        assert (pytest.approx(0.8882, rel=1e-2) ==
                value(btx_ftpz.fs.unit.condenser.
                      distillate.mole_frac_comp[0, "benzene"]))
        assert (pytest.approx(0.1118, rel=1e-2) ==
                value(btx_ftpz.fs.unit.condenser.
                      distillate.mole_frac_comp[0, "toluene"]))
        assert (pytest.approx(355.642, abs=1e-2) ==
                value(btx_ftpz.fs.unit.condenser.
                      distillate.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_ftpz.fs.unit.condenser.
                      distillate.pressure[0]))

        # Bottoms port - btx_ftpz
        assert (pytest.approx(21.021, rel=1e-2) ==
                value(btx_ftpz.fs.unit.reboiler.bottoms.flow_mol[0]))
        assert (pytest.approx(0.1495, rel=1e-2) ==
                value(btx_ftpz.fs.unit.reboiler.
                      bottoms.mole_frac_comp[0, "benzene"]))
        assert (pytest.approx(0.8504, rel=1e-3) ==
                value(btx_ftpz.fs.unit.reboiler.
                      bottoms.mole_frac_comp[0, "toluene"]))
        assert (pytest.approx(377.337, abs=1e-2) ==
                value(btx_ftpz.fs.unit.reboiler.
                      bottoms.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_ftpz.fs.unit.reboiler.
                      bottoms.pressure[0]))

        # Distillate port - btx_fctp
        assert (pytest.approx(16.856, rel=1e-2) ==
                value(btx_fctp.fs.unit.condenser.
                      distillate.flow_mol_comp[0, "benzene"]))
        assert (pytest.approx(2.121, rel=1e-2) ==
                value(btx_fctp.fs.unit.condenser.
                      distillate.flow_mol_comp[0, "toluene"]))
        assert (pytest.approx(355.638, abs=1e-2) ==
                value(btx_fctp.fs.unit.condenser.
                      distillate.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_fctp.fs.unit.condenser.
                      distillate.pressure[0]))

        # # Bottoms port - btx_fctp
        assert (pytest.approx(3.179, rel=1e-2) ==
                value(btx_fctp.fs.unit.reboiler.
                      bottoms.flow_mol_comp[0, "benzene"]))
        assert (pytest.approx(17.876, rel=1e-3) ==
                value(btx_fctp.fs.unit.reboiler.
                      bottoms.flow_mol_comp[0, "toluene"]))
        assert (pytest.approx(377.28, abs=1e-2) ==
                value(btx_fctp.fs.unit.reboiler.
                      bottoms.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_fctp.fs.unit.reboiler.
                      bottoms.pressure[0]))


class TestBTXIdealGeneric():
    @pytest.fixture(scope="class")
    def btx_ftpz_generic(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})
        m.fs.properties = GenericParameterBlock(default=configuration)

        m.fs.unit = TrayColumn(default={
                               "number_of_trays": 10,
                               "feed_tray_location": 5,
                               "condenser_type": CondenserType.totalCondenser,
                               "condenser_temperature_spec":
                                   TemperatureSpec.atBubblePoint,
                               "property_package": m.fs.properties,
                               "has_heat_transfer": False,
                               "has_pressure_change": False})

        # Inlet feed conditions
        m.fs.unit.feed.flow_mol.fix(100)
        m.fs.unit.feed.temperature.fix(368)
        m.fs.unit.feed.pressure.fix(101325)
        m.fs.unit.feed.mole_frac_comp[0, "benzene"].fix(0.5)
        m.fs.unit.feed.mole_frac_comp[0, "toluene"].fix(0.5)

        # unit level inputs
        m.fs.unit.condenser.reflux_ratio.fix(1.4)
        m.fs.unit.condenser.condenser_pressure.fix(101325)

        m.fs.unit.reboiler.boilup_ratio.fix(1.3)

        assert degrees_of_freedom(m) == 0

        return m

    @pytest.mark.unit
    @pytest.mark.generic
    def test_build(self, btx_ftpz_generic):
        assert len(btx_ftpz_generic.fs.unit.config) == 12

        assert btx_ftpz_generic.fs.unit.feed_tray.config.is_feed_tray

        assert hasattr(btx_ftpz_generic.fs.unit, "condenser")
        assert hasattr(btx_ftpz_generic.fs.unit, "reboiler")

        assert hasattr(btx_ftpz_generic.fs.unit, "rectification_section")
        assert hasattr(btx_ftpz_generic.fs.unit, "stripping_section")

        assert len(btx_ftpz_generic.fs.unit.config) == 12

    @pytest.mark.solver
    @pytest.mark.generic
    @pytest.mark.component
    def test_initialize(self, btx_ftpz_generic):
        initialization_tester(btx_ftpz_generic)

    @pytest.mark.solver
    @pytest.mark.generic
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.component
    def test_solve(self, btx_ftpz_generic):
        results = solver.solve(btx_ftpz_generic)

        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

    @pytest.mark.solver
    @pytest.mark.generic
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    @pytest.mark.component
    def test_solution(self, btx_ftpz_generic):

        # Distillate port - btx_ftpz
        assert (pytest.approx(49.28, rel=1e-2) ==
                value(btx_ftpz_generic.fs.unit.condenser.distillate.flow_mol[0]))
        assert (pytest.approx(0.8784, rel=1e-2) ==
                value(btx_ftpz_generic.fs.unit.condenser.
                      distillate.mole_frac_comp[0, "benzene"]))
        assert (pytest.approx(0.1215, rel=1e-2) ==
                value(btx_ftpz_generic.fs.unit.condenser.
                      distillate.mole_frac_comp[0, "toluene"]))
        assert (pytest.approx(355.853, abs=1e-2) ==
                value(btx_ftpz_generic.fs.unit.condenser.
                      distillate.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_ftpz_generic.fs.unit.condenser.
                      distillate.pressure[0]))

        # Bottoms port - btx_ftpz
        assert (pytest.approx(50.711, rel=1e-2) ==
                value(btx_ftpz_generic.fs.unit.reboiler.bottoms.flow_mol[0]))
        assert (pytest.approx(0.1322, rel=1e-2) ==
                value(btx_ftpz_generic.fs.unit.reboiler.
                      bottoms.mole_frac_comp[0, "benzene"]))
        assert (pytest.approx(0.8677, rel=1e-3) ==
                value(btx_ftpz_generic.fs.unit.reboiler.
                      bottoms.mole_frac_comp[0, "toluene"]))
        assert (pytest.approx(378.0433, abs=1e-2) ==
                value(btx_ftpz_generic.fs.unit.reboiler.
                      bottoms.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_ftpz_generic.fs.unit.reboiler.
                      bottoms.pressure[0]))
