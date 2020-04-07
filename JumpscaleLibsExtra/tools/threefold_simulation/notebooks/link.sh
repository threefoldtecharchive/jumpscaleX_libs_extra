#!/usr/bin/env bash
set -ex
cd /sandbox/code/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks
rm -rf code
mkdir -p code
cd code
ln ../../NodesBatch.py NodesBatch.py
ln ../../BillOfMaterial.py BillOfMaterial.py
ln ../../SimulatorBase.py SimulatorBase.py
ln ../../SimulatorConfig.py SimulatorConfig.py
ln ../../TFGridSimulator.py TFGridSimulator.py
ln ../../TFGridSimulatorFactory.py TFGridSimulatorFactory.py
