#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .sbt/boot .ivy2 .cache/coursier
export SBT_OPTS="${SBT_OPTS:-} -Dsbt.global.base=$PWD/.sbt -Dsbt.boot.directory=$PWD/.sbt/boot -Dsbt.ivy.home=$PWD/.ivy2 -Dsbt.server.autostart=false -Dsbt.server.forcestart=false"
export COURSIER_CACHE="${COURSIER_CACHE:-$PWD/.cache/coursier}"
sbt --no-server --batch --supershell=false Compile/compile
sbt --no-server --batch --supershell=false "runMain spatialaccagent.generated.GeneratedContractCheck"
sbt --no-server --batch --supershell=false "runMain spatialaccagent.generated.ElaborateGeneratedAccelerator"
sbt --no-server --batch --supershell=false "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop"
sbt --no-server --batch --supershell=false "runMain spatialaccagent.generated.ElaborateGeneratedAcceleratorVivado"
sbt --no-server --batch --supershell=false "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTopVivado"
