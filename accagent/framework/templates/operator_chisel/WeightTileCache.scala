package spatialaccagent.templates

import chisel3._
import chisel3.util._

/** Generic ready/valid DDR tile request emitted by a bounded weight cache. */
class WeightTileRequest(
  routeIdBits: Int,
  layerIndexBits: Int,
  tileIndexBits: Int,
  ddrAddrBits: Int,
  tileWordCountBits: Int
) extends Bundle {
  val routeId = UInt(routeIdBits.W)
  val layerIndex = UInt(layerIndexBits.W)
  val tileIndex = UInt(tileIndexBits.W)
  val shadowBank = Bool()
  val tileWordCount = UInt(tileWordCountBits.W)
  val ddrWordAddress = UInt(ddrAddrBits.W)
}

/** Echoed ready/valid DDR tile response consumed by a bounded weight cache. */
class WeightTileResponse(
  routeIdBits: Int,
  layerIndexBits: Int,
  tileIndexBits: Int,
  ddrAddrBits: Int,
  tileWordIndexBits: Int,
  dataWidthBits: Int = 512,
  validWordsBits: Int = 5
) extends Bundle {
  require(PhysicalImplementation.isSupportedRefillDataWidth(dataWidthBits), "production DDR response width must be a physically supported full-beat payload")
  val routeId = UInt(routeIdBits.W)
  val layerIndex = UInt(layerIndexBits.W)
  val tileIndex = UInt(tileIndexBits.W)
  val shadowBank = Bool()
  // wordIndex is the first 32-bit image-word index in this response beat.
  // validWords counts contiguous little-endian 32-bit words in data; the
  // final beat may contain fewer words than dataWidthBits/32.
  val wordIndex = UInt(tileWordIndexBits.W)
  val validWords = UInt(validWordsBits.W)
  val data = UInt(dataWidthBits.W)
  val last = Bool()
}

/**
  * Physically bounded active/shadow weight-tile storage.
  *
  * The addressed legacy loader remains available for compatibility, but cache
  * misses now issue a generic ready/valid DDR tile request and accept only an
  * ordered, metadata-matching tile response. A response writes only the
  * inactive bank. A tile becomes valid only after its final response beat is
  * accepted. The cache never allocates logicalDepth words on chip: its
  * physical footprint is exactly two banks of cacheTileWords*cacheTileCount
  * words.
  */
class WeightTileServiceIO(
  refillDataWidthBits: Int = PhysicalImplementation.resolveRefillDataWidthBits(512)
) extends Bundle {
  require(PhysicalImplementation.isSupportedRefillDataWidth(refillDataWidthBits), "production refill width must be a physically supported full-beat payload")
  private val refillWords = refillDataWidthBits / 32
  private val validWordsBits = log2Ceil(refillWords + 1 max 2)
  val routeId = Input(UInt(16.W))
  val layerIndex = Input(UInt(16.W))
  val ddrBaseWord = Input(UInt(64.W))
  val routeWordOffset = Input(UInt(64.W))
  val layerStrideWords = Input(UInt(64.W))
  val request = Decoupled(new WeightTileRequest(16, 16, 16, 64, 32))
  val response = Flipped(Decoupled(new WeightTileResponse(16, 16, 16, 64, 32, refillDataWidthBits, validWordsBits)))
  val tileComplete = Output(Bool())
  val activeBank = Output(Bool())
  val shadowBank = Output(Bool())
  val prefetchCommit = Output(Bool())
}

class WeightTileServiceMux(
  clientCount: Int,
  refillDataWidthBits: Int = PhysicalImplementation.resolveRefillDataWidthBits(512)
) extends Module {
  require(clientCount > 0, "weight tile service mux requires at least one client")
  require(PhysicalImplementation.isSupportedRefillDataWidth(refillDataWidthBits), "production refill width must be a physically supported full-beat payload")
  private val validWordsBits = log2Ceil(refillDataWidthBits / 32 + 1 max 2)

  val io = IO(new Bundle {
    val clientRequests = Flipped(Vec(clientCount, Decoupled(new WeightTileRequest(16, 16, 16, 64, 32))))
    val clientResponses = Vec(clientCount, Decoupled(new WeightTileResponse(16, 16, 16, 64, 32, refillDataWidthBits, validWordsBits)))
    val clientTileComplete = Input(Vec(clientCount, Bool()))
    val clientPrefetchCommit = Input(Vec(clientCount, Bool()))
    val request = Decoupled(new WeightTileRequest(16, 16, 16, 64, 32))
    val response = Flipped(Decoupled(new WeightTileResponse(16, 16, 16, 64, 32, refillDataWidthBits, validWordsBits)))
    val tileComplete = Output(Bool())
    val activeBank = Output(Bool())
    val shadowBank = Output(Bool())
    val prefetchCommit = Output(Bool())
  })

  private val ownerBits = log2Ceil(clientCount max 2)
  private val owner = RegInit(0.U(ownerBits.W))
  private val ownerValid = RegInit(false.B)
  private val requestValid = VecInit(io.clientRequests.map(_.valid))
  private val selected = PriorityEncoderOH(requestValid)
  private val selectedIndex = PriorityEncoder(requestValid)

  io.request.valid := requestValid.asUInt.orR && !ownerValid
  io.request.bits := Mux1H(selected, io.clientRequests.map(_.bits))
  for (index <- 0 until clientCount) {
    io.clientRequests(index).ready := io.request.ready && selected(index) && !ownerValid
    io.clientResponses(index).valid := io.response.valid && ownerValid && owner === index.U
    io.clientResponses(index).bits := io.response.bits
  }
  io.response.ready := ownerValid && Mux1H(
    VecInit((0 until clientCount).map(index => owner === index.U)),
    io.clientResponses.map(_.ready)
  )

  io.tileComplete := io.clientTileComplete.asUInt.orR
  io.prefetchCommit := io.clientPrefetchCommit.asUInt.orR
  io.activeBank := false.B
  io.shadowBank := true.B

  when(io.request.fire) {
    owner := selectedIndex
    ownerValid := true.B
  }
  // A request owns the response channel for the complete tile, not just its
  // first accepted word. Keep ownership until the final beat is accepted.
  when(io.response.fire && io.response.bits.last) {
    ownerValid := false.B
  }
}

class WeightTileCache(
  logicalDepth: Int,
  width: Int,
  logicalAddrBits: Int,
  cacheTileWords: Int,
  cacheTileCount: Int,
  role: String = "weight",
  refillDataWidthBits: Int = PhysicalImplementation.resolveRefillDataWidthBits(512),
  routeIdBits: Int = 16,
  layerIndexBits: Int = 16,
  ddrAddrBits: Int = 64
) extends Module {
  require(logicalDepth > 0, "logical weight depth must be positive")
  require(width > 0, "weight tile width must be positive")
  require(logicalAddrBits > 0, "logical weight address width must be positive")
  require(cacheTileWords > 0, "cache tile word capacity must be positive")
  require(cacheTileCount > 0, "cache tile count must be positive")
  require(width % 32 == 0, "DDR tile service requires cache words made from complete 32-bit image words")
  require(PhysicalImplementation.isSupportedRefillDataWidth(refillDataWidthBits), "production refill width must be a physically supported full-beat payload")
  require(routeIdBits > 0 && layerIndexBits > 0 && ddrAddrBits > 0, "tile metadata widths must be positive")

  private val cacheWords = cacheTileWords * cacheTileCount
  private val cacheAddrBits = log2Ceil(cacheWords max 2)
  private val logicalTileCount = (logicalDepth + cacheTileWords - 1) / cacheTileWords
  // Service metadata widths are fixed by the shared DDR tile ABI. Cache-local
  // dimensions remain parameterized, while request/response clients and muxes
  // can be connected without implicit Chisel width truncation.
  private val tileIndexBits = 16
  private val imageWordsPerCacheWord = width / 32
  private val imageWordsPerResponse = refillDataWidthBits / 32
  // One independent XPM write lane per possible 32-bit cache-word endpoint in
  // a refill beat. Thus a wide response can commit every complete cache word
  // in that beat instead of serializing its image words over later cycles.
  // A wide response can complete several cache words only when a cache word
  // is narrower than the selected payload.  Do not allocate one full-width
  // XPM memory per 32-bit image word: the physical write-lane count is the
  // maximum number of cache words touched by one accepted response beat.
  private def integerGcd(a: Int, b: Int): Int = if (b == 0) a else integerGcd(b, a % b)
  // Beat starts advance by imageWordsPerResponse. Size the physical write
  // lanes for the maximum number of complete cache words reachable across
  // that exact phase cycle, rather than allocating one lane for every 32-bit
  // word in the payload. Wide matrix words commonly need only one write lane.
  private val responseWritePeriod = imageWordsPerCacheWord / integerGcd(imageWordsPerCacheWord, imageWordsPerResponse)
  private val responseWriteLanes = math.max(
    1,
    (0 until responseWritePeriod).map { beat =>
      val phase = (beat * imageWordsPerResponse) % imageWordsPerCacheWord
      (phase + imageWordsPerResponse + imageWordsPerCacheWord - 1) / imageWordsPerCacheWord
    }.max
  )
  private val cacheLaneDepth = (cacheWords + responseWriteLanes - 1) / responseWriteLanes
  // Active and shadow remain distinct logical banks, but occupy disjoint
  // address regions of the same XPM per write lane. Its independent read and
  // write ports sustain an active-bank read alongside a shadow-bank refill.
  private val cacheStorageDepth = 2 * cacheLaneDepth
  private val cacheStorageAddrBits = log2Ceil(cacheStorageDepth max 2)
  private val cacheTileImageWords = cacheTileWords * imageWordsPerCacheWord
  private val tileWordIndexBits = 32
  private val tileWordCountBits = 32
  private val validWordsBits = log2Ceil(imageWordsPerResponse + 1 max 2)
  // The request address always advances by this full physical tile stride.
  // A tail tile may report fewer valid response words, but that shortened
  // response count must never alter the address of the next tile.
  private val fixedTileStrideWords = cacheTileImageWords
  require(fixedTileStrideWords > 0, "fixed tile stride must be positive")
  require(validWordsBits >= 1, "validWords metadata must be representable")

  val io = IO(new Bundle {
    val writeEn = Input(Bool())
    val writeAddr = Input(UInt(logicalAddrBits.W))
    val writeData = Input(UInt(width.W))
    val readEn = Input(Bool())
    val readAddr = Input(UInt(logicalAddrBits.W))
    val readReady = Output(Bool())
    val readHit = Output(Bool())
    val readData = Output(UInt(width.W))

    val routeId = Input(UInt(routeIdBits.W))
    val layerIndex = Input(UInt(layerIndexBits.W))
    val ddrBaseWord = Input(UInt(ddrAddrBits.W))
    val routeWordOffset = Input(UInt(ddrAddrBits.W))
    val layerStrideWords = Input(UInt(ddrAddrBits.W))
    val tileRequest = Decoupled(new WeightTileRequest(routeIdBits, layerIndexBits, tileIndexBits, ddrAddrBits, tileWordCountBits))
    val tileResponse = Flipped(Decoupled(new WeightTileResponse(routeIdBits, layerIndexBits, tileIndexBits, ddrAddrBits, tileWordIndexBits, refillDataWidthBits, validWordsBits)))
    val tileComplete = Output(Bool())

    // Compute holds its selected bank for the complete operation. Refill may
    // continue in the other bank, but ownership cannot switch until compute
    // releases the bank.
    val computeHold = Input(Bool())
    val computeBank = Input(Bool())

    val activeBank = Output(Bool())
    val shadowBank = Output(Bool())
    val prefetchCommit = Output(Bool())
  })

  private val activeBankReg = RegInit(false.B)
  // Weight-bank ownership is independent of activation ping-pong parity. Lock
  // the physical bank selected by the first resident compute read; otherwise
  // a later miss could refill the very bank whose tile compute is consuming.
  private val heldComputeBankReg = RegInit(false.B)
  private val computeBankLockedReg = RegInit(false.B)
  private val ownerBank = Mux(
    io.computeHold && computeBankLockedReg,
    heldComputeBankReg,
    activeBankReg
  )
  // Interleaved physical lanes permit responseWriteLanes complete cache words
  // to be written in parallel. Logical cache address A maps to lane A%N and
  // row floor(A/N); reads select that same lane and row.
  private val cacheStorage = Seq.tabulate(responseWriteLanes) { _ =>
    Module(new PhysicalSimpleDualPortMemory(cacheStorageDepth, width, role))
  }

  private val tileValid = Seq.tabulate(2) { _ => RegInit(VecInit(Seq.fill(cacheTileCount)(false.B))) }
  private val tileTags = Seq.tabulate(2) { _ => Reg(Vec(cacheTileCount, UInt(tileIndexBits.W))) }
  private val tileRouteTags = Seq.tabulate(2) { _ => Reg(Vec(cacheTileCount, UInt(routeIdBits.W))) }
  private val tileLayerTags = Seq.tabulate(2) { _ => Reg(Vec(cacheTileCount, UInt(layerIndexBits.W))) }

  private val missPending = RegInit(false.B)
  private val requestIssued = RegInit(false.B)
  private val expectedResponseWord = RegInit(0.U(tileWordIndexBits.W))
  private val tileAssembly = Reg(Vec(imageWordsPerCacheWord, UInt(32.W)))
  private val missTileIndex = Reg(UInt(tileIndexBits.W))
  private val missLayerIndex = Reg(UInt(layerIndexBits.W))
  private val missRouteId = Reg(UInt(routeIdBits.W))
  private val missShadowBank = Reg(Bool())
  private val missTileWordCount = Reg(UInt(tileWordCountBits.W))
  private val missDdrBaseWord = Reg(UInt(ddrAddrBits.W))
  private val missRouteWordOffset = Reg(UInt(ddrAddrBits.W))
  private val missLayerStrideWords = Reg(UInt(ddrAddrBits.W))
  private val tileCompleteReg = RegInit(false.B)

  private val readTileIndex = io.readAddr / cacheTileWords.U
  private val readTileSlotRaw = readTileIndex % cacheTileCount.U
  private val readTileSlot = AccMath.boundedIndex(readTileSlotRaw, cacheTileCount)
  private val activeHit = Mux(
    ownerBank,
    tileValid(1)(readTileSlot) && tileTags(1)(readTileSlot) === readTileIndex &&
      tileRouteTags(1)(readTileSlot) === io.routeId && tileLayerTags(1)(readTileSlot) === io.layerIndex,
    tileValid(0)(readTileSlot) && tileTags(0)(readTileSlot) === readTileIndex &&
      tileRouteTags(0)(readTileSlot) === io.routeId && tileLayerTags(0)(readTileSlot) === io.layerIndex
  )
  private val shadowHit = Mux(
    ownerBank,
    tileValid(0)(readTileSlot) && tileTags(0)(readTileSlot) === readTileIndex &&
      tileRouteTags(0)(readTileSlot) === io.routeId && tileLayerTags(0)(readTileSlot) === io.layerIndex,
    tileValid(1)(readTileSlot) && tileTags(1)(readTileSlot) === readTileIndex &&
      tileRouteTags(1)(readTileSlot) === io.routeId && tileLayerTags(1)(readTileSlot) === io.layerIndex
  )
  private val readHit = activeHit || shadowHit
  private val selectedReadBank = Mux(activeHit, ownerBank, ~ownerBank)
  private val cacheReadAddr = io.readAddr % cacheWords.U
  private val readCanProbe = !missPending && !requestIssued
  private val readProbe = io.readEn && readCanProbe

  private val legacyWriteAddr = io.writeAddr % cacheWords.U
  private val responseSlotRaw = io.tileResponse.bits.tileIndex % cacheTileCount.U
  private val responseSlot = AccMath.boundedIndex(responseSlotRaw, cacheTileCount)
  private val responseStartWord = io.tileResponse.bits.wordIndex
  private val responseValidWords = io.tileResponse.bits.validWords
  private val responseWordValues = io.tileResponse.bits.data.asTypeOf(Vec(imageWordsPerResponse, UInt(32.W)))
  private val responseBank = io.tileResponse.bits.shadowBank
  private val responseEndWord = responseStartWord + responseValidWords
  private val responseMetadataMatches =
    io.tileResponse.bits.routeId === missRouteId &&
      io.tileResponse.bits.layerIndex === missLayerIndex &&
      io.tileResponse.bits.tileIndex === missTileIndex &&
      io.tileResponse.bits.shadowBank === missShadowBank &&
      responseStartWord === expectedResponseWord &&
      responseValidWords =/= 0.U && responseValidWords <= imageWordsPerResponse.U &&
      responseEndWord <= missTileWordCount &&
      io.tileResponse.bits.last === (responseEndWord === missTileWordCount)

  // Each response-lane candidate represents the cache word ending at that
  // 32-bit image word. It combines words from this wide beat with the saved
  // partial word from the preceding beat where necessary.
  private val responseWriteCandidates = (0 until imageWordsPerResponse).map { beatLane =>
    val absoluteWord = responseStartWord + beatLane.U
    val cacheWordLane = absoluteWord % imageWordsPerCacheWord.U
    val cacheWordIndex = responseSlot * cacheTileWords.U + absoluteWord / imageWordsPerCacheWord.U
    val completesWord = beatLane.U < responseValidWords &&
      (cacheWordLane === (imageWordsPerCacheWord - 1).U || absoluteWord + 1.U === missTileWordCount)
    val assembled = Wire(Vec(imageWordsPerCacheWord, UInt(32.W)))
    for (subword <- 0 until imageWordsPerCacheWord) {
      val sourceLane = beatLane.U + subword.U - cacheWordLane
      val currentWordValid = sourceLane < responseValidWords &&
        beatLane.U + subword.U >= cacheWordLane
      assembled(subword) := Mux(
        subword.U < cacheWordLane,
        tileAssembly(subword),
        Mux(
          currentWordValid,
          responseWordValues(AccMath.boundedIndex(sourceLane, imageWordsPerResponse)),
          0.U
        )
      )
    }
    (completesWord, cacheWordIndex, assembled.asUInt)
  }

  // Once the current tile is committed, use another cache slot in the same
  // shadow bank for the next tile while compute continues to read the
  // committed tile. The cache remains physically bounded by cacheTileCount;
  // when only one slot is admitted, the next miss is demand-serviced instead
  // of overwriting the tile still owned by compute.
  private val hasNextPrefetchTile = missTileIndex =/= (logicalTileCount - 1).U
  private val nextPrefetchTile = missTileIndex + 1.U
  private val nextPrefetchWordCount = Mux(
    nextPrefetchTile === (logicalTileCount - 1).U,
    ((logicalDepth - (logicalTileCount - 1) * cacheTileWords) * imageWordsPerCacheWord).U,
    fixedTileStrideWords.U
  )

  // A miss is consumed by the DDR request path, not by the compute datapath.
  // Refill may proceed into the shadow bank while a resident active tile is
  // still read by compute; only misses are serialized behind the outstanding
  // request. Never expose stale data on a miss.
  io.readReady := readHit
  io.readHit := readHit
  private val cacheReadLane = cacheReadAddr % responseWriteLanes.U
  private val cacheReadRow = cacheReadAddr / responseWriteLanes.U
  private val cacheReadLaneReg = RegInit(0.U(log2Ceil(responseWriteLanes max 2).W))
  io.readData := Mux1H((0 until responseWriteLanes).map { lane =>
    (cacheReadLaneReg === lane.U) -> cacheStorage(lane).io.readData
  })

  io.tileRequest.valid := missPending && !requestIssued
  io.tileRequest.bits.routeId := missRouteId
  io.tileRequest.bits.layerIndex := missLayerIndex
  io.tileRequest.bits.tileIndex := missTileIndex
  io.tileRequest.bits.shadowBank := missShadowBank
  io.tileRequest.bits.tileWordCount := missTileWordCount
  // Keep every tile on the fixed physical cache-tile stride. The final tile's
  // response count may be shorter, but it must not move the address of later
  // tiles or layers.
  // This is the shared DDR tile-service contract address rule: the accepted
  // request count is the tile stride unit, not a hard-coded cache capacity.
  io.tileRequest.bits.ddrWordAddress :=
    missDdrBaseWord + missRouteWordOffset +
      (missLayerIndex * missLayerStrideWords) +
      (missTileIndex * fixedTileStrideWords.U)

  io.tileResponse.ready := missPending && requestIssued && responseMetadataMatches
  io.tileComplete := tileCompleteReg

  // The compatibility loader is never allowed to overwrite a bank owned by
  // compute. DDR refill remains the only legal update path during compute.
  val legacyWriteAccepted = io.writeEn && !io.computeHold
  val legacyCommit = legacyWriteAccepted && io.writeAddr === (logicalDepth - 1).U
  val legacyTileIndex = io.writeAddr / cacheTileWords.U
  val legacyTileSlot = AccMath.boundedIndex(legacyTileIndex % cacheTileCount.U, cacheTileCount)
  val legacyTileLast =
    legacyWriteAccepted && ((io.writeAddr === (logicalDepth - 1).U) || (io.writeAddr % cacheTileWords.U === (cacheTileWords - 1).U))
  // Write every complete logical cache word represented by an accepted wide
  // refill beat in parallel. A final partial cache word is zero-padded in
  // unused image-word lanes. Legacy single-word writes use the same
  // interleaved physical addressing without changing their data ordering.
  val responseWriteFired = io.tileResponse.fire
  val legacyLane = legacyWriteAddr % responseWriteLanes.U
  val legacyRow = legacyWriteAddr / responseWriteLanes.U
  for (lane <- 0 until responseWriteLanes) {
    val laneCandidates = responseWriteCandidates.map { candidate =>
      val selected = candidate._1 && candidate._2 % responseWriteLanes.U === lane.U
      (selected, candidate._2 / responseWriteLanes.U, candidate._3)
    }
    val responseLaneWrite = responseWriteFired && laneCandidates.map(_._1).reduce(_ || _)
    val responseLaneAddr = Mux1H(laneCandidates.map(item => item._1 -> item._2))
    val responseLaneData = Mux1H(laneCandidates.map(item => item._1 -> item._3))
    val legacyLaneWrite = legacyWriteAccepted && legacyLane === lane.U
    val writeEnable = responseLaneWrite || legacyLaneWrite
    val writeRow = Mux(responseLaneWrite, responseLaneAddr, legacyRow)
    val writeData = Mux(responseLaneWrite, responseLaneData, io.writeData)
    // Response writes target the request's shadow bank. Legacy writes retain
    // their prior inactive-bank destination. The region offset ensures the
    // single XPM's read port can serve the selected bank while its write port
    // fills the other, without changing the registered read latency.
    val writeBank = Mux(responseLaneWrite, responseBank, !ownerBank)
    val writeBase = Mux(writeBank, cacheLaneDepth.U, 0.U).pad(cacheStorageAddrBits)
    val physicalWriteAddr = writeBase + writeRow.pad(cacheStorageAddrBits)
    val readBase = Mux(selectedReadBank, cacheLaneDepth.U, 0.U).pad(cacheStorageAddrBits)
    val physicalReadAddr = readBase + cacheReadRow.pad(cacheStorageAddrBits)
    cacheStorage(lane).io.writeEn := writeEnable
    cacheStorage(lane).io.writeAddr := physicalWriteAddr
    cacheStorage(lane).io.writeData := writeData
    cacheStorage(lane).io.readEn := io.readEn && readHit && cacheReadLane === lane.U
    cacheStorage(lane).io.readAddr := physicalReadAddr
  }

  when(!io.computeHold) {
    computeBankLockedReg := false.B
  }
  when(io.computeHold && !computeBankLockedReg && io.readEn && readHit) {
    heldComputeBankReg := selectedReadBank
    computeBankLockedReg := true.B
  }

  when(io.readEn && readHit) {
    // The XPM read result is registered. Preserve the accepted lane together
    // with the accepted bank so consecutive reads to different interleaved
    // lanes cannot select the next request's lane on the response cycle.
    cacheReadLaneReg := cacheReadLane
    // A compute hold pins all reads to computeBank. Outside compute, a read of
    // a complete shadow tile is the explicit ownership handoff. Never toggle
    // the committed bank merely because a shadow tag was observed while the
    // current operation still owns the active bank.
    when(shadowHit && !io.computeHold && !missPending && !requestIssued) {
      activeBankReg := selectedReadBank
    }
  }.elsewhen(io.readEn && readCanProbe) {
    // Do not leave an evicted tag readable while its physical slot is being
    // overwritten. The requester cannot consume the refill until the final
    // response beat validates the new tag.
    when(ownerBank) {
      tileValid(0)(readTileSlot) := false.B
    }.otherwise {
      tileValid(1)(readTileSlot) := false.B
    }
    for (lane <- 0 until imageWordsPerCacheWord) {
      tileAssembly(lane) := 0.U
    }
    missPending := true.B
    requestIssued := false.B
    expectedResponseWord := 0.U
    missTileIndex := readTileIndex
    missLayerIndex := io.layerIndex
    missRouteId := io.routeId
    missShadowBank := ~ownerBank
    missDdrBaseWord := io.ddrBaseWord
    missRouteWordOffset := io.routeWordOffset
    missLayerStrideWords := io.layerStrideWords
    missTileWordCount := Mux(
      readTileIndex === (logicalTileCount - 1).U,
      ((logicalDepth - (logicalTileCount - 1) * cacheTileWords) * imageWordsPerCacheWord).U,
      cacheTileImageWords.U
    )
  }

  when(io.tileRequest.fire) {
    requestIssued := true.B
  }

  tileCompleteReg := false.B
  when(io.tileResponse.fire) {
    val finalImageWord = responseEndWord - 1.U
    val finalCacheWordLane = finalImageWord % imageWordsPerCacheWord.U
    val finalCacheWordIndex = finalImageWord / imageWordsPerCacheWord.U
    val responseCacheWordIndex = responseStartWord / imageWordsPerCacheWord.U
    val finalCacheStartLane = Mux(
      finalCacheWordIndex === responseCacheWordIndex,
      responseStartWord % imageWordsPerCacheWord.U,
      0.U
    )
    when(io.tileResponse.bits.last || finalCacheWordLane === (imageWordsPerCacheWord - 1).U) {
      for (lane <- 0 until imageWordsPerCacheWord) { tileAssembly(lane) := 0.U }
    }.otherwise {
      for (subword <- 0 until imageWordsPerCacheWord) {
        when(subword.U >= finalCacheStartLane && subword.U <= finalCacheWordLane) {
          val sourceLane = subword.U - finalCacheStartLane
          when(sourceLane < responseValidWords) {
            tileAssembly(subword) := responseWordValues(AccMath.boundedIndex(sourceLane, imageWordsPerResponse))
          }
        }.otherwise {
          tileAssembly(subword) := 0.U
        }
      }
    }
    when(responseEndWord === missTileWordCount) {
      requestIssued := false.B
      expectedResponseWord := 0.U
      tileCompleteReg := true.B
      // A completed refill is usable immediately by compute. Ownership never
      // switches underneath an active operation; outside compute the completed
      // shadow bank may become the committed bank as before.
      when(!io.computeHold) {
        activeBankReg := missShadowBank
      }
      when(missShadowBank) {
        tileValid(1)(responseSlot) := true.B
        tileTags(1)(responseSlot) := missTileIndex
        tileRouteTags(1)(responseSlot) := missRouteId
        tileLayerTags(1)(responseSlot) := missLayerIndex
      }.otherwise {
        tileValid(0)(responseSlot) := true.B
        tileTags(0)(responseSlot) := missTileIndex
        tileRouteTags(0)(responseSlot) := missRouteId
        tileLayerTags(0)(responseSlot) := missLayerIndex
      }
      if (cacheTileCount > 1) {
        when(hasNextPrefetchTile) {
          // With compute ownership held, retain the shadow destination and
          // use its next slot. This overlaps the next tile's DDR refill with
          // compute without touching the active bank or allocating a full
          // matrix on chip. Outside compute, preserve the existing bank
          // handoff rule and refill the newly inactive bank.
          missPending := true.B
          missTileIndex := nextPrefetchTile
          missTileWordCount := nextPrefetchWordCount
          missShadowBank := Mux(io.computeHold, missShadowBank, ~missShadowBank)
        }.otherwise {
          missPending := false.B
        }
      } else {
        missPending := false.B
      }
    }.otherwise {
      expectedResponseWord := responseEndWord
    }
  }

  when(legacyWriteAccepted) {
    when(io.writeAddr === 0.U) {
      for (slot <- 0 until cacheTileCount) {
        when(ownerBank) { tileValid(0)(slot) := false.B }.otherwise { tileValid(1)(slot) := false.B }
      }
    }
    when(legacyTileLast) {
      when(ownerBank) {
        tileValid(0)(legacyTileSlot) := true.B
        tileTags(0)(legacyTileSlot) := legacyTileIndex
        tileRouteTags(0)(legacyTileSlot) := io.routeId
        tileLayerTags(0)(legacyTileSlot) := io.layerIndex
      }.otherwise {
        tileValid(1)(legacyTileSlot) := true.B
        tileTags(1)(legacyTileSlot) := legacyTileIndex
        tileRouteTags(1)(legacyTileSlot) := io.routeId
        tileLayerTags(1)(legacyTileSlot) := io.layerIndex
      }
    }
  }

  when(legacyCommit && !io.computeHold) {
    activeBankReg := ~activeBankReg
  }

  io.activeBank := activeBankReg
  io.shadowBank := ~activeBankReg
  io.prefetchCommit := legacyCommit || (tileCompleteReg && !io.computeHold)
}
