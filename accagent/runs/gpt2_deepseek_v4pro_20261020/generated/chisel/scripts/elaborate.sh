#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
sbt --no-server --batch --supershell=false "runMain spatialaccagent.generated.ElaborateGeneratedAccelerator"
sbt --no-server --batch --supershell=false "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop"
sbt --no-server --batch --supershell=false "runMain spatialaccagent.generated.ElaborateGeneratedAcceleratorVivado"
sbt --no-server --batch --supershell=false "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTopVivado"
