#define _FILE_OFFSET_BITS 64

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mimic_api.h"
#include "mimic_dma.h"
#include "mimic_sdk.h"

#ifndef CARD_ID
#define CARD_ID 0
#endif
#define CONTROL_BASE 0x00d0000000ULL
#ifndef DDR_ADAPTER_BASE
#define DDR_ADAPTER_BASE 0x0800000000ULL
#endif
#define ADAPTER_PATH "/root/fpga/plan6_huginn/payload/adapter.usw512"
#define TRANSFER_BYTES (1U << 20)
#ifndef TEST_CONTROL
#define TEST_CONTROL 0
#endif

int main(void) {
    MmSession session;
    memset(&session, 0, sizeof(session));
    mmerrno rc = MmSession_Open(&session);
    if (rc != MM_API_SUCCESS) {
        fprintf(stderr, "MmSession_Open failed rc=%d\n", rc);
        return 1;
    }

    unsigned card_count = 0;
    rc = MmSession_ScanFpgaDeviceNum(&session, &card_count);
    if (rc != MM_API_SUCCESS || CARD_ID >= (int)card_count) {
        fprintf(stderr, "Card unavailable rc=%d count=%u\n", rc, card_count);
        MmSession_Close(&session);
        return 1;
    }
    mmerrno link_rc = is_gtx_interconnect_safe(&session, CARD_ID);
    printf("CHIP2CHIP_LINK card=%d dbdf=%s rc=%d\n",
           CARD_ID, session.DBDF[CARD_ID], link_rc);
#ifdef LINK_ONLY
    MmSession_Close(&session);
    return link_rc == MM_API_SUCCESS ? 0 : 2;
#endif
#ifdef LOCAL_STAGE_TEST
    uint8_t stage_data[64], stage_readback[64];
    for (unsigned i = 0; i < sizeof(stage_data); ++i)
        stage_data[i] = (uint8_t)(i ^ 0xa5U);
    rc = dma_to_device(&session, CARD_ID, 0, (char *)stage_data,
                       sizeof(stage_data), 0x100000000ULL);
    printf("LOCAL_STAGE_H2C card=%d address=0x100000000 bytes=%zu rc=%d\n",
           CARD_ID, sizeof(stage_data), rc);
    if (rc != MM_API_SUCCESS) {
        MmSession_Close(&session);
        return 3;
    }
    memset(stage_readback, 0, sizeof(stage_readback));
    rc = dma_from_device(&session, CARD_ID, 0, (char *)stage_readback,
                         sizeof(stage_readback), 0x100000000ULL);
    int stage_match = rc == MM_API_SUCCESS &&
                      memcmp(stage_data, stage_readback, sizeof(stage_data)) == 0;
    printf("LOCAL_STAGE_C2H card=%d address=0x100000000 bytes=%zu rc=%d match=%d\n",
           CARD_ID, sizeof(stage_readback), rc, stage_match);
    MmSession_Close(&session);
    return stage_match ? 0 : 4;
#endif

    uint8_t *adapter_prefix = malloc(TRANSFER_BYTES);
    if (!adapter_prefix) {
        fprintf(stderr, "Cannot allocate adapter prefix buffer\n");
        MmSession_Close(&session);
        return 1;
    }
    FILE *adapter = fopen(ADAPTER_PATH, "rb");
    if (!adapter || fread(adapter_prefix, 1, TRANSFER_BYTES, adapter) !=
                        TRANSFER_BYTES) {
        fprintf(stderr, "Cannot read adapter prefix\n");
        if (adapter)
            fclose(adapter);
        free(adapter_prefix);
        MmSession_Close(&session);
        return 1;
    }
    fclose(adapter);

    rc = mm_dma_write(&session, CARD_ID, 0, adapter_prefix,
                      DDR_ADAPTER_BASE, TRANSFER_BYTES);
    printf("DDR_KNOWN_PREFIX_H2C address=0x%llx bytes=%u rc=%d\n",
           (unsigned long long)DDR_ADAPTER_BASE, TRANSFER_BYTES, rc);
    if (rc != MM_API_SUCCESS) {
        free(adapter_prefix);
        MmSession_Close(&session);
        return 1;
    }

    uint8_t *readback = malloc(TRANSFER_BYTES);
    if (!readback) {
        free(adapter_prefix);
        MmSession_Close(&session);
        return 1;
    }
    rc = mm_dma_read(&session, CARD_ID, 0, readback,
                     DDR_ADAPTER_BASE, TRANSFER_BYTES);
    int ddr_match = rc == MM_API_SUCCESS &&
                    memcmp(adapter_prefix, readback, TRANSFER_BYTES) == 0;
    printf("DDR_READBACK address=0x%llx bytes=%u rc=%d match=%d\n",
           (unsigned long long)DDR_ADAPTER_BASE, TRANSFER_BYTES, rc, ddr_match);
    free(readback);
    free(adapter_prefix);
    if (rc != MM_API_SUCCESS || !ddr_match) {
        MmSession_Close(&session);
        return 2;
    }

#if !TEST_CONTROL
    printf("CONTROL_TEST skipped\n");
    MmSession_Close(&session);
    return 0;
#endif

    uint32_t context_tokens = 512;
    rc = mm_dma_write(&session, CARD_ID, 0, (uint8_t *)&context_tokens,
                      CONTROL_BASE + 0x18, sizeof(context_tokens));
    printf("CONTROL_CONTEXT_H2C address=0x%llx bytes=%zu context_tokens=%u rc=%d\n",
           (unsigned long long)(CONTROL_BASE + 0x18), sizeof(context_tokens),
           context_tokens, rc);
    if (rc != MM_API_SUCCESS) {
        MmSession_Close(&session);
        return 1;
    }

    uint32_t readback_context = 0;
    rc = mm_dma_read(&session, CARD_ID, 0, (uint8_t *)&readback_context,
                     CONTROL_BASE + 0x18, sizeof(readback_context));
    if (rc == MM_API_SUCCESS)
        printf("CONTROL_CONTEXT_C2H address=0x%llx bytes=%zu value=%u\n",
               (unsigned long long)(CONTROL_BASE + 0x18), sizeof(readback_context),
               readback_context);
    else
        printf("CONTROL_CONTEXT_C2H address=0x%llx bytes=%zu rc=%d\n",
               (unsigned long long)(CONTROL_BASE + 0x18), sizeof(readback_context), rc);

    uint32_t status = 0;
    mmerrno status_rc = mm_dma_read(&session, CARD_ID, 0, (uint8_t *)&status,
                                    CONTROL_BASE + 0x04, sizeof(status));
    printf("CONTROL_STATUS_C2H address=0x%llx bytes=%zu value=0x%08x rc=%d\n",
           (unsigned long long)(CONTROL_BASE + 0x04), sizeof(status), status,
           status_rc);

    MmSession_Close(&session);
    return rc == MM_API_SUCCESS && readback_context == 512 &&
                   status_rc == MM_API_SUCCESS
               ? 0
               : 2;
}
