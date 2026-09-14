#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define CTRL_BASE 0x3000000000ULL
#define DDR_BASE 0x2800000000ULL
#define OUTPUT_ABS 0x28092f1000ULL
#define INPUT_SIZE_BYTES 65536ULL
#define DDR_IMAGE_SIZE_BYTES 154080256ULL
#define OUTPUT_READ_BYTES 1024ULL

static const uint32_t cfg_words[22] = {
    0x0000000f, 0x00000040, 0x00000000, 0x00000000,
    0x092f1000, 0x00000000, 0x00000000, 0x3f7ffed8,
    0x3a05c000, 0x39f62000, 0x3a0fc000, 0x3cc2e000,
    0x3d688000, 0x3ca78000, 0x3b20e4e0, 0x42fe0000,
    0x3c010204, 0x3a65e001, 0x3f7fff64, 0x39c82000,
    0x3b33a000, 0x3c982048
};

static uint64_t now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static int write_full(int fd, uint64_t addr, const void *buf, size_t size)
{
    const uint8_t *ptr = (const uint8_t *)buf;
    size_t done = 0;
    while (done < size) {
        ssize_t rc = pwrite(fd, ptr + done, size - done, (off_t)(addr + done));
        if (rc < 0) {
            fprintf(stderr, "pwrite addr=0x%llx size=%zu failed: %s\n",
                    (unsigned long long)(addr + done), size - done, strerror(errno));
            return -1;
        }
        if (rc == 0) {
            fprintf(stderr, "pwrite addr=0x%llx returned 0\n", (unsigned long long)(addr + done));
            return -1;
        }
        done += (size_t)rc;
    }
    return 0;
}

static int read_full(int fd, uint64_t addr, void *buf, size_t size)
{
    uint8_t *ptr = (uint8_t *)buf;
    size_t done = 0;
    while (done < size) {
        ssize_t rc = pread(fd, ptr + done, size - done, (off_t)(addr + done));
        if (rc < 0) {
            fprintf(stderr, "pread addr=0x%llx size=%zu failed: %s\n",
                    (unsigned long long)(addr + done), size - done, strerror(errno));
            return -1;
        }
        if (rc == 0) {
            fprintf(stderr, "pread addr=0x%llx returned 0\n", (unsigned long long)(addr + done));
            return -1;
        }
        done += (size_t)rc;
    }
    return 0;
}

static int write_u32(int h2c_fd, uint64_t addr, uint32_t value)
{
    return write_full(h2c_fd, addr, &value, sizeof(value));
}

static int read_u32(int c2h_fd, uint64_t addr, uint32_t *value)
{
    return read_full(c2h_fd, addr, value, sizeof(*value));
}

static void sleep_us(unsigned usec)
{
    struct timespec ts;
    ts.tv_sec = usec / 1000000U;
    ts.tv_nsec = (long)(usec % 1000000U) * 1000L;
    nanosleep(&ts, NULL);
}

static int load_file_region(int fd, int h2c_fd, uint64_t dst_addr, uint64_t bytes)
{
    const size_t chunk_size = 4 * 1024 * 1024;
    uint8_t *buf = (uint8_t *)malloc(chunk_size);
    uint64_t done = 0;
    if (!buf) {
        fprintf(stderr, "malloc %zu failed\n", chunk_size);
        return -1;
    }
    while (done < bytes) {
        size_t chunk = (bytes - done) > chunk_size ? chunk_size : (size_t)(bytes - done);
        ssize_t rc = read(fd, buf, chunk);
        if (rc != (ssize_t)chunk) {
            fprintf(stderr, "input file read failed at 0x%llx: rc=%zd errno=%s\n",
                    (unsigned long long)done, rc, strerror(errno));
            free(buf);
            return -1;
        }
        if (write_full(h2c_fd, dst_addr + done, buf, chunk) != 0) {
            free(buf);
            return -1;
        }
        done += chunk;
    }
    free(buf);
    return 0;
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "Usage: sudo %s [runs] [poll_timeout_ms] [write_input_mode] [poison_output]\n"
            "  runs            default 20\n"
            "  poll_timeout_ms default 1000\n"
            "  write_input_mode: 0=no input write, 1=write first 64KB from DDR image, 2=write full DDR image\n"
            "  poison_output: 0=do not modify output area, 1=poison 1KB output area before each run; default 0\n"
            "Env:\n"
            "  XDMA_ID default 1\n"
            "  DDR_IMAGE default /home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin\n"
            "Notes:\n"
            "  host_start_to_result_ns measures from just before reg25 start write to first status read with result_status!=0.\n"
            "  hw_latency_cycles_reg31 is only meaningful on the new debug-latency bit; old bit may return an ordinary register value.\n",
            prog);
}

int main(int argc, char **argv)
{
    int runs = argc > 1 ? atoi(argv[1]) : 20;
    int poll_timeout_ms = argc > 2 ? atoi(argv[2]) : 1000;
    int write_input_mode = argc > 3 ? atoi(argv[3]) : 0;
    int poison_output = argc > 4 ? atoi(argv[4]) : 0;
    const char *xdma_id = getenv("XDMA_ID") ? getenv("XDMA_ID") : "1";
    const char *ddr_image = getenv("DDR_IMAGE") ? getenv("DDR_IMAGE") : "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin";
    char h2c_path[128];
    char c2h_path[128];
    int h2c_fd = -1;
    int c2h_fd = -1;
    uint8_t poison[OUTPUT_READ_BYTES];
    uint8_t output[OUTPUT_READ_BYTES];

    if (runs <= 0 || poll_timeout_ms <= 0 || write_input_mode < 0 || write_input_mode > 2 ||
        poison_output < 0 || poison_output > 1) {
        usage(argv[0]);
        return 2;
    }

    snprintf(h2c_path, sizeof(h2c_path), "/dev/xdma%s_h2c_0", xdma_id);
    snprintf(c2h_path, sizeof(c2h_path), "/dev/xdma%s_c2h_0", xdma_id);
    h2c_fd = open(h2c_path, O_RDWR | O_SYNC);
    c2h_fd = open(c2h_path, O_RDWR | O_SYNC);
    if (h2c_fd < 0 || c2h_fd < 0) {
        fprintf(stderr, "open %s/%s failed: %s\n", h2c_path, c2h_path, strerror(errno));
        return 1;
    }

    memset(poison, 0xa5, sizeof(poison));

    if (write_input_mode != 0) {
        int image_fd = open(ddr_image, O_RDONLY);
        uint64_t bytes = write_input_mode == 1 ? INPUT_SIZE_BYTES : DDR_IMAGE_SIZE_BYTES;
        uint64_t t0 = now_ns();
        if (image_fd < 0) {
            fprintf(stderr, "open DDR_IMAGE %s failed: %s\n", ddr_image, strerror(errno));
            return 1;
        }
        if (load_file_region(image_fd, h2c_fd, DDR_BASE, bytes) != 0) {
            close(image_fd);
            return 1;
        }
        close(image_fd);
        printf("input_write_mode=%d bytes=%llu host_input_write_ns=%llu\n",
               write_input_mode, (unsigned long long)bytes, (unsigned long long)(now_ns() - t0));
    }

    printf("runs=%d poll_timeout_ms=%d xdma_id=%s\n", runs, poll_timeout_ms, xdma_id);
    printf("run,host_start_to_result_ns,poll_reads,status_raw,input_status,result_status,hw_latency_cycles_reg31,output_hash32\n");

    for (int run = 1; run <= runs; ++run) {
        uint32_t status = 0;
        uint32_t hw_cycles = 0;
        uint32_t hash = 2166136261u;
        int poll_reads = 0;
        int got = 0;
        uint64_t t_start;
        uint64_t t_done = 0;
        uint64_t deadline;

        if (poison_output) {
            if (write_full(h2c_fd, OUTPUT_ABS, poison, sizeof(poison)) != 0)
                return 1;
        }

        if (write_u32(h2c_fd, CTRL_BASE + 0x64, 0x00000004) != 0)
            return 1;
        sleep_us(200000);
        if (write_u32(h2c_fd, CTRL_BASE + 0x64, 0x00000002) != 0)
            return 1;
        sleep_us(200000);
        for (int i = 0; i < 22; ++i) {
            if (write_u32(h2c_fd, CTRL_BASE + (uint64_t)i * 4, cfg_words[i]) != 0)
                return 1;
        }
        if (write_u32(h2c_fd, CTRL_BASE + 0x60, 0x00000002) != 0)
            return 1;
        if (write_u32(h2c_fd, CTRL_BASE + 0x64, 0x00000008) != 0)
            return 1;
        sleep_us(200000);

        t_start = now_ns();
        if (write_u32(h2c_fd, CTRL_BASE + 0x64, 0x00000001) != 0)
            return 1;
        deadline = t_start + (uint64_t)poll_timeout_ms * 1000000ULL;

        while (now_ns() < deadline) {
            if (read_u32(c2h_fd, CTRL_BASE + 0x64, &status) != 0)
                return 1;
            ++poll_reads;
            if (((status >> 3) & 0x7u) != 0) {
                t_done = now_ns();
                got = 1;
                break;
            }
        }

        read_u32(c2h_fd, CTRL_BASE + 0x7c, &hw_cycles);
        if (read_full(c2h_fd, OUTPUT_ABS, output, sizeof(output)) != 0)
            return 1;
        for (size_t i = 0; i < sizeof(output); ++i) {
            hash ^= output[i];
            hash *= 16777619u;
        }

        printf("%d,%llu,%d,0x%08x,%u,%u,0x%08x,0x%08x%s\n",
               run,
               (unsigned long long)(got ? (t_done - t_start) : 0),
               poll_reads,
               status,
               status & 0x7u,
               (status >> 3) & 0x7u,
               hw_cycles,
               hash,
               got ? "" : ",TIMEOUT");
        fflush(stdout);
        if (!got)
            return 2;
    }

    close(h2c_fd);
    close(c2h_fd);
    return 0;
}
