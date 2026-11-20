#define _FILE_OFFSET_BITS 64

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "mimic_api.h"
#include "mimic_dma.h"
#include "mimic_sdk.h"

#define CARD_ID 3
#define CONTROL_BASE 0x00d0000000ULL
#define DDR_TEST_ADDRESS 0x0f00000000ULL
#define DDR_TEST_BYTES 4096U
#define DIAG_BITSTREAM \
    "/root/fpga/plan6_huginn/diagnostic/plan6_axil_diag.bit"
#define RESTORE_BITSTREAM \
    "/root/fpga/plan6_huginn/app_shell_9p_wrapper.bit"

static mmerrno read_reg(MmSession *session, uint64_t address, uint32_t *value) {
    return mm_dma_read(session, CARD_ID, 0, (uint8_t *)value,
                       address, sizeof(*value));
}

static mmerrno write_reg(MmSession *session, uint64_t address, uint32_t value) {
    return mm_dma_write(session, CARD_ID, 0, (uint8_t *)&value,
                        address, sizeof(value));
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
    int diagnostic_programmed = 0;
    uint32_t magic = 0, status = 0, scratch = 0, counter_before = 0;
    const uint32_t scratch_pattern = 0x00000017U;
    mmerrno magic_rc = 0, status_rc = 0;
    mmerrno scratch_write_rc = 0, scratch_read_rc = 0, counter_rc = 0;
    mmerrno ddr_write_rc = 0, ddr_read_rc = 0;
    int ddr_match = 0;
    uint8_t write_buffer[DDR_TEST_BYTES];
    uint8_t read_buffer[DDR_TEST_BYTES];
    rc = MmSession_ScanFpgaDeviceNum(&session, &card_count);
    if (rc != MM_API_SUCCESS || CARD_ID >= (int)card_count) {
        fprintf(stderr, "CARD_UNAVAILABLE rc=%d count=%u\n", rc, card_count);
        MmSession_Close(&session);
        return 2;
    }
    printf("CARD id=%d dbdf=%s count=%u\n", CARD_ID,
           session.DBDF[CARD_ID], card_count);
    rc = is_gtx_interconnect_safe(&session, CARD_ID);
    printf("LINK before_program rc=%d\n", rc);
    if (rc != MM_API_SUCCESS)
        goto close_session;

    rc = program_fpga(&session, CARD_ID, 0, 1, DIAG_BITSTREAM);
    printf("PROGRAM diagnostic rc=%d\n", rc);
    if (rc != MM_API_SUCCESS)
        goto restore;
    diagnostic_programmed = 1;
    rc = is_gtx_interconnect_safe(&session, CARD_ID);
    printf("LINK after_program rc=%d\n", rc);

    magic_rc = read_reg(&session, CONTROL_BASE + 0x00, &magic);
    status_rc = read_reg(&session, CONTROL_BASE + 0x04, &status);
    printf("AXIL_MAGIC rc=%d value=0x%08x expected=0x4c515052\n",
           magic_rc, magic);
    printf("AXIL_STATUS rc=%d value=0x%08x expected=0xa11e0001\n",
           status_rc, status);

    scratch_write_rc = write_reg(&session, CONTROL_BASE + 0x08,
                                 scratch_pattern);
    scratch_read_rc = read_reg(&session, CONTROL_BASE + 0x08, &scratch);
    printf("AXIL_SCRATCH write_rc=%d read_rc=%d value=0x%08x expected=0x%08x\n",
           scratch_write_rc, scratch_read_rc, scratch, scratch_pattern);
    counter_rc = read_reg(&session, CONTROL_BASE + 0x0c, &counter_before);
    printf("AXIL_COUNTER rc=%d value=%u\n", counter_rc, counter_before);

    for (uint32_t i = 0; i < DDR_TEST_BYTES; ++i)
        write_buffer[i] = (uint8_t)((i * 37U + 0xa5U) & 0xffU);
    ddr_write_rc = mm_dma_write(&session, CARD_ID, 0, write_buffer,
                                DDR_TEST_ADDRESS, DDR_TEST_BYTES);
    if (ddr_write_rc == MM_API_SUCCESS) {
        memset(read_buffer, 0, sizeof(read_buffer));
        ddr_read_rc = mm_dma_read(&session, CARD_ID, 0, read_buffer,
                                  DDR_TEST_ADDRESS, DDR_TEST_BYTES);
        ddr_match = ddr_read_rc == MM_API_SUCCESS &&
                    memcmp(write_buffer, read_buffer, sizeof(write_buffer)) == 0;
    }
    printf("DDR_ROUNDTRIP address=0x%llx bytes=%u write_rc=%d read_rc=%d match=%d\n",
           (unsigned long long)DDR_TEST_ADDRESS, DDR_TEST_BYTES,
           ddr_write_rc, ddr_read_rc, ddr_match);

restore:
    rc = program_fpga(&session, CARD_ID, 0, 1, RESTORE_BITSTREAM);
    printf("PROGRAM restore rc=%d\n", rc);
    if (rc == MM_API_SUCCESS) {
        rc = is_gtx_interconnect_safe(&session, CARD_ID);
        printf("LINK after_restore rc=%d\n", rc);
    }

close_session:
    MmSession_Close(&session);
    if (rc != MM_API_SUCCESS)
        return 3;
    if (!diagnostic_programmed)
        return 5;
    if (magic_rc != MM_API_SUCCESS || magic != 0x4c515052U ||
        status_rc != MM_API_SUCCESS || status != 0xa11e0001U ||
        scratch_write_rc != MM_API_SUCCESS || scratch_read_rc != MM_API_SUCCESS ||
        scratch != scratch_pattern || counter_rc != MM_API_SUCCESS ||
        ddr_write_rc != MM_API_SUCCESS || ddr_read_rc != MM_API_SUCCESS ||
        !ddr_match)
        return 4;
    return 0;
}
