package spatialaccagent.generated

import spatialaccagent.templates._

object GeneratedDesignParams {
  val designId: String = "tinyllama_1_1b_seq32_gpt61_20261107"
  val modelType: String = "llama"
  val targetMaxSeqLen: Int = 32
  val clockTargetMHz: Int = 0
  val inputBits: Int = 8
  val elemBits: Int = 8
  val outputBits: Int = 8
  val weightBits: Int = 4
  val accBits: Int = 32
  val integerMode: Boolean = true
  val scaleBits: Int = 32
  val scaleShift: Int = 31
  val roundingMode: String = "nearest_even"
  val saturationEnabled: Boolean = true
  val lanes: Int = 16
  val computeArrayRows: Int = 8
  val computeArrayCols: Int = 32
  val computeBackend: String = "integer_dsp"
  val weightMemory: String = "xpm_uram"
  val activationMemory: String = "xpm_bram"
  val fifoMemory: String = "xpm_bram"
  val largeCacheMemory: String = "xpm_uram"
  val fifoDepth: Int = 32
  val weightBanks: Int = 1
  val activationBanks: Int = 4
  val weightBanksByRole: Map[String, Int] = Map("weight" -> 1, "weight_attn_out" -> 1, "weight_mlp_down" -> 1, "weight_mlp_gate" -> 1, "weight_mlp_up" -> 1, "weight_qkv" -> 1)
  val burstBeats: Int = 1
  val pipelineDepth: Int = 1
  val cacheTileWords: Int = 256
  val cacheTileCount: Int = 2
  val cacheRefillDataWidthBits: Int = 512
  val boardAxiDataWidthBits: Int = 512
  val crossTokenReuseTokens: Int = 16
  val attentionOutputCrossTokenReuseTokens: Int = 1
  // Materialize the reuse control before any PhysicalImplementation call or
  // parameter construction. Keep this declaration independent of the case
  // class parameter family so every generated complete top has the same
  // concrete configuration symbol.
  // This declaration is intentionally emitted before every physical
  // configuration call and before construction of the selected block-family
  // parameter object. It is a concrete Stage-4 value, never a model-family
  // default or a later forward reference.
  require(crossTokenReuseTokens > 0, "generated cross-token reuse must be positive")
  require(attentionOutputCrossTokenReuseTokens > 0, "generated attention output reuse must be positive")
  // Materialize every physical control as a concrete generated value before
  // invoking PhysicalImplementation or constructing any operator parameter.
  // Complete-top elaboration must not depend on Scala initialization order.
  // Declare the selected controls before any PhysicalImplementation call.
  // Scala object initialization is ordered, and generated complete-top
  // compilation must see concrete values rather than an unresolved forward
  // reference. The selected width is the discovered board payload; 32-bit
  // compatibility payloads are not admitted by this generated path.
  // Materialize the selected reuse context before any generated parameter
  // construction or PhysicalImplementation configuration. This declaration is
  // intentionally concrete in every generated design; it must not depend on
  // a later case-class field or on Scala initialization-order inference.
  // Materialize the selected reuse control directly from the promoted Stage-4
  // binding before any physical configuration or parameter construction. Keep
  // the public name concrete here: generated complete-top elaboration must not
  // depend on a forward reference or a model-family case-class default.
  val generatedCrossTokenReuseTokens: Int = crossTokenReuseTokens
  val selectedCrossTokenReuseTokensFromConfig: Int = crossTokenReuseTokens
  require(crossTokenReuseTokens > 0, "generated cross-token reuse must be positive")
  // These are the authoritative generated physical controls. Both the block
  // family and the aggregate service use these concrete materialized values.
  val configuredRefillDataWidthBits: Int = cacheRefillDataWidthBits
  val configuredCrossTokenReuseTokens: Int = crossTokenReuseTokens
  require(configuredRefillDataWidthBits == boardAxiDataWidthBits,
    "generated refill width must equal the discovered board AXI payload")
  val selectedCrossTokenReuseTokens: Int = configuredCrossTokenReuseTokens
  val refillDataWidthBits: Int = configuredRefillDataWidthBits
  val selectedRefillDataWidthBits: Int = configuredRefillDataWidthBits
  val materializedCacheTileWords: Int = cacheTileWords
  val materializedCacheTileCount: Int = cacheTileCount
  val materializedRefillDataWidthBits: Int = selectedRefillDataWidthBits
  val materializedCrossTokenReuseTokens: Int = selectedCrossTokenReuseTokens
  require(materializedRefillDataWidthBits == boardAxiDataWidthBits, "generated refill width must equal the discovered board AXI payload")
  require(materializedCrossTokenReuseTokens == crossTokenReuseTokens, "generated reuse configuration did not reach materialization")
  // Use the already declared materialized values here rather than referring
  // to a later or conditionally emitted symbol. This keeps GeneratedDesignParams
  // valid for every generic block family during complete-top compilation.
  // Pass the promoted Stage-4 literals directly into the physical configuration
  // calls. This avoids a Scala initialization/forward-reference dependency in
  // generated complete-top sources while retaining the named materialized
  // controls above for all downstream parameter families.
  PhysicalImplementation.configureRefillDataWidth(512)
  PhysicalImplementation.configureCrossTokenReuse(16)
  PhysicalImplementation.configureAttentionOutputCrossTokenReuse(1)
  PhysicalImplementation.configureNumericPolicy(
    weightBits, elemBits, accBits, scaleBits, scaleShift, roundingMode, saturationEnabled
  )
  val operatorSequence: Seq[String] = Seq("rms_norm_1", "self_attention", "residual_add_1", "rms_norm_2", "mlp_gate_proj", "mlp_up_proj", "activation_mul", "mlp_down_proj", "residual_add_2")
  val stageIds: Seq[String] = Seq("stage_00_rms_norm_1", "stage_01_self_attention", "stage_02_residual_add_1", "stage_03_rms_norm_2", "stage_04_mlp_gate_proj", "stage_05_mlp_up_proj", "stage_06_activation_mul", "stage_07_mlp_down_proj", "stage_08_residual_add_2")
  val params = LlamaStyleBlockParams(batchSize = 32, computeArrayCols = 32, computeArrayRows = 8, elemBits = 8, headDim = 64, hiddenSize = 2048, inputBits = 8, intermediateSize = 5632, kvHeads = 4, lanes = 16, maxSeqLen = 32, outputBits = 8, qHeads = 32, weightBits = 4, accBits = 32, integerMode = true, cacheTileWords = 256, cacheTileCount = 2, refillDataWidthBits = 512, crossTokenReuseTokens = 16)
}
