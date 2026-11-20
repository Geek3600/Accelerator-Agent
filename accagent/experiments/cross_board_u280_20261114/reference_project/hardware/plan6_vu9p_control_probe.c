#define _FILE_OFFSET_BITS 64

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "mimic_api.h"
#include "mimic_dma.h"
#include "mimic_sdk.h"

#ifndef CARD_ID
#define CARD_ID 1
#endif

typedef struct {
    const char *name;
    unsigned channel;
    uint64_t address;
    uint32_t bytes;
    int use_absolute_address;
} probe_t;

static const probe_t probes[] = {
    {"program_ddr_raw_ch0", 0, 0x100000000ULL, 64, 1},
    {"ddr1_ch1", 1, 0x5000000000ULL, 64, 1},
};

int main(void) {
    MmSession session;
    memset(&session, 0, sizeof(session));
    mmerrno rc = MmSession_Open(&session);
    if (rc != MM_API_SUCCESS) {
        fprintf(stderr, "MmSession_Open failed rc=%d\n", rc);
        return 1;
    }
    unsigned count = 0;
    rc = MmSession_ScanFpgaDeviceNum(&session, &count);
    if (rc != MM_API_SUCCESS || CARD_ID >= (int)count) {
        fprintf(stderr, "Card unavailable rc=%d count=%u\n", rc, count);
        MmSession_Close(&session);
        return 1;
    }
    setvbuf(stdout, NULL, _IOLBF, 0);
    for (unsigned i = 0; i < sizeof(probes) / sizeof(probes[0]); ++i) {
        uint8_t data[64] = {0};
        const probe_t *probe = &probes[i];
        if (probe->use_absolute_address)
            rc = dma_from_device(&session, CARD_ID, probe->channel,
                                 (char *)data, probe->bytes, probe->address);
        else
            rc = mm_dma_read(&session, CARD_ID, probe->channel, data,
                             probe->address, probe->bytes);
        uint32_t first_word = 0;
        memcpy(&first_word, data, sizeof(first_word));
        printf("READ_PROBE card=%d name=%s channel=%u address=0x%llx bytes=%u rc=%d first_word=0x%08x\n",
               CARD_ID, probe->name, probe->channel,
               (unsigned long long)probe->address, probe->bytes, rc, first_word);
    }
    MmSession_Close(&session);
    return 0;
}
