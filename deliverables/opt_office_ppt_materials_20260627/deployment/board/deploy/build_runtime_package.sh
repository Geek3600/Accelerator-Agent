#!/bin/bash
set -euo pipefail

SOURCE_DIR=${SOURCE_DIR:-/home/hyyuan/pyjm12_demo}
OUT_DIR=${OUT_DIR:-/tmp}
PACKAGE_NAME=${PACKAGE_NAME:-pyjm12_office2010_runtime_20260616}
WORK_DIR=${WORK_DIR:-/tmp/${PACKAGE_NAME}_staging}
COMPRESS=${COMPRESS:-0}

package_dir="${WORK_DIR}/pyjm12_demo"
tar_path="${OUT_DIR}/${PACKAGE_NAME}.tar"
if [[ "$COMPRESS" -eq 1 ]]; then
  package_path="${OUT_DIR}/${PACKAGE_NAME}.tar.gz"
else
  package_path="$tar_path"
fi
sha_path="${OUT_DIR}/${PACKAGE_NAME}.sha256"

require_file() {
  if [[ ! -e "$1" ]]; then
    echo "missing required file: $1" >&2
    exit 1
  fi
}

copy_file() {
  local rel=$1
  local mode=${2:-0644}
  require_file "${SOURCE_DIR}/${rel}"
  mkdir -p "${package_dir}/$(dirname "$rel")"
  install -m "$mode" "${SOURCE_DIR}/${rel}" "${package_dir}/${rel}"
}

rm -rf "$WORK_DIR" "$tar_path" "${tar_path}.gz" "$package_path" "$sha_path"
mkdir -p "$package_dir"

copy_file app_shell_9p_wrapper_debug_latency_fixedmux_constrained_20260513.bit
copy_file ddr_image.u32.bin
copy_file patterns.txt
copy_file pyjm_fpga_demo.c
copy_file pyjm_fpga_batch_gen.py 0755
copy_file pyjm_passwords_to_hcmask.py 0755
copy_file pyjm_update_app_status.py 0755
copy_file run_pyjm_batch_demo.sh 0755
copy_file run_pyjm_office2010_single_card.sh 0755
copy_file run_pyjm_office2010_multi_card.sh 0755

copy_file office2010_shared/App/app_shell_9p_wrapper.bin
copy_file office2010_shared/App/FPGA_Crack_Info.ini
copy_file office2010_shared/App/office2010_test 0755
copy_file office2010_shared/include/ipc_flock.h
copy_file office2010_shared/include/mimic_api.h
copy_file office2010_shared/include/mimic_dma.h
copy_file office2010_shared/include/mimic_sdk.h
copy_file office2010_shared/lib/libmimic_v6_api.so 0755
copy_file office2010_shared/lib/libmimic_v6_sdk.so 0755
copy_file office2010_shared/lib/liboffice2010_mask.a

copy_file deploy/app_status.template.json
copy_file deploy/init_node.sh 0755
copy_file deploy/preflight_check.sh 0755
copy_file deploy/build_runtime_package.sh 0755

cat >"${package_dir}/PACKAGE_MANIFEST.txt" <<'EOF'
PYJM + Office2010 FPGA runtime package

Included runtime files:
- OPT/PYJM FPGA bitstream:
  app_shell_9p_wrapper_debug_latency_fixedmux_constrained_20260513.bit
- OPT/PYJM DDR image:
  ddr_image.u32.bin
- Password pattern table:
  patterns.txt
- Host/runtime scripts and source:
  pyjm_fpga_demo.c
  pyjm_fpga_batch_gen.py
  pyjm_passwords_to_hcmask.py
  pyjm_update_app_status.py
  run_pyjm_batch_demo.sh
  run_pyjm_office2010_single_card.sh
  run_pyjm_office2010_multi_card.sh
- Office2010 runtime:
  office2010_shared/App/app_shell_9p_wrapper.bin
  office2010_shared/App/FPGA_Crack_Info.ini
  office2010_shared/App/office2010_test
  office2010_shared/include/*
  office2010_shared/lib/*
- Deployment helpers:
  deploy/app_status.template.json
  deploy/init_node.sh
  deploy/preflight_check.sh
  deploy/build_runtime_package.sh
- Integrity list:
  SHA256SUMS

Not included:
- /home/test/mimic_driver_c6 and XDMA kernel driver. These are node prerequisites.
- /home/share/app_status.json runtime state. Only a template is included.
- Generated card_* directories, multi_card_logs, __pycache__, 10^4_fpga.txt, *.hcmask, mmsdk.log, office2010_batch_*.log, and old tar files.

Expected node prerequisites:
- Ubuntu/Linux node with Python 3 and gcc.
- sudo privilege for the deployment user.
- /home/test/mimic_driver_c6 present, including fpga_program, get_fpga_num, XDMA driver tools, and load_driver.sh.
- 8 FPGA cards visible after XDMA driver load.

Smoke commands:
cd /home/hyyuan/pyjm12_demo
PYJM_SUDO_PASSWORD=... ./deploy/init_node.sh
PYJM_SUDO_PASSWORD=... ./run_pyjm_office2010_multi_card.sh --cards 0 --parallel --total-generate 1 --poll-timeout-ms 5000
PYJM_SUDO_PASSWORD=... CARD_START_SPREAD_SEC=2 ./run_pyjm_office2010_multi_card.sh --cards 0,1,2,3,4,5,6,7 --parallel --total-generate 1 --poll-timeout-ms 5000
EOF

cat >"${package_dir}/README_DEPLOY.md" <<'EOF'
# PYJM + Office2010 Runtime Deployment

Extract under `/home/hyyuan` so the runtime path becomes `/home/hyyuan/pyjm12_demo`.

```bash
cd /home/hyyuan
tar -xzf /path/to/pyjm12_office2010_runtime_20260616.tar.gz
cd /home/hyyuan/pyjm12_demo
```

Initialize node-side prerequisites that are not part of this package:

```bash
PYJM_SUDO_PASSWORD=<sudo-password> ./deploy/init_node.sh
```

Run smoke tests:

```bash
PYJM_SUDO_PASSWORD=<sudo-password> ./run_pyjm_office2010_multi_card.sh \
  --cards 0 \
  --parallel \
  --total-generate 1 \
  --poll-timeout-ms 5000

PYJM_SUDO_PASSWORD=<sudo-password> CARD_START_SPREAD_SEC=2 ./run_pyjm_office2010_multi_card.sh \
  --cards 0,1,2,3,4,5,6,7 \
  --parallel \
  --total-generate 1 \
  --poll-timeout-ms 5000
```

Run the formal 8-card flow:

```bash
PYJM_SUDO_PASSWORD=<sudo-password> ./run_pyjm_office2010_multi_card.sh \
  --cards 0,1,2,3,4,5,6,7 \
  --parallel \
  --total-generate 10000 \
  --poll-timeout-ms 5000
```

`exit=0` means Office2010 found a password. `exit=4` means the flow completed normally with no hit. Any other exit code is a real error.
EOF

(
  cd "$package_dir"
  bash -n run_pyjm_batch_demo.sh run_pyjm_office2010_single_card.sh run_pyjm_office2010_multi_card.sh deploy/init_node.sh deploy/preflight_check.sh deploy/build_runtime_package.sh
  python3 -m py_compile pyjm_fpga_batch_gen.py pyjm_passwords_to_hcmask.py pyjm_update_app_status.py
  python3 -m json.tool deploy/app_status.template.json >/dev/null
  find . -type d -name __pycache__ -prune -exec rm -rf {} +
  rm -f SHA256SUMS .SHA256SUMS.tmp
  while IFS= read -r rel; do
    sha256sum "$rel" >> .SHA256SUMS.tmp
  done < <(find . -type f ! -name SHA256SUMS ! -name .SHA256SUMS.tmp -printf '%P\n' | sort)
  mv .SHA256SUMS.tmp SHA256SUMS
)

tar -C "$WORK_DIR" -cf "$tar_path" pyjm12_demo
if [[ "$COMPRESS" -eq 1 ]]; then
  gzip -1 "$tar_path"
  mv "${tar_path}.gz" "$package_path"
fi
sha256sum "$package_path" > "$sha_path"

echo "package=${package_path}"
cat "$sha_path"
if [[ "$COMPRESS" -eq 1 ]]; then
  tar -tzf "$package_path" >/dev/null
else
  tar -tf "$package_path" >/dev/null
fi
echo "package_check_ok"
