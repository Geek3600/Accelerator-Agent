#include <stdio.h>
#include <string.h>

#include "mimic_api.h"
#include "mimic_sdk.h"

#ifndef CARD_ID
#define CARD_ID 1
#endif

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
    dma_reset(&session, CARD_ID);
    sys_reset(&session, CARD_ID);
    rc = is_gtx_interconnect_safe(&session, CARD_ID);
    printf("RESET card=%d link_rc=%d\n", CARD_ID, rc);
    MmSession_Close(&session);
    return rc == MM_API_SUCCESS ? 0 : 1;
}
