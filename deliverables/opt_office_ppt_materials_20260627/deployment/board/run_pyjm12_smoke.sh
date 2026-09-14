#!/usr/bin/env bash
set -euo pipefail

MIMIC_DIR=${MIMIC_DIR:-/home/test/mimic_driver_c6}
XDMA_ID=${XDMA_ID:-1}
RUNS=${RUNS:-5}
POLL_SECONDS=${POLL_SECONDS:-20}
DDR_IMAGE=${DDR_IMAGE:-/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin}
WRITE_DDR=${WRITE_DDR:-0}

H2C_DEV=/dev/xdma${XDMA_ID}_h2c_0
C2H_DEV=/dev/xdma${XDMA_ID}_c2h_0
DMA_TO=${MIMIC_DIR}/xdma_driver/tools/dma_to_device
DMA_FROM=${MIMIC_DIR}/xdma_driver/tools/dma_from_device

CTRL_BASE=0x3000000000
DDR_BASE=0x2800000000
OUTPUT_ABS=0x28092f1000
OUTPUT_REL_LE=00102f09
DDR_SIZE=154080256

write_u32_le_hex() {
  local addr=$1
  local le_hex=$2
  echo "${le_hex}" | xxd -r -p > /tmp/pyjm12_word.bin
  sudo "${DMA_TO}" -d "${H2C_DEV}" -a "${addr}" -s 4 -f /tmp/pyjm12_word.bin >/tmp/pyjm12_dma.log 2>&1
}

read_u32_hex() {
  local addr=$1
  local out=$2
  sudo "${DMA_FROM}" -d "${C2H_DEV}" -a "${addr}" -s 4 -f "${out}" >/tmp/pyjm12_dma.log 2>&1
  od -An -tx4 -N4 "${out}" | tr -d ' '
}

require_file() {
  if [[ ! -e "$1" ]]; then
    echo "missing: $1" >&2
    exit 1
  fi
}

main() {
  cd "${MIMIC_DIR}"
  require_file "${DMA_TO}"
  require_file "${DMA_FROM}"
  require_file "${DDR_IMAGE}"
  sudo chmod +x "${DMA_TO}" "${DMA_FROM}" >/dev/null 2>&1 || true

  echo "MIMIC_DIR=${MIMIC_DIR}"
  echo "XDMA_ID=${XDMA_ID} H2C=${H2C_DEV} C2H=${C2H_DEV}"
  echo "DDR_IMAGE=${DDR_IMAGE}"
  echo "WRITE_DDR=${WRITE_DDR} RUNS=${RUNS} POLL_SECONDS=${POLL_SECONDS}"

  if [[ "${WRITE_DDR}" == "1" ]]; then
    echo "Writing DDR image to ${DDR_BASE}, size=${DDR_SIZE}"
    sudo "${DMA_TO}" -d "${H2C_DEV}" -a "${DDR_BASE}" -s "${DDR_SIZE}" -f "${DDR_IMAGE}"
    sudo "${DMA_FROM}" -d "${C2H_DEV}" -a "${DDR_BASE}" -s 64 -f /tmp/pyjm12_ddr_head.bin >/tmp/pyjm12_dma.log 2>&1
    echo "=== DDR head readback ==="
    hexdump -Cv /tmp/pyjm12_ddr_head.bin
  fi

  for run in $(seq 1 "${RUNS}"); do
    echo ""
    echo "================ RUN ${run} ================"

    write_u32_le_hex 0x3000000064 04000000
    sleep 0.2
    write_u32_le_hex 0x3000000064 02000000
    sleep 0.2
    write_u32_le_hex 0x3000000060 02000000
    write_u32_le_hex 0x3000000010 "${OUTPUT_REL_LE}"
    write_u32_le_hex 0x3000000064 08000000
    sleep 0.2

    before=$(read_u32_hex 0x3000000064 /tmp/pyjm12_status_before.bin)
    echo "status_before_start=0x${before}"

    write_u32_le_hex 0x3000000064 01000000

    got=0
    raw=00000000
    for poll in $(seq 0 "${POLL_SECONDS}"); do
      raw=$(read_u32_hex 0x3000000064 /tmp/pyjm12_status_poll.bin)
      dec=$((16#${raw}))
      input=$((dec & 7))
      result=$(((dec >> 3) & 7))
      echo "run=${run} poll=${poll} raw=0x${raw} input_status=${input} result_status=${result}"
      if [[ "${result}" -ne 0 ]]; then
        got=1
        break
      fi
      sleep 1
    done

    sudo "${DMA_FROM}" -d "${C2H_DEV}" -a "${OUTPUT_ABS}" -s 128 -f "/tmp/pyjm12_output_run_${run}.bin" >/tmp/pyjm12_dma.log 2>&1
    echo "=== output head run ${run} @ ${OUTPUT_ABS} ==="
    hexdump -Cv "/tmp/pyjm12_output_run_${run}.bin" | head -12

    latency=$(read_u32_hex 0x300000007c /tmp/pyjm12_latency_cycles.bin || true)
    if [[ -n "${latency}" ]]; then
      echo "latency_cycles_reg31=0x${latency}"
    fi

    if [[ "${got}" -ne 1 ]]; then
      echo "RUN ${run} FAILED: result_status did not change" >&2
      exit 2
    fi
    echo "RUN ${run} PASS"
  done

  echo ""
  echo "All ${RUNS} run(s) passed."
}

main "$@"
