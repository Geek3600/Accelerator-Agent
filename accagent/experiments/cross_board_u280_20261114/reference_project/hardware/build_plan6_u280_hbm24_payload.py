"""Export and verify the complete Huginn USW-512 payload for U280 HBM PCs."""
import hashlib
import json
import mmap
from pathlib import Path

from hardware.export_plan6_huginn_core import build_huginn_linear_operator_map


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_DIR = ROOT / "results/plan6/huginn_recurrent_core"
OUTPUT_DIR = ROOT / "results/plan6/huginn_u280_hbm27"
OUTPUT_FILE = OUTPUT_DIR / "weights_hbm27_pc_major.bin"
MANIFEST_FILE = OUTPUT_DIR / "manifest.json"
RECORD_BYTES = 64
HBM_PC_COUNT = 27
POOL_LANE_COUNT = 24
ROWS_PER_TILE = 96
SLOTS_PER_TILE = 4
ZERO_RECORD = bytes(RECORD_BYTES)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lane_row(tile, slot, lane):
    if POOL_LANE_COUNT == 32:
        return tile * ROWS_PER_TILE + slot * POOL_LANE_COUNT + lane
    return tile * ROWS_PER_TILE + (lane // 8) * 32 + (lane % 8) * 4 + slot


def source_record_offset(view, local_row, window, windows):
    return (view["weight_offset_bytes"] +
            (local_row * windows + window) * RECORD_BYTES)


def iter_groups(rows, windows):
    tiles = (rows + ROWS_PER_TILE - 1) // ROWS_PER_TILE
    for tile in range(tiles):
        for slot in range(SLOTS_PER_TILE):
            for window in range(windows):
                yield tile, slot, window


def set_covered(coverage, record_index):
    byte_index, bit_index = divmod(record_index, 8)
    bit = 1 << bit_index
    if coverage[byte_index] & bit:
        raise ValueError(f"source record {record_index} was exported more than once")
    coverage[byte_index] |= bit


def is_covered(coverage, record_index):
    byte_index, bit_index = divmod(record_index, 8)
    return bool(coverage[byte_index] & (1 << bit_index))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUTPUT_FILE.exists() or MANIFEST_FILE.exists():
        raise FileExistsError(f"refusing to overwrite {OUTPUT_DIR}")

    payload_manifest = json.loads((PAYLOAD_DIR / "manifest.json").read_text())
    operators = build_huginn_linear_operator_map(payload_manifest)
    if len(operators) != 21:
        raise ValueError(f"expected 21 linear operators, found {len(operators)}")

    sources = {
        name: (PAYLOAD_DIR / name).open("rb")
        for name in ("weights.usw512", "adapter.usw512")
    }
    source_maps = {
        name: mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
        for name, stream in sources.items()
    }
    source_hashes = {name: sha256_file(PAYLOAD_DIR / name) for name in sources}
    expected_hashes = {
        "weights.usw512": payload_manifest["sources"]["core_weights_sha256"],
        "adapter.usw512": payload_manifest["file_sha256"]["adapter.usw512"],
    }
    if source_hashes != expected_hashes:
        raise ValueError("full Huginn source payload hashes differ from manifest")

    source_records = {
        "weights.usw512": (PAYLOAD_DIR / "weights.usw512").stat().st_size // RECORD_BYTES,
        "adapter.usw512": (PAYLOAD_DIR / "adapter.usw512").stat().st_size // RECORD_BYTES,
    }
    coverage = {
        name: bytearray((count + 7) // 8)
        for name, count in source_records.items()
    }
    output_operators = []
    total_groups = 0
    total_logical_records = sum(
        (((int(view["shape"][0]) + ROWS_PER_TILE - 1) // ROWS_PER_TILE) *
         SLOTS_PER_TILE * ((int(view["shape"][1]) + 255) // 256) * POOL_LANE_COUNT)
        for view in operators
    )
    pc_record_counts = [
        (total_logical_records + HBM_PC_COUNT - 1 - pc) // HBM_PC_COUNT
        for pc in range(HBM_PC_COUNT)
    ]
    pc_lane_bytes = [count * RECORD_BYTES for count in pc_record_counts]
    pc_base_offsets = []
    for pc in range(HBM_PC_COUNT):
        pc_base_offsets.append(sum(pc_lane_bytes[:pc]))
    for view in operators:
        rows, columns = map(int, view["shape"])
        windows = (columns + 255) // 256
        tiles = (rows + ROWS_PER_TILE - 1) // ROWS_PER_TILE
        groups = tiles * SLOTS_PER_TILE * windows
        output_operators.append({
            **view,
            "matrix_rows": rows,
            "matrix_columns": columns,
            "windows_per_row": windows,
            "tiles": tiles,
            "groups": groups,
            "pc_record_offset": total_groups,
            "pc_bytes": groups * RECORD_BYTES,
            "logical_record_offset": total_groups * POOL_LANE_COUNT,
        })
        total_groups += groups
    pc_major_bytes = sum(pc_lane_bytes)

    try:
        with OUTPUT_FILE.open("xb") as output:
            output.truncate(pc_major_bytes)
            for view in output_operators:
                rows = view["matrix_rows"]
                windows = view["windows_per_row"]
                weight_file = view["weight_file"]
                source = source_maps[weight_file]
                for group_index, (tile, slot, window) in enumerate(iter_groups(rows, windows)):
                    logical_group = view["pc_record_offset"] + group_index
                    for lane in range(POOL_LANE_COUNT):
                        local_row = lane_row(tile, slot, lane)
                        global_record = logical_group * POOL_LANE_COUNT + lane
                        pc_record, pc = divmod(global_record, HBM_PC_COUNT)
                        output_offset = pc_base_offsets[pc] + pc_record * RECORD_BYTES
                        if local_row < rows:
                            byte_offset = source_record_offset(view, local_row, window, windows)
                            record = source[byte_offset:byte_offset + RECORD_BYTES]
                            source_record = (view["weight_offset_bytes"] // RECORD_BYTES +
                                local_row * windows + window)
                            set_covered(coverage[weight_file], source_record)
                        else:
                            record = ZERO_RECORD
                        output.seek(output_offset)
                        output.write(record)

        for name, record_count in source_records.items():
            covered = sum(value.bit_count() for value in coverage[name])
            if covered != record_count:
                raise ValueError(f"{name}: covered {covered} of {record_count} source records")

        with OUTPUT_FILE.open("rb") as stream:
            output_map = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
            try:
                for view in output_operators:
                    rows = view["matrix_rows"]
                    windows = view["windows_per_row"]
                    source = source_maps[view["weight_file"]]
                    for group_index, (tile, slot, window) in enumerate(iter_groups(rows, windows)):
                        logical_group = view["pc_record_offset"] + group_index
                        for lane in range(POOL_LANE_COUNT):
                            local_row = lane_row(tile, slot, lane)
                            global_record = logical_group * POOL_LANE_COUNT + lane
                            pc_record, pc = divmod(global_record, HBM_PC_COUNT)
                            actual_offset = pc_base_offsets[pc] + pc_record * RECORD_BYTES
                            if local_row < rows:
                                source_offset = source_record_offset(
                                    view, local_row, window, windows
                                )
                                expected = source[source_offset:source_offset + RECORD_BYTES]
                                source_record = (view["weight_offset_bytes"] // RECORD_BYTES +
                                    local_row * windows + window)
                                if not is_covered(coverage[view["weight_file"]], source_record):
                                    raise ValueError("reverse map found an uncovered source record")
                            else:
                                expected = ZERO_RECORD
                            if output_map[actual_offset:actual_offset + RECORD_BYTES] != expected:
                                raise ValueError(
                                    f"byte mismatch in {view['name']} tile={tile} "
                                    f"slot={slot} window={window} lane={lane}"
                                )
            finally:
                output_map.close()

        for item in output_operators:
            logical_start = item["logical_record_offset"]
            logical_end = logical_start + item["groups"] * POOL_LANE_COUNT
            pc_offsets = []
            pc_counts = []
            for pc in range(HBM_PC_COUNT):
                first = logical_start + ((pc - logical_start) % HBM_PC_COUNT)
                count = max(0, (logical_end - 1 - first) // HBM_PC_COUNT + 1)
                pc_offsets.append(pc_base_offsets[pc] + (first // HBM_PC_COUNT) * RECORD_BYTES)
                pc_counts.append(count)
            item["pc_base_offsets_bytes"] = pc_offsets
            item["pc_record_counts"] = pc_counts
        result = {
            "format": f"Plan6-Huginn-U280-HBM{HBM_PC_COUNT}-to-pool{POOL_LANE_COUNT}-v1",
            "payload_manifest_sha256": sha256_file(PAYLOAD_DIR / "manifest.json"),
            "source_payload_sha256": source_hashes,
            "source_payload_bytes": {
                name: (PAYLOAD_DIR / name).stat().st_size for name in source_hashes
            },
            "source_records_covered_once": source_records,
            "pc_memory_layout": f"flatten output groups then stripe records by global_index modulo {HBM_PC_COUNT}",
            "record_bytes": RECORD_BYTES,
            "hbm_pc_count": HBM_PC_COUNT,
            "pool_lane_count": POOL_LANE_COUNT,
            "rows_per_tile": ROWS_PER_TILE,
            "group_count": total_groups,
            "pc_major_payload_bytes": OUTPUT_FILE.stat().st_size,
            "pc_major_payload_sha256": sha256_file(OUTPUT_FILE),
            "logical_record_count": total_logical_records,
            "pc_record_counts": pc_record_counts,
            "pc_base_offsets_bytes": pc_base_offsets,
            "weight_pc_ids": list(range(HBM_PC_COUNT)),
            "reserved_pc_ids": list(range(HBM_PC_COUNT, 32)),
            "reserved_pc_status": "reserved interfaces have no payload or bandwidth counted",
            "operators": output_operators,
        }
        MANIFEST_FILE.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({
            "format": result["format"],
            "source_payload_sha256": source_hashes,
            "source_records_covered_once": source_records,
            "group_count": total_groups,
            "pc_major_payload_bytes": result["pc_major_payload_bytes"],
            "pc_major_payload_sha256": result["pc_major_payload_sha256"],
            "verification": "PASS: reverse map matches every source record and padding byte",
        }, indent=2))
        return result
    finally:
        for source in source_maps.values():
            source.close()
        for stream in sources.values():
            stream.close()


if __name__ == "__main__":
    main()
