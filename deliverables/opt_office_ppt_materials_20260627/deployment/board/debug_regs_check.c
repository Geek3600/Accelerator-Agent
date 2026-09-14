#include "mimic_api.h"
#include "mimic_sdk.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define DBG_BASE 0x1000000000ULL
#define EXPECT_MAGIC 0x0ACC2026U

static const uint32_t cfg_words[22] = {
    0x0000000f, 0x00000040, 0x00000000, 0x00000000,
    0x092f1400, 0x00000000, 0x00000000, 0x3f7ffed8,
    0x3a05c000, 0x39f62000, 0x3a0fc000, 0x3cc2e000,
    0x3d688000, 0x3ca78000, 0x3b20e4e0, 0x42fe0000,
    0x3c010204, 0x3a65e001, 0x3f7fff64, 0x39c82000,
    0x3b33a000, 0x3c982048
};

static int do_read(MmSession *session, int card, uint64_t offset, uint32_t *value)
{
    mmerrno ret = mm_fpga_read(session, card, 0, 0, offset, value);
    if (ret != MM_API_SUCCESS) {
        fprintf(stderr, "READ  offset=0x%llx failed ret=%d\n", (unsigned long long)offset, ret);
        return -1;
    }
    printf("READ  [0x%012llx] = 0x%08x\n", (unsigned long long)offset, *value);
    return 0;
}

static int do_write(MmSession *session, int card, uint64_t offset, uint32_t value)
{
    mmerrno ret = mm_fpga_write(session, card, 0, 0, offset, value);
    if (ret != MM_API_SUCCESS) {
        fprintf(stderr, "WRITE offset=0x%llx value=0x%08x failed ret=%d\n", (unsigned long long)offset, value, ret);
        return -1;
    }
    printf("WRITE [0x%012llx] = 0x%08x\n", (unsigned long long)offset, value);
    return 0;
}

static int open_card(MmSession *session, int *card)
{
    unsigned card_count = 0;
    mmerrno ret;
    memset(session, 0, sizeof(*session));
    ret = MmSession_Open(session);
    if (ret != MM_API_SUCCESS) {
        fprintf(stderr, "MmSession_Open failed ret=%d\n", ret);
        return -1;
    }
    ret = MmSession_ScanFpgaDeviceNum(session, &card_count);
    if (ret != MM_API_SUCCESS || card_count == 0) {
        fprintf(stderr, "ScanFpgaDeviceNum failed ret=%d card_count=%u\n", ret, card_count);
        return -1;
    }
    *card = 0;
    printf("FPGA card_count=%u, using card_id=0 channel_id=0\n", card_count);
    return 0;
}

static int check_magic(MmSession *session, int card)
{
    uint32_t value = 0;
    if (do_read(session, card, DBG_BASE + 0x68, &value) != 0)
        return -1;
    if (value != EXPECT_MAGIC) {
        fprintf(stderr, "MAGIC mismatch: got 0x%08x expected 0x%08x\n", value, EXPECT_MAGIC);
        return -1;
    }
    printf("MAGIC OK\n");
    return 0;
}

static int load_cfg(MmSession *session, int card)
{
    uint32_t value = 0;
    for (int i = 0; i < 22; ++i) {
        if (do_write(session, card, DBG_BASE + (uint64_t)i * 4, cfg_words[i]) != 0)
            return -1;
    }
    if (do_write(session, card, DBG_BASE + 0x60, 0x00000002) != 0)
        return -1;
    if (do_write(session, card, DBG_BASE + 0x64, 0x00000008) != 0)
        return -1;
    usleep(10000);
    if (do_read(session, card, DBG_BASE + 0x70, &value) != 0)
        return -1;
    printf("cfg_latch_count=%u start_count=%u\n", value & 0xffffu, value >> 16);
    return 0;
}

static int start_and_poll(MmSession *session, int card, int loops)
{
    uint32_t value = 0;
    if (do_write(session, card, DBG_BASE + 0x64, 0x00000001) != 0)
        return -1;
    usleep(10000);
    if (do_read(session, card, DBG_BASE + 0x70, &value) != 0)
        return -1;
    printf("cfg_latch_count=%u start_count=%u\n", value & 0xffffu, value >> 16);
    for (int i = 0; i < loops; ++i) {
        if (do_read(session, card, DBG_BASE + 0x64, &value) != 0)
            return -1;
        printf("poll=%d input_status=%u result_status=%u raw=0x%08x\n",
               i, value & 0x7u, (value >> 3) & 0x7u, value);
        if (((value >> 3) & 0x7u) != 0)
            break;
        usleep(200000);
    }
    return 0;
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "Usage: %s <magic|load_cfg|start|poll|clear|reset|all> [poll_loops]\n"
            "  Uses mimic SDK mm_fpga_read/write with DBG_BASE=0x1000000000.\n",
            prog);
}

int main(int argc, char **argv)
{
    MmSession session;
    int card = 0;
    const char *cmd = argc >= 2 ? argv[1] : "magic";
    int loops = argc >= 3 ? atoi(argv[2]) : 200;

    if (open_card(&session, &card) != 0)
        return 1;

    if (strcmp(cmd, "magic") == 0)
        return check_magic(&session, card) == 0 ? 0 : 1;
    if (strcmp(cmd, "load_cfg") == 0)
        return check_magic(&session, card) == 0 && load_cfg(&session, card) == 0 ? 0 : 1;
    if (strcmp(cmd, "start") == 0)
        return check_magic(&session, card) == 0 && start_and_poll(&session, card, loops) == 0 ? 0 : 1;
    if (strcmp(cmd, "poll") == 0) {
        uint32_t value = 0;
        for (int i = 0; i < loops; ++i) {
            if (do_read(&session, card, DBG_BASE + 0x64, &value) != 0)
                return 1;
            printf("poll=%d input_status=%u result_status=%u raw=0x%08x\n",
                   i, value & 0x7u, (value >> 3) & 0x7u, value);
            usleep(200000);
        }
        return 0;
    }
    if (strcmp(cmd, "clear") == 0)
        return do_write(&session, card, DBG_BASE + 0x64, 0x00000002) == 0 ? 0 : 1;
    if (strcmp(cmd, "reset") == 0)
        return do_write(&session, card, DBG_BASE + 0x64, 0x00000004) == 0 ? 0 : 1;
    if (strcmp(cmd, "all") == 0)
        return check_magic(&session, card) == 0 && load_cfg(&session, card) == 0 && start_and_poll(&session, card, loops) == 0 ? 0 : 1;

    usage(argv[0]);
    return 2;
}
