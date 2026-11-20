#define _FILE_OFFSET_BITS 64

#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include "mimic_api.h"
#include "mimic_sdk.h"

#define CARD_ID 3
#define EXPECTED_DBDF "0000:32:00.0"
#define CONTROL_BASE 0x00d0000000ULL
#define SCRATCH_REG26 (CONTROL_BASE + 0x68)
#define OFFICIAL_BITSTREAM "/root/fpga/mimic_reference_app_shell_9p.bit"
#define RESTORE_BITSTREAM "/root/fpga/plan6_huginn/app_shell_9p_wrapper.bit"

static mmerrno read_register(MmSession *session, uint32_t *value) {
    return mm_dma_read(session, CARD_ID, 0, (uint8_t *)value,
                       SCRATCH_REG26, sizeof(*value));
}

static mmerrno write_register(MmSession *session, uint32_t value) {
    return mm_dma_write(session, CARD_ID, 0, (uint8_t *)&value,
                        SCRATCH_REG26, sizeof(value));
}

static mmerrno program_image(MmSession *session, const char *path) {
    mmerrno result = program_fpga(session, CARD_ID, 0, 1, path);
    if (result != MM_API_SUCCESS)
        return result;

    for (int attempt = 0; attempt < 30; ++attempt) {
        result = is_gtx_interconnect_safe(session, CARD_ID);
        if (result == MM_API_SUCCESS)
            return result;
        usleep(400000);
    }
    return result;
}

int main(void) {
    const uint32_t patterns[] = {0x5a3cc3a5U, 0xa5c33c5aU};
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
    printf("CARD id=%d dbdf=%s driver=%s\n", CARD_ID,
           session.DBDF[CARD_ID], session.Driver_identifer[CARD_ID]);

    int test_ok = 0;
    int official_programmed = 0;
    uint32_t original_value = 0;
    mmerrno official_rc = program_image(&session, OFFICIAL_BITSTREAM);
    printf("PROGRAM official rc=%d path=%s\n", official_rc, OFFICIAL_BITSTREAM);
    if (official_rc == MM_API_SUCCESS) {
        official_programmed = 1;
        result = read_register(&session, &original_value);
        printf("SCRATCH original rc=%d value=0x%08x address=0x%llx\n",
               result, original_value, (unsigned long long)SCRATCH_REG26);
        if (result == MM_API_SUCCESS) {
            test_ok = 1;
            for (size_t index = 0; index < sizeof(patterns) / sizeof(patterns[0]); ++index) {
                uint32_t readback = 0;
                mmerrno write_rc = write_register(&session, patterns[index]);
                mmerrno read_rc = write_rc == MM_API_SUCCESS ?
                                  read_register(&session, &readback) : write_rc;
                printf("SCRATCH pattern=%zu write_rc=%d read_rc=%d value=0x%08x expected=0x%08x\n",
                       index, write_rc, read_rc, readback, patterns[index]);
                if (write_rc != MM_API_SUCCESS || read_rc != MM_API_SUCCESS ||
                    readback != patterns[index])
                    test_ok = 0;
            }

            mmerrno restore_reg_rc = write_register(&session, original_value);
            uint32_t restored_value = 0;
            mmerrno verify_reg_rc = restore_reg_rc == MM_API_SUCCESS ?
                                    read_register(&session, &restored_value) : restore_reg_rc;
            printf("SCRATCH restore write_rc=%d read_rc=%d value=0x%08x expected=0x%08x\n",
                   restore_reg_rc, verify_reg_rc, restored_value, original_value);
            if (restore_reg_rc != MM_API_SUCCESS || verify_reg_rc != MM_API_SUCCESS ||
                restored_value != original_value)
                test_ok = 0;
        }
    }

    mmerrno restore_rc = program_image(&session, RESTORE_BITSTREAM);
    printf("PROGRAM restore rc=%d path=%s\n", restore_rc, RESTORE_BITSTREAM);
    uint32_t restored_status = 0, restored_context = 0;
    mmerrno status_rc = MM_API_ERR_CODE_EINVAL;
    mmerrno context_rc = MM_API_ERR_CODE_EINVAL;
    if (restore_rc == MM_API_SUCCESS) {
        status_rc = mm_dma_read(&session, CARD_ID, 0, (uint8_t *)&restored_status,
                                CONTROL_BASE + 0x04, sizeof(restored_status));
        context_rc = mm_dma_read(&session, CARD_ID, 0, (uint8_t *)&restored_context,
                                 CONTROL_BASE + 0x18, sizeof(restored_context));
    }
    printf("RESTORE_VERIFY status_rc=%d status=0x%08x context_rc=%d context=%u\n",
           status_rc, restored_status, context_rc, restored_context);

    MmSession_Close(&session);
    if (!official_programmed || !test_ok || restore_rc != MM_API_SUCCESS ||
        status_rc != MM_API_SUCCESS || context_rc != MM_API_SUCCESS)
        return 3;
    return 0;
}
