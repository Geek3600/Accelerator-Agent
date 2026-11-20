#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "mimic_api.h"
#include "mimic_dma.h"
#include "mimic_sdk.h"

#define CARD_ID 0
#define DDR_ADAPTER_BASE 0x0800000000ULL
#define DDR1_ENDPOINT_BASE 0x5000000000ULL
#define CHANNEL1_STATUS_ENDPOINT 0x40f0000004ULL
#define READ_BYTES 64
#define ADAPTER_PATH "/root/fpga/plan6_huginn/payload/adapter.usw512"

int main(void) {
    MmSession session;
    memset(&session, 0, sizeof(session));
    mmerrno result = MmSession_Open(&session);
    if (result != MM_API_SUCCESS) {
        fprintf(stderr, "MmSession_Open failed rc=%d\n", result);
        return 1;
    }

    uint8_t expected[READ_BYTES];
    uint8_t actual[READ_BYTES];
    FILE *payload = fopen(ADAPTER_PATH, "rb");
    if (!payload || fread(expected, 1, sizeof(expected), payload) != sizeof(expected)) {
        fprintf(stderr, "Cannot read adapter payload prefix\n");
        if (payload)
            fclose(payload);
        MmSession_Close(&session);
        return 1;
    }
    fclose(payload);

    result = mm_dma_read(&session, CARD_ID, 0, actual,
                         DDR_ADAPTER_BASE, sizeof(actual));
    if (result != MM_API_SUCCESS) {
        fprintf(stderr, "DDR read failed address=0x%llx bytes=%u rc=%d\n",
                (unsigned long long)DDR_ADAPTER_BASE,
                (unsigned)sizeof(actual), result);
    } else {
        unsigned mismatches = 0;
        for (unsigned index = 0; index < sizeof(actual); ++index)
            mismatches += actual[index] != expected[index];
        printf("DDR0_READBACK address=0x%llx bytes=%u mismatches=%u\n",
               (unsigned long long)DDR_ADAPTER_BASE,
               (unsigned)sizeof(actual), mismatches);
    }

    mmerrno channel1_result = dma_from_device(
        &session, CARD_ID, 1, (char *)actual, sizeof(actual),
        DDR1_ENDPOINT_BASE);
    printf("DDR1_CHANNEL1_READBACK address=0x%llx bytes=%u rc=%d first_bytes=%02x%02x%02x%02x\n",
           (unsigned long long)DDR1_ENDPOINT_BASE, (unsigned)sizeof(actual),
           channel1_result, actual[0], actual[1], actual[2], actual[3]);

    uint32_t channel1_status = 0;
    mmerrno status_result = dma_from_device(
        &session, CARD_ID, 1, (char *)&channel1_status, sizeof(channel1_status),
        CHANNEL1_STATUS_ENDPOINT);
    printf("CONTROL_CHANNEL1_READ address=0x%llx rc=%d value=0x%08x\n",
           (unsigned long long)CHANNEL1_STATUS_ENDPOINT, status_result,
           channel1_status);

    MmSession_Close(&session);
    return result == MM_API_SUCCESS && channel1_result == MM_API_SUCCESS &&
           status_result == MM_API_SUCCESS ? 0 : 1;
}
