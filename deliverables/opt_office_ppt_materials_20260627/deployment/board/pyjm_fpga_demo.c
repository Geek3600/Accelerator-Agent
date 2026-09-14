#define _GNU_SOURCE
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define CTRL_BASE 0x3000000000ULL
#define DDR_BASE 0x2800000000ULL
#define ACC_OUTPUT_ABS 0x28092f1000ULL
#define DDR_IMAGE_SIZE_BYTES 154080256ULL
#define INPUT_SIZE_BYTES 65536ULL
#define EXPECT_MAGIC 0x0ACC2026U

#define DEFAULT_RAW_OUTPUT_BYTES 1024U
#define MAX_RAW_OUTPUT_BYTES 65536U
#define PASSWORD_RECORD_BYTES 256U
#define PATTERN_FIELD_OFF 0x40U
#define PATTERN_FIELD_BYTES 64U
#define PASSWORD_FIELD_OFF 0x80U
#define PASSWORD_FIELD_BYTES 128U

static const uint32_t cfg_words[22] = {
    0x0000000f, 0x00000040, 0x00000000, 0x00000000,
    0x092f1000, 0x00000000, 0x00000000, 0x3f7ffed8,
    0x3a05c000, 0x39f62000, 0x3a0fc000, 0x3cc2e000,
    0x3d688000, 0x3ca78000, 0x3b20e4e0, 0x42fe0000,
    0x3c010204, 0x3a65e001, 0x3f7fff64, 0x39c82000,
    0x3b33a000, 0x3c982048
};

struct run_result {
    uint32_t status;
    uint32_t hw_cycles;
    uint32_t output_hash;
    uint64_t host_latency_ns;
    int poll_reads;
};

struct options {
    int runs;
    int poll_timeout_ms;
    int write_input_mode;
    int check_magic;
    int write_password_record;
    int password_len;
    uint32_t nonce;
    uint64_t password_base;
    size_t raw_output_bytes;
    char pattern[128];
};

static uint64_t now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static void sleep_us(unsigned usec)
{
    struct timespec ts;
    ts.tv_sec = usec / 1000000U;
    ts.tv_nsec = (long)(usec % 1000000U) * 1000L;
    nanosleep(&ts, NULL);
}

static int parse_u64(const char *s, uint64_t *value)
{
    char *end = NULL;
    errno = 0;
    *value = strtoull(s, &end, 0);
    return errno == 0 && end != s && *end == '\0';
}

static int parse_int(const char *s, int *value)
{
    char *end = NULL;
    long v;
    errno = 0;
    v = strtol(s, &end, 0);
    if (errno != 0 || end == s || *end != '\0')
        return 0;
    *value = (int)v;
    return 1;
}

static int parse_u32_arg(const char *s, uint32_t *value)
{
    uint64_t uv = 0;
    if (!parse_u64(s, &uv) || uv > 0xffffffffULL)
        return 0;
    *value = (uint32_t)uv;
    return 1;
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
            fprintf(stderr, "pwrite addr=0x%llx returned 0\n",
                    (unsigned long long)(addr + done));
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
            fprintf(stderr, "pread addr=0x%llx returned 0\n",
                    (unsigned long long)(addr + done));
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

static uint32_t fnv1a32(const uint8_t *buf, size_t size)
{
    uint32_t hash = 2166136261u;
    for (size_t i = 0; i < size; ++i) {
        hash ^= buf[i];
        hash *= 16777619u;
    }
    return hash;
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

static void put_u32_le(uint8_t *buf, size_t off, uint32_t value)
{
    buf[off + 0] = (uint8_t)(value & 0xffu);
    buf[off + 1] = (uint8_t)((value >> 8) & 0xffu);
    buf[off + 2] = (uint8_t)((value >> 16) & 0xffu);
    buf[off + 3] = (uint8_t)((value >> 24) & 0xffu);
}

static void put_u64_le(uint8_t *buf, size_t off, uint64_t value)
{
    put_u32_le(buf, off, (uint32_t)(value & 0xffffffffULL));
    put_u32_le(buf, off + 4, (uint32_t)(value >> 32));
}

static char pick_char(const char *set, const uint8_t *raw, size_t raw_size,
                      uint32_t *state, size_t pos)
{
    size_t set_len = strlen(set);
    uint8_t b = raw[(pos * 17U + (*state & 0xffU)) % raw_size];
    *state ^= (uint32_t)b + 0x9e3779b9u + (uint32_t)(pos << 6) + (uint32_t)(pos >> 2);
    *state *= 16777619u;
    return set[*state % set_len];
}

static void append_pattern_chars(char kind, int count, const uint8_t *raw, size_t raw_size,
                                 uint32_t *state, char *out, size_t *out_len, size_t max_len)
{
    static const char letters[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
    static const char digits[] = "0123456789";
    static const char specials[] = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~";
    static const char uppers[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    static const char lowers[] = "abcdefghijklmnopqrstuvwxyz";
    const char *set = letters;

    if (kind == 'N')
        set = digits;
    else if (kind == 'S')
        set = specials;
    else if (kind == 'U')
        set = uppers;
    else if (kind == 'l')
        set = lowers;

    for (int i = 0; i < count && *out_len < max_len; ++i) {
        out[*out_len] = pick_char(set, raw, raw_size, state, *out_len);
        ++(*out_len);
    }
}

static int generate_password_from_pattern(const char *pattern, int requested_len,
                                          const uint8_t *raw, size_t raw_size,
                                          uint32_t hash, uint32_t nonce,
                                          char *out, size_t out_cap)
{
    const char *p = pattern;
    size_t out_len = 0;
    int parsed_any = 0;
    uint32_t state = hash ^ 0x50594a4du ^ (nonce * 0x9e3779b1u);

    if (out_cap == 0 || raw_size == 0)
        return -1;

    while (*p != '\0' && out_len + 1 < out_cap) {
        char kind;
        int count = 0;
        while (isspace((unsigned char)*p))
            ++p;
        kind = *p;
        if (!(kind == 'L' || kind == 'N' || kind == 'S' || kind == 'U' || kind == 'l'))
            break;
        ++p;
        while (isdigit((unsigned char)*p)) {
            count = count * 10 + (*p - '0');
            ++p;
        }
        if (count <= 0)
            break;
        parsed_any = 1;
        append_pattern_chars(kind, count, raw, raw_size, &state, out, &out_len, out_cap - 1);
    }

    if (!parsed_any) {
        int fallback_len = requested_len > 0 ? requested_len : 12;
        for (int i = 0; i < fallback_len && out_len + 1 < out_cap; ++i)
            append_pattern_chars('L', 1, raw, raw_size, &state, out, &out_len, out_cap - 1);
    } else if (requested_len > 0) {
        while ((int)out_len < requested_len && out_len + 1 < out_cap)
            append_pattern_chars('L', 1, raw, raw_size, &state, out, &out_len, out_cap - 1);
    }

    out[out_len] = '\0';
    return (int)out_len;
}

static int write_password_record(int h2c_fd, int c2h_fd, uint64_t addr,
                                 const char *pattern, const char *password,
                                 const struct run_result *rr)
{
    uint8_t rec[PASSWORD_RECORD_BYTES];
    uint8_t verify[16];
    size_t pattern_len = strlen(pattern);
    size_t password_len = strlen(password);

    memset(rec, 0, sizeof(rec));
    memcpy(rec + 0x00, "PYJM", 4);
    put_u32_le(rec, 0x04, 1); /* version */
    put_u32_le(rec, 0x08, 1); /* valid */
    put_u32_le(rec, 0x0c, 1); /* record count */
    put_u32_le(rec, 0x10, (uint32_t)password_len);
    put_u32_le(rec, 0x14, (uint32_t)pattern_len);
    put_u32_le(rec, 0x18, rr->output_hash);
    put_u32_le(rec, 0x1c, rr->hw_cycles);
    put_u64_le(rec, 0x20, rr->host_latency_ns);
    put_u64_le(rec, 0x28, ACC_OUTPUT_ABS);
    put_u32_le(rec, 0x30, PASSWORD_RECORD_BYTES);

    if (pattern_len >= PATTERN_FIELD_BYTES)
        pattern_len = PATTERN_FIELD_BYTES - 1;
    if (password_len >= PASSWORD_FIELD_BYTES)
        password_len = PASSWORD_FIELD_BYTES - 1;
    memcpy(rec + PATTERN_FIELD_OFF, pattern, pattern_len);
    memcpy(rec + PASSWORD_FIELD_OFF, password, password_len);

    if (write_full(h2c_fd, addr, rec, sizeof(rec)) != 0)
        return -1;
    if (read_full(c2h_fd, addr, verify, sizeof(verify)) != 0)
        return -1;
    if (memcmp(verify, rec, sizeof(verify)) != 0) {
        fprintf(stderr, "password record verify failed at addr=0x%llx\n",
                (unsigned long long)addr);
        return -1;
    }
    return 0;
}

static int check_debug_magic(int c2h_fd)
{
    uint32_t magic = 0;
    if (read_u32(c2h_fd, CTRL_BASE + 0x68, &magic) != 0)
        return -1;
    printf("debug_magic=0x%08x\n", magic);
    if (magic != EXPECT_MAGIC) {
        fprintf(stderr, "debug magic mismatch: got 0x%08x expected 0x%08x\n",
                magic, EXPECT_MAGIC);
        return -1;
    }
    return 0;
}

static int run_accelerator_once(int h2c_fd, int c2h_fd, int poll_timeout_ms,
                                uint8_t *raw_output, size_t raw_output_bytes,
                                struct run_result *rr)
{
    uint64_t t_start;
    uint64_t t_done = 0;
    uint64_t deadline;
    int got = 0;

    memset(rr, 0, sizeof(*rr));

    if (write_u32(h2c_fd, CTRL_BASE + 0x64, 0x00000004) != 0)
        return -1;
    sleep_us(200000);
    if (write_u32(h2c_fd, CTRL_BASE + 0x64, 0x00000002) != 0)
        return -1;
    sleep_us(200000);
    for (int i = 0; i < 22; ++i) {
        if (write_u32(h2c_fd, CTRL_BASE + (uint64_t)i * 4, cfg_words[i]) != 0)
            return -1;
    }
    if (write_u32(h2c_fd, CTRL_BASE + 0x60, 0x00000002) != 0)
        return -1;
    if (write_u32(h2c_fd, CTRL_BASE + 0x64, 0x00000008) != 0)
        return -1;
    sleep_us(200000);

    t_start = now_ns();
    if (write_u32(h2c_fd, CTRL_BASE + 0x64, 0x00000001) != 0)
        return -1;
    deadline = t_start + (uint64_t)poll_timeout_ms * 1000000ULL;

    while (now_ns() < deadline) {
        if (read_u32(c2h_fd, CTRL_BASE + 0x64, &rr->status) != 0)
            return -1;
        ++rr->poll_reads;
        if (((rr->status >> 3) & 0x7u) != 0) {
            t_done = now_ns();
            got = 1;
            break;
        }
    }

    if (read_u32(c2h_fd, CTRL_BASE + 0x7c, &rr->hw_cycles) != 0)
        return -1;
    if (read_full(c2h_fd, ACC_OUTPUT_ABS, raw_output, raw_output_bytes) != 0)
        return -1;
    rr->output_hash = fnv1a32(raw_output, raw_output_bytes);
    rr->host_latency_ns = got ? (t_done - t_start) : 0;
    return got ? 0 : 1;
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "Usage: sudo %s [options]\n"
            "Options:\n"
            "  --runs N                  accelerator runs before writing password record, default 1\n"
            "  --poll-timeout-ms N       poll timeout per run, default 1000\n"
            "  --write-ddr-mode N        0=no write, 1=first 64KB, 2=full image; default 0\n"
            "  --pattern TEXT            pattern used for demo password, default env PATTERN or L8\n"
            "  --password-len N          override/minimum password length, default pattern-derived\n"
            "  --nonce N                 per-attempt nonce mixed into demo password generation, default 0\n"
            "  --password-base ADDR      absolute DDR address for password record, default 0x%llx\n"
            "  --raw-output-bytes N      raw accelerator output bytes to hash, default %u\n"
            "  --no-magic-check          skip reg26 magic check\n"
            "  --no-password-record      do not write final DDR password record\n"
            "  -h, --help                show this help\n"
            "Env:\n"
            "  XDMA_ID                   default 7\n"
            "  DDR_IMAGE                 default /home/hyyuan/pyjm12_demo/ddr_image.u32.bin\n"
            "  PATTERN                   default L8\n",
            prog, (unsigned long long)ACC_OUTPUT_ABS, DEFAULT_RAW_OUTPUT_BYTES);
}

static int parse_options(int argc, char **argv, struct options *opt)
{
    static const struct option long_opts[] = {
        {"runs", required_argument, NULL, 1},
        {"poll-timeout-ms", required_argument, NULL, 2},
        {"write-ddr-mode", required_argument, NULL, 3},
        {"pattern", required_argument, NULL, 4},
        {"password-len", required_argument, NULL, 5},
        {"password-base", required_argument, NULL, 6},
        {"raw-output-bytes", required_argument, NULL, 7},
        {"no-magic-check", no_argument, NULL, 8},
        {"no-password-record", no_argument, NULL, 9},
        {"nonce", required_argument, NULL, 10},
        {"help", no_argument, NULL, 'h'},
        {NULL, 0, NULL, 0},
    };
    const char *env_pattern = getenv("PATTERN");
    int c;

    opt->runs = 1;
    opt->poll_timeout_ms = 1000;
    opt->write_input_mode = 0;
    opt->check_magic = 1;
    opt->write_password_record = 1;
    opt->password_len = 0;
    opt->nonce = 0;
    opt->password_base = ACC_OUTPUT_ABS;
    opt->raw_output_bytes = DEFAULT_RAW_OUTPUT_BYTES;
    snprintf(opt->pattern, sizeof(opt->pattern), "%s", env_pattern ? env_pattern : "L8");

    while ((c = getopt_long(argc, argv, "h", long_opts, NULL)) != -1) {
        int iv = 0;
        uint64_t uv = 0;
        switch (c) {
        case 1:
            if (!parse_int(optarg, &opt->runs))
                return -1;
            break;
        case 2:
            if (!parse_int(optarg, &opt->poll_timeout_ms))
                return -1;
            break;
        case 3:
            if (!parse_int(optarg, &opt->write_input_mode))
                return -1;
            break;
        case 4:
            snprintf(opt->pattern, sizeof(opt->pattern), "%s", optarg);
            break;
        case 5:
            if (!parse_int(optarg, &opt->password_len))
                return -1;
            break;
        case 6:
            if (!parse_u64(optarg, &uv))
                return -1;
            opt->password_base = uv;
            break;
        case 7:
            if (!parse_int(optarg, &iv))
                return -1;
            opt->raw_output_bytes = (size_t)iv;
            break;
        case 8:
            opt->check_magic = 0;
            break;
        case 9:
            opt->write_password_record = 0;
            break;
        case 10:
            if (!parse_u32_arg(optarg, &opt->nonce))
                return -1;
            break;
        case 'h':
            usage(argv[0]);
            exit(0);
        default:
            return -1;
        }
    }

    if (opt->runs <= 0 || opt->poll_timeout_ms <= 0 ||
        opt->write_input_mode < 0 || opt->write_input_mode > 2 ||
        opt->password_len < 0 ||
        opt->raw_output_bytes == 0 || opt->raw_output_bytes > MAX_RAW_OUTPUT_BYTES) {
        return -1;
    }
    return 0;
}

int main(int argc, char **argv)
{
    struct options opt;
    struct run_result rr;
    const char *xdma_id = getenv("XDMA_ID") ? getenv("XDMA_ID") : "7";
    const char *ddr_image = getenv("DDR_IMAGE") ? getenv("DDR_IMAGE") : "/home/hyyuan/pyjm12_demo/ddr_image.u32.bin";
    char h2c_path[128];
    char c2h_path[128];
    char password[PASSWORD_FIELD_BYTES];
    uint8_t *raw_output = NULL;
    int h2c_fd = -1;
    int c2h_fd = -1;
    int ret = 1;

    if (parse_options(argc, argv, &opt) != 0) {
        usage(argv[0]);
        return 2;
    }

    raw_output = (uint8_t *)malloc(opt.raw_output_bytes);
    if (!raw_output) {
        fprintf(stderr, "malloc raw_output %zu failed\n", opt.raw_output_bytes);
        return 1;
    }

    snprintf(h2c_path, sizeof(h2c_path), "/dev/xdma%s_h2c_0", xdma_id);
    snprintf(c2h_path, sizeof(c2h_path), "/dev/xdma%s_c2h_0", xdma_id);
    h2c_fd = open(h2c_path, O_RDWR | O_SYNC);
    c2h_fd = open(c2h_path, O_RDWR | O_SYNC);
    if (h2c_fd < 0 || c2h_fd < 0) {
        fprintf(stderr, "open %s/%s failed: %s\n", h2c_path, c2h_path, strerror(errno));
        goto out;
    }

    printf("pyjm_fpga_demo xdma_id=%s h2c=%s c2h=%s\n", xdma_id, h2c_path, c2h_path);
    printf("pattern=%s password_base=0x%llx raw_output_addr=0x%llx raw_output_bytes=%zu\n",
           opt.pattern, (unsigned long long)opt.password_base,
           (unsigned long long)ACC_OUTPUT_ABS, opt.raw_output_bytes);
    printf("password_nonce=%u\n", opt.nonce);

    if (opt.check_magic && check_debug_magic(c2h_fd) != 0)
        goto out;

    if (opt.write_input_mode != 0) {
        int image_fd = open(ddr_image, O_RDONLY);
        uint64_t bytes = opt.write_input_mode == 1 ? INPUT_SIZE_BYTES : DDR_IMAGE_SIZE_BYTES;
        uint64_t t0 = now_ns();
        if (image_fd < 0) {
            fprintf(stderr, "open DDR_IMAGE %s failed: %s\n", ddr_image, strerror(errno));
            goto out;
        }
        if (load_file_region(image_fd, h2c_fd, DDR_BASE, bytes) != 0) {
            close(image_fd);
            goto out;
        }
        close(image_fd);
        printf("input_write_mode=%d bytes=%llu host_input_write_ns=%llu\n",
               opt.write_input_mode, (unsigned long long)bytes,
               (unsigned long long)(now_ns() - t0));
    }

    printf("run,host_start_to_result_ns,poll_reads,status_raw,input_status,result_status,hw_latency_cycles_reg31,output_hash32\n");
    for (int run = 1; run <= opt.runs; ++run) {
        int rc = run_accelerator_once(h2c_fd, c2h_fd, opt.poll_timeout_ms,
                                      raw_output, opt.raw_output_bytes, &rr);
        printf("%d,%llu,%d,0x%08x,%u,%u,0x%08x,0x%08x%s\n",
               run,
               (unsigned long long)rr.host_latency_ns,
               rr.poll_reads,
               rr.status,
               rr.status & 0x7u,
               (rr.status >> 3) & 0x7u,
               rr.hw_cycles,
               rr.output_hash,
               rc == 0 ? "" : ",TIMEOUT");
        fflush(stdout);
        if (rc != 0)
            goto out;
    }

    if (generate_password_from_pattern(opt.pattern, opt.password_len, raw_output,
                                       opt.raw_output_bytes, rr.output_hash, opt.nonce,
                                       password, sizeof(password)) < 0) {
        fprintf(stderr, "failed to generate demo password from raw output\n");
        goto out;
    }

    printf("password_pattern=%s\n", opt.pattern);
    printf("password_value=%s\n", password);

    if (opt.write_password_record) {
        if (write_password_record(h2c_fd, c2h_fd, opt.password_base,
                                  opt.pattern, password, &rr) != 0)
            goto out;
        printf("password_record_addr=0x%llx\n", (unsigned long long)opt.password_base);
        printf("password_record_bytes=%u\n", PASSWORD_RECORD_BYTES);
        printf("password_record_magic=PYJM\n");
    }

    ret = 0;

out:
    if (h2c_fd >= 0)
        close(h2c_fd);
    if (c2h_fd >= 0)
        close(c2h_fd);
    free(raw_output);
    return ret;
}
