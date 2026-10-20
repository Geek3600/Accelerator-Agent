package spatialaccagent.generated

object GeneratedContractCheck extends App {
  val p = GeneratedDesignParams.params
  require(p.hiddenSize > 0, "hiddenSize must be positive")
  require(p.intermediateSize > 0, "intermediateSize must be positive")
  require(p.lanes > 0, "lanes must be positive")
  require(p.hiddenSize % p.lanes == 0, "hiddenSize must be divisible by lanes")
  require(GeneratedDesignParams.computeArrayRows > 0, "computeArrayRows must be positive")
  require(GeneratedDesignParams.computeArrayCols > 0, "computeArrayCols must be positive")
  require(GeneratedDesignParams.computeArrayRows <= p.lanes && p.lanes % GeneratedDesignParams.computeArrayRows == 0, "computeArrayRows must tile lanes")
  require(
    (GeneratedDesignParams.computeArrayCols <= p.lanes && p.lanes % GeneratedDesignParams.computeArrayCols == 0) ||
      (GeneratedDesignParams.computeArrayCols > p.lanes && GeneratedDesignParams.computeArrayCols % p.lanes == 0),
    "computeArrayCols must tile lanes or combine complete input lane groups"
  )
  require((GeneratedDesignParams.computeArrayCols & (GeneratedDesignParams.computeArrayCols - 1)) == 0, "computeArrayCols must be a power of two")
  require(p.inputBits == p.outputBits, "block ingress, egress, and residual path must use the same width")
  require(p.elemBits <= p.inputBits, "internal element width must not exceed block stream width")
  if (GeneratedDesignParams.integerMode) {
    require(GeneratedDesignParams.weightBits == 4, "W4A8 matrix storage must use signed INT4")
    require(GeneratedDesignParams.elemBits == 8, "W4A8 activation storage must use signed INT8")
    require(GeneratedDesignParams.accBits == 32, "W4A8 accumulation and bias must use signed INT32")
  }
  require(GeneratedDesignParams.fifoDepth > 0, "fifoDepth must be positive")
  require(GeneratedDesignParams.weightBanks > 0, "weightBanks must be positive")
  require(GeneratedDesignParams.activationBanks > 0, "activationBanks must be positive")
  require(GeneratedDesignParams.weightBanksByRole.values.forall(_ > 0), "weightBanksByRole values must be positive")
  require(GeneratedDesignParams.burstBeats > 0, "burstBeats must be positive")
  require(GeneratedDesignParams.pipelineDepth > 0, "pipelineDepth must be positive")
  require(GeneratedDesignParams.cacheRefillDataWidthBits >= 64 && GeneratedDesignParams.cacheRefillDataWidthBits % 32 == 0 && (GeneratedDesignParams.cacheRefillDataWidthBits & (GeneratedDesignParams.cacheRefillDataWidthBits - 1)) == 0, "new generated designs must use a physically supported full-beat DDR refill payload")
  require(GeneratedDesignParams.cacheRefillDataWidthBits == GeneratedDesignParams.boardAxiDataWidthBits, "generated refill payload must equal the discovered board AXI width")
  require(GeneratedDesignParams.configuredRefillDataWidthBits == GeneratedDesignParams.refillDataWidthBits, "selected refill width must reach the generated configuration")
  require(GeneratedDesignParams.configuredCrossTokenReuseTokens == GeneratedDesignParams.crossTokenReuseTokens, "selected cross-token reuse must reach the generated configuration")
  require(GeneratedDesignParams.materializedRefillDataWidthBits == GeneratedDesignParams.cacheRefillDataWidthBits, "materialized refill width must equal the selected cache payload")
  require(GeneratedDesignParams.materializedCrossTokenReuseTokens == GeneratedDesignParams.crossTokenReuseTokens, "materialized reuse must equal the selected reuse context")
  println(
    s"GeneratedContractCheck pass: hidden=${p.hiddenSize}, intermediate=${p.intermediateSize}, lanes=${p.lanes}, bits=${p.inputBits}/${p.elemBits}/${p.outputBits}"
  )
}
