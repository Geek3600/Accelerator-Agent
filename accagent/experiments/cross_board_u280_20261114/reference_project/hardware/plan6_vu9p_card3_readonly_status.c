#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "mimic_api.h"
#include "mimic_sdk.h"

#define CARD_ID 3
#define EXPECTED_DBDF "0000:32:00.0"
#define CONTROL_BASE 0x00d0000000ULL

typedef struct {
    const char *name;
    uint64_t offset;
} reg_entry_t;

static const reg_entry_t registers[] = {
    {"status", 0x04},
    {"cycles_low", 0x08},
    {"cycles_high", 0x0c},
    {"nonzero_chunks", 0x10},
    {"output_digest", 0x14},
    {"context_tokens", 0x18},
    {"scratch26", 0x68},
};

int main(void) {
    setvbuf(stdout, NULL, _IOLBF, 0);
    MmSession session;
    memset(&session, 0, sizeof(session));
    mmerrno result = MmSession_Open(&session);
    if (result != MM_API_SUCCESS) {
        printf("SESSION_OPEN rc=%d\n", result);
        return 1;
    }

    unsigned card_count = 0;
    result = MmSession_ScanFpgaDeviceNum(&session, &card_count);
    if (result != MM_API_SUCCESS || CARD_ID >= (int)card_count ||
        strcmp(session.DBDF[CARD_ID], EXPECTED_DBDF) != 0) {
        printf("CARD_CHECK rc=%d count=%u id=%d dbdf=%s expected=%s\n",
               result, card_count, CARD_ID,
               CARD_ID < (int)card_count ? session.DBDF[CARD_ID] : "unavailable",
               EXPECTED_DBDF);
        MmSession_Close(&session);
        return 2;
    }

    mmerrno link_rc = is_gtx_interconnect_safe(&session, CARD_ID);
    printf("CARD id=%d dbdf=%s driver=%s link_rc=%d\n", CARD_ID,
           session.DBDF[CARD_ID], session.Driver_identifer[CARD_ID], link_rc);

    int read_error = 0;
    for (size_t index = 0; index < sizeof(registers) / sizeof(registers[0]); ++index) {
        uint32_t value = 0;
        mmerrno read_rc = mm_dma_read(&session, CARD_ID, 0, (uint8_t *)&value,
                                      CONTROL_BASE + registers[index].offset,
                                      sizeof(value));
        printf("READ name=%s address=0x%llx rc=%d value=0x%08x\n",
               registers[index].name,
               (unsigned long long)(CONTROL_BASE + registers[index].offset),
               read_rc, value);
        if (read_rc != MM_API_SUCCESS)
            read_error = 1;
    }

    MmSession_Close(&session);
    return read_error ? 3 : 0;
}
