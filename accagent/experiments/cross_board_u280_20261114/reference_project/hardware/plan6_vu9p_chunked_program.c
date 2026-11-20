#define _FILE_OFFSET_BITS 64

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "mimic_api.h"
#include "mimic_dma.h"
#include "mimic_sdk.h"

#define CARD_ID 1
#define BITSTREAM_PATH "/root/fpga/plan6_huginn/app_shell_9p_wrapper.bit"
#define DMA_CHUNK_BYTES (1U << 20)

static int write_config(MmSession *session, uint64_t offset, uint32_t value) {
    mmerrno rc = reg_readwrite(session, CARD_ID,
                               C6_FPGA_PROGRAM_CONFIG_ADDR + offset,
                               value, NULL, false);
    if (rc != MM_API_SUCCESS) {
        fprintf(stderr, "CONFIG_WRITE offset=0x%llx value=0x%x rc=%d\n",
                (unsigned long long)offset, value, rc);
        return 1;
    }
    return 0;
}

static int read_config(MmSession *session, uint64_t offset, uint32_t *value) {
    mmerrno rc = reg_readwrite(session, CARD_ID,
                               C6_FPGA_PROGRAM_CONFIG_ADDR + offset,
                               0, value, true);
    if (rc != MM_API_SUCCESS) {
        fprintf(stderr, "CONFIG_READ offset=0x%llx rc=%d\n",
                (unsigned long long)offset, rc);
        return 1;
    }
    return 0;
}

int main(void) {
    MmSession session;
    memset(&session, 0, sizeof(session));
    mmerrno rc = MmSession_Open(&session);
    if (rc != MM_API_SUCCESS) {
        fprintf(stderr, "MmSession_Open rc=%d\n", rc);
        return 1;
    }

    unsigned card_count = 0;
    rc = MmSession_ScanFpgaDeviceNum(&session, &card_count);
    if (rc != MM_API_SUCCESS || CARD_ID >= (int)card_count) {
        fprintf(stderr, "Card unavailable rc=%d count=%u\n", rc, card_count);
        MmSession_Close(&session);
        return 1;
    }
    printf("BOARD card=%d dbdf=%s\n", CARD_ID, session.DBDF[CARD_ID]);

    FILE *bitstream = fopen(BITSTREAM_PATH, "rb");
    if (!bitstream || fseeko(bitstream, 0, SEEK_END) != 0) {
        fprintf(stderr, "Cannot open or seek bitstream %s\n", BITSTREAM_PATH);
        if (bitstream)
            fclose(bitstream);
        MmSession_Close(&session);
        return 1;
    }
    off_t file_bytes = ftello(bitstream);
    if (file_bytes <= 0 || fseeko(bitstream, 0, SEEK_SET) != 0) {
        fprintf(stderr, "Invalid bitstream size\n");
        fclose(bitstream);
        MmSession_Close(&session);
        return 1;
    }

    uint64_t transfer_bytes = ((uint64_t)file_bytes + 31U) & ~31ULL;
    if ((transfer_bytes % DMA_CHUNK_BYTES) % 32U != 0) {
        fprintf(stderr, "Final DMA chunk is not 32-byte aligned\n");
        fclose(bitstream);
        MmSession_Close(&session);
        return 1;
    }
    uint8_t *buffer = malloc(DMA_CHUNK_BYTES);
    if (!buffer) {
        fprintf(stderr, "Cannot allocate DMA buffer\n");
        fclose(bitstream);
        MmSession_Close(&session);
        return 1;
    }

    uint64_t offset = 0;
    uint64_t chunk_count = 0;
    while (offset < transfer_bytes) {
        uint32_t chunk_bytes = (uint32_t)(transfer_bytes - offset);
        if (chunk_bytes > DMA_CHUNK_BYTES)
            chunk_bytes = DMA_CHUNK_BYTES;
        uint32_t file_chunk_bytes = 0;
        if (offset < (uint64_t)file_bytes) {
            uint64_t remaining = (uint64_t)file_bytes - offset;
            file_chunk_bytes = remaining < chunk_bytes ?
                               (uint32_t)remaining : chunk_bytes;
        }
        memset(buffer, 0, chunk_bytes);
        if (file_chunk_bytes &&
            fread(buffer, 1, file_chunk_bytes, bitstream) != file_chunk_bytes) {
            fprintf(stderr, "Bitstream read failed offset=0x%llx\n",
                    (unsigned long long)offset);
            free(buffer);
            fclose(bitstream);
            MmSession_Close(&session);
            return 1;
        }
        rc = dma_to_device(&session, CARD_ID, 0, (char *)buffer,
                           chunk_bytes, C6_PL_DDR_BASE_ADDR + offset);
        if (rc != MM_API_SUCCESS) {
            fprintf(stderr, "BITSTREAM_DMA_FAILED offset=0x%llx bytes=%u rc=%d\n",
                    (unsigned long long)offset, chunk_bytes, rc);
            free(buffer);
            fclose(bitstream);
            MmSession_Close(&session);
            return 1;
        }
        offset += chunk_bytes;
        ++chunk_count;
    }
    free(buffer);
    fclose(bitstream);
    printf("BITSTREAM_DMA_COMPLETE base=0x%llx bytes=%llu chunks=%llu chunk_bytes=%u\n",
           (unsigned long long)C6_PL_DDR_BASE_ADDR,
           (unsigned long long)transfer_bytes,
           (unsigned long long)chunk_count, DMA_CHUNK_BYTES);

    const uint32_t chip_select = 1;
    if (write_config(&session, 0x04, 1) ||
        write_config(&session, 0x04, 0) ||
        write_config(&session, 0x10, (uint32_t)((uint64_t)file_bytes / 4U)) ||
        write_config(&session, 0x08, chip_select) ||
        write_config(&session, 0x00, 2) ||
        write_config(&session, 0x00, 1)) {
        MmSession_Close(&session);
        return 1;
    }
    usleep(100000);
    if (write_config(&session, 0x00, 0)) {
        MmSession_Close(&session);
        return 1;
    }

    uint32_t status = 0;
    uint32_t init_status = 0;
    int init_ready = 0;
    for (int attempt = 0; attempt < 30; ++attempt) {
        if (read_config(&session, 0x08, &init_status)) {
            MmSession_Close(&session);
            return 1;
        }
        if (init_status != 0) {
            init_ready = 1;
            break;
        }
        usleep(100000);
    }
    if (!init_ready) {
        fprintf(stderr, "FPGA_INIT_TIMEOUT\n");
        MmSession_Close(&session);
        return 1;
    }

    int done = 0;
    for (int attempt = 0; attempt < 10; ++attempt) {
        if (read_config(&session, 0x0c, &status)) {
            MmSession_Close(&session);
            return 1;
        }
        if ((status & 0x7U & chip_select) == chip_select) {
            done = 1;
            break;
        }
        usleep(500000);
    }
    if (write_config(&session, 0x04, 1) ||
        write_config(&session, 0x04, 0)) {
        MmSession_Close(&session);
        return 1;
    }
    if (!done) {
        fprintf(stderr, "FPGA_DONE_TIMEOUT status=0x%08x\n", status);
        MmSession_Close(&session);
        return 1;
    }

    printf("BITSTREAM_PROGRAMMED card=%d bytes=%llu transfer_bytes=%llu init=0x%08x done=0x%08x\n",
           CARD_ID, (unsigned long long)file_bytes,
           (unsigned long long)transfer_bytes, init_status, status);
    MmSession_Close(&session);
    return 0;
}
