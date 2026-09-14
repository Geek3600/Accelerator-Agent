package DM

object Param {
    val SINGLE_QUERY_BATCH = 12
    val BATCHSIZE = SINGLE_QUERY_BATCH
    val LBANCHNUM = 4
    val LBATCHSIZE = BATCHSIZE * LBANCHNUM // 加速器可以同时为128个用户维护独立的历史KVcache
    val LOAD_VECNUM = 2 // 每周期从Load0收到2个Q元素+2个K元素
    val HEAD_VECNUM = 64 // 一个Q/K向量有64个元素
    // 真实场景已收敛到 16-token 短序列，不再保留 912 历史长度上限。
    val MAX_SEQLEN = 16
    val MAX_PREFILL = 16
    val TILE_SEQLEN = 16
    val LOCAL_PREFILL = 16
    val MULNUM = 32 //32个乘法器
    val DATAW = 8 // 数据位宽
    val MEM_DEPTH = 512

}
