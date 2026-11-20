#define _FILE_OFFSET_BITS 64

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include "mimic_api.h"
#include "mimic_dma.h"
#include "mimic_sdk.h"

#ifndef CARD_ID
#define CARD_ID 1
#endif
#define CONTEXT_TOKENS 512
#define BITSTREAM_PATH "/root/fpga/plan6_huginn/app_shell_9p_wrapper.bit"
#define PAYLOAD_DIR "/root/fpga/plan6_huginn/payload"

#define CONTROL_BASE 0x00d0000000ULL
#define DDR_WEIGHT_BASE 0x0800000000ULL
#define DDR_GAMMA_BASE 0x0a00000000ULL
#define CORE_WEIGHT_BASE (DDR_WEIGHT_BASE + 0x001000000ULL)
#define CORE_GAMMA_BASE (DDR_GAMMA_BASE + 0x00100000ULL)

#define REG_CONTROL 0x00
#define REG_STATUS 0x04
#define REG_CYCLES_LO 0x08
#define REG_CYCLES_HI 0x0c
#define REG_NONZERO_CHUNKS 0x10
#define REG_OUTPUT_DIGEST 0x14
#define REG_CONTEXT_TOKENS 0x18

#define DMA_CHUNK_BYTES (1U << 20)
#define DMA_WORD_BYTES 64U
#define RUN_TIMEOUT_POLLS 3600000U

typedef struct {
    const char *name;
    uint64_t address;
    uint64_t expected_bytes;
} payload_region_t;

static const payload_region_t payload_regions[] = {
    {"adapter.usw512", DDR_WEIGHT_BASE, 14192640},
    {"weights.usw512", CORE_WEIGHT_BASE, 400834560},
    {"adapter_gamma.fp16", DDR_GAMMA_BASE, 337920},
    {"gamma.fp16", CORE_GAMMA_BASE, 15933440},
};

static uint64_t monotonic_ns(void) {
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return (uint64_t)now.tv_sec * 1000000000ULL + (uint64_t)now.tv_nsec;
}

static int write_register(MmSession *session, uint64_t offset, uint32_t value) {
    mmerrno result = mm_dma_write(session, CARD_ID, 0,
                                  (uint8_t *)&value,
                                  CONTROL_BASE + offset, sizeof(value));
    if (result != MM_API_SUCCESS) {
        fprintf(stderr, "MMIO write failed offset=0x%llx rc=%d\n",
                (unsigned long long)offset, result);
        return 1;
    }
    return 0;
}

static int read_register(MmSession *session, uint64_t offset, uint32_t *value) {
    mmerrno result = mm_dma_read(session, CARD_ID, 0,
                                 (uint8_t *)value,
                                 CONTROL_BASE + offset, sizeof(*value));
    if (result != MM_API_SUCCESS) {
        fprintf(stderr, "MMIO read failed offset=0x%llx rc=%d\n",
                (unsigned long long)offset, result);
        return 1;
    }
    return 0;
}

static int load_payload(MmSession *session, const payload_region_t *region,
                        uint8_t *buffer) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s", PAYLOAD_DIR, region->name);
    FILE *payload = fopen(path, "rb");
    if (!payload) {
        fprintf(stderr, "Cannot open payload: %s\n", path);
        return 1;
    }

    if (fseeko(payload, 0, SEEK_END) != 0) {
        fclose(payload);
        return 1;
    }
    off_t file_bytes = ftello(payload);
    if (file_bytes < 0 || (uint64_t)file_bytes != region->expected_bytes ||
        (region->expected_bytes % DMA_WORD_BYTES) != 0 ||
        fseeko(payload, 0, SEEK_SET) != 0) {
        fprintf(stderr, "Unexpected payload length: %s\n", path);
        fclose(payload);
        return 1;
    }

    uint64_t offset = 0;
    while (offset < region->expected_bytes) {
        uint32_t chunk_bytes = DMA_CHUNK_BYTES;
        uint64_t remaining = region->expected_bytes - offset;
        if (remaining < chunk_bytes)
            chunk_bytes = (uint32_t)remaining;
        if (fread(buffer, 1, chunk_bytes, payload) != chunk_bytes) {
            fprintf(stderr, "Payload read failed: %s\n", path);
            fclose(payload);
            return 1;
        }
        mmerrno result = mm_dma_write(session, CARD_ID, 0, buffer,
                                      region->address + offset, chunk_bytes);
        if (result != MM_API_SUCCESS) {
            fprintf(stderr, "DMA write failed file=%s offset=0x%llx rc=%d\n",
                    region->name, (unsigned long long)offset, result);
            fclose(payload);
            return 1;
        }
        offset += chunk_bytes;
    }

    fclose(payload);
    printf("PAYLOAD name=%s address=0x%llx bytes=%llu\n", region->name,
           (unsigned long long)region->address,
           (unsigned long long)region->expected_bytes);
    return 0;
}

int main(void) {
    setvbuf(stdout, NULL, _IOLBF, 0);
    MmSession session;
    memset(&session, 0, sizeof(session));
    mmerrno result = MmSession_Open(&session);
    if (result != MM_API_SUCCESS) {
        fprintf(stderr, "MmSession_Open failed rc=%d\n", result);
        return 1;
    }

    unsigned card_count = 0;
    result = MmSession_ScanFpgaDeviceNum(&session, &card_count);
    if (result != MM_API_SUCCESS || CARD_ID >= (int)card_count) {
        fprintf(stderr, "Card %d unavailable scan_rc=%d card_count=%u\n",
                CARD_ID, result, card_count);
        MmSession_Close(&session);
        return 1;
    }
    printf("BOARD card=%d dbdf=%s\n", CARD_ID, session.DBDF[CARD_ID]);

#ifndef SKIP_PROGRAM
    result = program_fpga(&session, CARD_ID, 0, 1, BITSTREAM_PATH);
    if (result != MM_API_SUCCESS) {
        fprintf(stderr, "Official SDK programming failed card=%d rc=%d\n",
                CARD_ID, result);
        MmSession_Close(&session);
        return 1;
    }
    printf("BITSTREAM card=%d path=%s status=programmed\n",
           CARD_ID, BITSTREAM_PATH);
#else
    printf("BITSTREAM path=%s status=already_programmed\n", BITSTREAM_PATH);
#endif
    for (int attempt = 0; attempt < 30; ++attempt) {
        if (is_gtx_interconnect_safe(&session, CARD_ID) == MM_API_SUCCESS)
            break;
        if (attempt == 29) {
            fprintf(stderr, "PCIe interconnect did not become ready\n");
            MmSession_Close(&session);
            return 1;
        }
        usleep(400000);
    }
    printf("LINK card=%d status=UP\n", CARD_ID);

    uint8_t *buffer = malloc(DMA_CHUNK_BYTES);
    if (!buffer) {
        MmSession_Close(&session);
        return 1;
    }
    for (size_t index = 0;
         index < sizeof(payload_regions) / sizeof(payload_regions[0]);
         ++index) {
        if (load_payload(&session, &payload_regions[index], buffer)) {
            free(buffer);
            MmSession_Close(&session);
            return 1;
        }
    }
    free(buffer);

    uint32_t configured_context = 0;
    if (write_register(&session, REG_CONTROL, 2) ||
        write_register(&session, REG_CONTEXT_TOKENS, CONTEXT_TOKENS) ||
        read_register(&session, REG_CONTEXT_TOKENS, &configured_context)) {
        MmSession_Close(&session);
        return 1;
    }
    if (configured_context != CONTEXT_TOKENS) {
        fprintf(stderr, "Context readback mismatch configured=%u expected=%u\n",
                configured_context, CONTEXT_TOKENS);
        MmSession_Close(&session);
        return 1;
    }
    printf("CONTROL base=0x%llx context_tokens=%u register_bytes=%zu\n",
           (unsigned long long)CONTROL_BASE, configured_context,
           sizeof(uint32_t));

    uint32_t status = 0;
    uint64_t start_ns = monotonic_ns();
    if (write_register(&session, REG_CONTROL, 1)) {
        MmSession_Close(&session);
        return 1;
    }
    int complete = 0;
    for (uint32_t poll = 0; poll < RUN_TIMEOUT_POLLS; ++poll) {
        if (read_register(&session, REG_STATUS, &status)) {
            MmSession_Close(&session);
            return 1;
        }
        if ((status & 0x04) != 0) {
            fprintf(stderr, "Accelerator reported error status=0x%08x\n", status);
            MmSession_Close(&session);
            return 1;
        }
        if ((status & 0x09) == 0x09) {
            complete = 1;
            break;
        }
        usleep(1000);
    }
    uint64_t elapsed_ns = monotonic_ns() - start_ns;
    if (!complete) {
        fprintf(stderr, "Accelerator timeout status=0x%08x\n", status);
        MmSession_Close(&session);
        return 1;
    }

    uint32_t cycles_low = 0, cycles_high = 0, nonzero_chunks = 0, digest = 0;
    if (read_register(&session, REG_CYCLES_LO, &cycles_low) ||
        read_register(&session, REG_CYCLES_HI, &cycles_high) ||
        read_register(&session, REG_NONZERO_CHUNKS, &nonzero_chunks) ||
        read_register(&session, REG_OUTPUT_DIGEST, &digest)) {
        MmSession_Close(&session);
        return 1;
    }
    uint64_t cycles = ((uint64_t)cycles_high << 32) | cycles_low;
    printf("PLAN6_VU9P_RESULT card=%d context_tokens=%d status=0x%08x "
           "cycles=%" PRIu64 " nonzero_chunks=%u digest=0x%08x "
           "host_elapsed_ms=%.3f\n",
           CARD_ID, CONTEXT_TOKENS, status, cycles, nonzero_chunks, digest,
           (double)elapsed_ns / 1000000.0);

    MmSession_Close(&session);
    return nonzero_chunks == 0 ? 2 : 0;
}
