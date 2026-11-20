"""Export the complete Huginn payload for 32 HBM PCs and 32 pool lanes."""
from hardware import build_plan6_u280_hbm24_payload as exporter


exporter.HBM_PC_COUNT = 32
exporter.POOL_LANE_COUNT = 32
exporter.SLOTS_PER_TILE = exporter.ROWS_PER_TILE // exporter.POOL_LANE_COUNT
exporter.OUTPUT_DIR = exporter.ROOT / "results/plan6/huginn_u280_hbm32_pool32"
exporter.OUTPUT_FILE = exporter.OUTPUT_DIR / "weights_hbm32_pc_major.bin"
exporter.MANIFEST_FILE = exporter.OUTPUT_DIR / "manifest.json"


if __name__ == "__main__":
    exporter.main()
