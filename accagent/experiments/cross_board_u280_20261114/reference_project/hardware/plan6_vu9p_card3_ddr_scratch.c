#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "mimic_api.h"
#include "mimic_dma.h"
#include "mimic_sdk.h"

#define CARD_ID 3
#define SCRATCH_ADDRESS 0x0f00000000ULL
#define TEST_BYTES 64U

int main(void) {
    MmSession session;
    uint8_t original[TEST_BYTES];
    uint8_t pattern[TEST_BYTES];
    uint8_t readback[TEST_BYTES];
    memset(&session, 0, sizeof(session));

    mmerrno rc = MmSession_Open(&session);
    if (rc != MM_API_SUCCESS) {
        printf("SESSION rc=%d\n", rc);
        return 1;
    }

    unsigned card_count = 0;
    rc = MmSession_ScanFpgaDeviceNum(&session, &card_count);
    if (rc != MM_API_SUCCESS || CARD_ID >= (int)card_count) {
        printf("CARD rc=%d count=%u\n", rc, card_count);
        MmSession_Close(&session);
        return 2;
    }
    printf("CARD id=%d dbdf=%s count=%u\n", CARD_ID,
           session.DBDF[CARD_ID], card_count);

    rc = mm_dma_read(&session, CARD_ID, 0, original,
                     SCRATCH_ADDRESS, TEST_BYTES);
    printf("SCRATCH_SAVE address=0x%llx bytes=%u rc=%d\n",
           (unsigned long long)SCRATCH_ADDRESS, TEST_BYTES, rc);
    if (rc != MM_API_SUCCESS) {
        MmSession_Close(&session);
        return 3;
    }

    for (unsigned i = 0; i < TEST_BYTES; ++i)
        pattern[i] = (uint8_t)(0x5bU ^ (i * 29U));
    mmerrno write_rc = mm_dma_write(&session, CARD_ID, 0, pattern,
                                    SCRATCH_ADDRESS, TEST_BYTES);
    memset(readback, 0, sizeof(readback));
    mmerrno read_rc = MM_API_ERR_READ_DMA_FAILED_ERR;
    int match = 0;
    if (write_rc == MM_API_SUCCESS) {
        read_rc = mm_dma_read(&session, CARD_ID, 0, readback,
                              SCRATCH_ADDRESS, TEST_BYTES);
        match = read_rc == MM_API_SUCCESS &&
                memcmp(pattern, readback, TEST_BYTES) == 0;
    }
    printf("SCRATCH_ROUNDTRIP write_rc=%d read_rc=%d match=%d\n",
           write_rc, read_rc, match);

    mmerrno restore_rc = mm_dma_write(&session, CARD_ID, 0, original,
                                      SCRATCH_ADDRESS, TEST_BYTES);
    memset(readback, 0, sizeof(readback));
    mmerrno verify_rc = MM_API_ERR_READ_DMA_FAILED_ERR;
    int restored = 0;
    if (restore_rc == MM_API_SUCCESS) {
        verify_rc = mm_dma_read(&session, CARD_ID, 0, readback,
                                SCRATCH_ADDRESS, TEST_BYTES);
        restored = verify_rc == MM_API_SUCCESS &&
                   memcmp(original, readback, TEST_BYTES) == 0;
    }
    printf("SCRATCH_RESTORE write_rc=%d read_rc=%d match=%d\n",
           restore_rc, verify_rc, restored);

    MmSession_Close(&session);
    return match && restored ? 0 : 4;
}
