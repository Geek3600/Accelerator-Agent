#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "vcs_vpi_user.h"

#define SPATIALACC_STATE_MAGIC "SPACST1"
#define SPATIALACC_STATE_VERSION 1U
#define SPATIALACC_FNV_OFFSET UINT64_C(1469598103934665603)
#define SPATIALACC_FNV_PRIME UINT64_C(1099511628211)

typedef struct {
    char *name;
    PLI_INT32 type;
    PLI_INT32 size;
} spatialacc_state_desc;

typedef struct {
    spatialacc_state_desc *rows;
    size_t count;
    size_t capacity;
} spatialacc_state_table;

typedef struct {
    char magic[8];
    uint32_t version;
    uint32_t state_count;
    uint64_t schema_hash;
} spatialacc_state_header;

typedef struct {
    uint32_t name_bytes;
    uint32_t type;
    uint32_t size_bits;
    uint32_t vector_words;
} spatialacc_state_entry;

static uint64_t spatialacc_hash_bytes(uint64_t hash, const void *data, size_t size) {
    const unsigned char *bytes = (const unsigned char *)data;
    size_t index;
    for (index = 0; index < size; ++index) {
        hash ^= (uint64_t)bytes[index];
        hash *= SPATIALACC_FNV_PRIME;
    }
    return hash;
}

static int spatialacc_supported_type(PLI_INT32 type) {
    return type == vpiReg || type == vpiMemoryWord ||
           type == vpiIntegerVar || type == vpiTimeVar ||
           type == vpiBitVar || type == vpiLongIntVar ||
           type == vpiShortIntVar || type == vpiIntVar ||
           type == vpiByteVar || type == vpiEnumVar ||
           type == vpiStructVar || type == vpiUnionVar;
}

static int spatialacc_container_type(PLI_INT32 type) {
    return type == vpiMemory || type == vpiRegArray;
}

static void spatialacc_table_free(spatialacc_state_table *table) {
    size_t index;
    for (index = 0; index < table->count; ++index) {
        free(table->rows[index].name);
    }
    free(table->rows);
    memset(table, 0, sizeof(*table));
}

static int spatialacc_table_add(
    spatialacc_state_table *table,
    vpiHandle handle
) {
    const char *name = vpi_get_str(vpiFullName, handle);
    spatialacc_state_desc *row;
    PLI_INT32 size;
    if (name == NULL || name[0] == '\0') {
        return 0;
    }
    size = vpi_get(vpiSize, handle);
    if (size <= 0) {
        return 0;
    }
    if (table->count == table->capacity) {
        size_t capacity = table->capacity == 0 ? 256 : table->capacity * 2;
        void *updated = realloc(table->rows, capacity * sizeof(*table->rows));
        if (updated == NULL) {
            return -1;
        }
        table->rows = (spatialacc_state_desc *)updated;
        table->capacity = capacity;
    }
    row = &table->rows[table->count++];
    row->name = strdup(name);
    if (row->name == NULL) {
        return -1;
    }
    row->type = vpi_get(vpiType, handle);
    row->size = size;
    return 0;
}

static int spatialacc_scan_variable(
    vpiHandle handle,
    spatialacc_state_table *table
) {
    PLI_INT32 type = vpi_get(vpiType, handle);
    vpiHandle iterator;
    vpiHandle item;
    if (spatialacc_supported_type(type)) {
        return spatialacc_table_add(table, handle);
    }
    if (!spatialacc_container_type(type)) {
        return 0;
    }
    iterator = vpi_iterate(
        type == vpiMemory ? vpiMemoryWord : vpiReg,
        handle
    );
    if (iterator == NULL) {
        iterator = vpi_iterate(vpiVariables, handle);
    }
    while (iterator != NULL && (item = vpi_scan(iterator)) != NULL) {
        if (spatialacc_scan_variable(item, table) != 0) {
            return -1;
        }
    }
    return 0;
}

static int spatialacc_scan_scope(
    vpiHandle scope,
    spatialacc_state_table *table
) {
    vpiHandle iterator;
    vpiHandle item;
    iterator = vpi_iterate(vpiVariables, scope);
    while (iterator != NULL && (item = vpi_scan(iterator)) != NULL) {
        if (spatialacc_scan_variable(item, table) != 0) {
            return -1;
        }
    }
    iterator = vpi_iterate(vpiModule, scope);
    while (iterator != NULL && (item = vpi_scan(iterator)) != NULL) {
        if (spatialacc_scan_scope(item, table) != 0) {
            return -1;
        }
    }
    iterator = vpi_iterate(vpiGenScope, scope);
    while (iterator != NULL && (item = vpi_scan(iterator)) != NULL) {
        if (spatialacc_scan_scope(item, table) != 0) {
            return -1;
        }
    }
    return 0;
}

static int spatialacc_compare_rows(const void *left_value, const void *right_value) {
    const spatialacc_state_desc *left =
        (const spatialacc_state_desc *)left_value;
    const spatialacc_state_desc *right =
        (const spatialacc_state_desc *)right_value;
    return strcmp(left->name, right->name);
}

static int spatialacc_collect_state(
    const char *root_name,
    spatialacc_state_table *table
) {
    vpiHandle root = vpi_handle_by_name((PLI_BYTE8 *)root_name, NULL);
    size_t read_index;
    size_t write_index;
    if (root == NULL) {
        vpi_printf(
            "SPATIALACC_CHECKPOINT_ERROR root_not_found=%s\n",
            root_name
        );
        return -1;
    }
    if (spatialacc_scan_scope(root, table) != 0) {
        return -1;
    }
    qsort(
        table->rows,
        table->count,
        sizeof(*table->rows),
        spatialacc_compare_rows
    );
    write_index = 0;
    for (read_index = 0; read_index < table->count; ++read_index) {
        if (
            write_index > 0 &&
            strcmp(
                table->rows[read_index].name,
                table->rows[write_index - 1].name
            ) == 0
        ) {
            free(table->rows[read_index].name);
            continue;
        }
        if (write_index != read_index) {
            table->rows[write_index] = table->rows[read_index];
        }
        ++write_index;
    }
    table->count = write_index;
    return table->count == 0 ? -1 : 0;
}

static uint64_t spatialacc_schema_hash(const spatialacc_state_table *table) {
    uint64_t hash = SPATIALACC_FNV_OFFSET;
    size_t index;
    for (index = 0; index < table->count; ++index) {
        const spatialacc_state_desc *row = &table->rows[index];
        uint32_t name_bytes = (uint32_t)strlen(row->name);
        uint32_t type = (uint32_t)row->type;
        uint32_t size = (uint32_t)row->size;
        hash = spatialacc_hash_bytes(hash, &name_bytes, sizeof(name_bytes));
        hash = spatialacc_hash_bytes(hash, row->name, name_bytes);
        hash = spatialacc_hash_bytes(hash, &type, sizeof(type));
        hash = spatialacc_hash_bytes(hash, &size, sizeof(size));
    }
    return hash;
}

static int spatialacc_write_schema(
    const char *path,
    const spatialacc_state_table *table,
    uint64_t schema_hash
) {
    FILE *stream = fopen(path, "w");
    size_t index;
    if (stream == NULL) {
        return -1;
    }
    fprintf(
        stream,
        "schema_version=spatialaccagent.vcs_vpi_state_schema.v1\n"
        "state_count=%lu\n"
        "fnv1a64=%016llx\n",
        (unsigned long)table->count,
        (unsigned long long)schema_hash
    );
    for (index = 0; index < table->count; ++index) {
        fprintf(
            stream,
            "%s\t%d\t%d\n",
            table->rows[index].name,
            (int)table->rows[index].type,
            (int)table->rows[index].size
        );
    }
    if (fflush(stream) != 0 || fclose(stream) != 0) {
        return -1;
    }
    return 0;
}

static int spatialacc_read_string_args(
    char **state_path,
    char **root_name,
    char **schema_path
) {
    vpiHandle call = vpi_handle(vpiSysTfCall, NULL);
    vpiHandle iterator = vpi_iterate(vpiArgument, call);
    vpiHandle argument;
    char **outputs[3] = {state_path, root_name, schema_path};
    int index = 0;
    while (
        iterator != NULL &&
        index < 3 &&
        (argument = vpi_scan(iterator)) != NULL
    ) {
        s_vpi_value value;
        value.format = vpiStringVal;
        vpi_get_value(argument, &value);
        if (value.value.str == NULL) {
            return -1;
        }
        *outputs[index] = strdup(value.value.str);
        if (*outputs[index] == NULL) {
            return -1;
        }
        ++index;
    }
    return index == 3 ? 0 : -1;
}

static void spatialacc_set_result(int result) {
    vpiHandle call = vpi_handle(vpiSysTfCall, NULL);
    s_vpi_value value;
    value.format = vpiIntVal;
    value.value.integer = result;
    vpi_put_value(call, &value, NULL, vpiNoDelay);
}

static int spatialacc_capture_impl(
    const char *state_path,
    const char *root_name,
    const char *schema_path
) {
    spatialacc_state_table table = {0};
    spatialacc_state_header header;
    FILE *stream = NULL;
    size_t index;
    int result = -1;
    if (spatialacc_collect_state(root_name, &table) != 0) {
        goto done;
    }
    memset(&header, 0, sizeof(header));
    memcpy(header.magic, SPATIALACC_STATE_MAGIC, 7);
    header.version = SPATIALACC_STATE_VERSION;
    header.state_count = (uint32_t)table.count;
    header.schema_hash = spatialacc_schema_hash(&table);
    if (spatialacc_write_schema(schema_path, &table, header.schema_hash) != 0) {
        goto done;
    }
    stream = fopen(state_path, "wb");
    if (stream == NULL || fwrite(&header, sizeof(header), 1, stream) != 1) {
        goto done;
    }
    for (index = 0; index < table.count; ++index) {
        spatialacc_state_desc *row = &table.rows[index];
        vpiHandle handle = vpi_handle_by_name((PLI_BYTE8 *)row->name, NULL);
        spatialacc_state_entry entry;
        s_vpi_value value;
        if (handle == NULL) {
            goto done;
        }
        memset(&entry, 0, sizeof(entry));
        entry.name_bytes = (uint32_t)strlen(row->name);
        entry.type = (uint32_t)row->type;
        entry.size_bits = (uint32_t)row->size;
        entry.vector_words = (entry.size_bits + 31U) / 32U;
        value.format = vpiVectorVal;
        value.value.vector = NULL;
        vpi_get_value(handle, &value);
        if (
            value.value.vector == NULL ||
            fwrite(&entry, sizeof(entry), 1, stream) != 1 ||
            fwrite(row->name, entry.name_bytes, 1, stream) != 1 ||
            fwrite(
                value.value.vector,
                sizeof(s_vpi_vecval),
                entry.vector_words,
                stream
            ) != entry.vector_words
        ) {
            goto done;
        }
    }
    if (fflush(stream) != 0) {
        goto done;
    }
    result = 0;
done:
    if (stream != NULL && fclose(stream) != 0) {
        result = -1;
    }
    if (result == 0) {
        vpi_printf(
            "SPATIALACC_CHECKPOINT_CAPTURE_PASS root=%s states=%lu schema=%016llx\n",
            root_name,
            (unsigned long)table.count,
            (unsigned long long)header.schema_hash
        );
    } else {
        vpi_printf("SPATIALACC_CHECKPOINT_CAPTURE_FAIL root=%s\n", root_name);
    }
    spatialacc_table_free(&table);
    return result;
}

static int spatialacc_restore_impl(
    const char *state_path,
    const char *root_name,
    const char *schema_path
) {
    spatialacc_state_table table = {0};
    spatialacc_state_header header;
    FILE *stream = NULL;
    uint32_t index;
    int result = -1;
    (void)schema_path;
    if (spatialacc_collect_state(root_name, &table) != 0) {
        goto done;
    }
    stream = fopen(state_path, "rb");
    if (stream == NULL || fread(&header, sizeof(header), 1, stream) != 1) {
        goto done;
    }
    if (
        memcmp(header.magic, SPATIALACC_STATE_MAGIC, 7) != 0 ||
        header.version != SPATIALACC_STATE_VERSION ||
        header.state_count != table.count ||
        header.schema_hash != spatialacc_schema_hash(&table)
    ) {
        vpi_printf("SPATIALACC_CHECKPOINT_SCHEMA_MISMATCH root=%s\n", root_name);
        goto done;
    }
    for (index = 0; index < header.state_count; ++index) {
        spatialacc_state_entry entry;
        char *name = NULL;
        s_vpi_vecval *vector = NULL;
        vpiHandle handle;
        s_vpi_value value;
        if (fread(&entry, sizeof(entry), 1, stream) != 1) {
            goto entry_done;
        }
        name = (char *)malloc((size_t)entry.name_bytes + 1U);
        vector = (s_vpi_vecval *)calloc(
            entry.vector_words,
            sizeof(*vector)
        );
        if (
            name == NULL || vector == NULL ||
            fread(name, entry.name_bytes, 1, stream) != 1 ||
            fread(
                vector,
                sizeof(*vector),
                entry.vector_words,
                stream
            ) != entry.vector_words
        ) {
            goto entry_done;
        }
        name[entry.name_bytes] = '\0';
        handle = vpi_handle_by_name((PLI_BYTE8 *)name, NULL);
        if (
            handle == NULL ||
            (uint32_t)vpi_get(vpiType, handle) != entry.type ||
            (uint32_t)vpi_get(vpiSize, handle) != entry.size_bits
        ) {
            goto entry_done;
        }
        value.format = vpiVectorVal;
        value.value.vector = vector;
        vpi_put_value(handle, &value, NULL, vpiNoDelay);
        free(name);
        free(vector);
        continue;
entry_done:
        free(name);
        free(vector);
        goto done;
    }
    result = 0;
done:
    if (stream != NULL && fclose(stream) != 0) {
        result = -1;
    }
    if (result == 0) {
        vpi_printf(
            "SPATIALACC_CHECKPOINT_RESTORE_PASS root=%s states=%lu schema=%016llx\n",
            root_name,
            (unsigned long)table.count,
            (unsigned long long)header.schema_hash
        );
    } else {
        vpi_printf("SPATIALACC_CHECKPOINT_RESTORE_FAIL root=%s\n", root_name);
    }
    spatialacc_table_free(&table);
    return result;
}

void spatialacc_state_capture(void) {
    char *state_path = NULL;
    char *root_name = NULL;
    char *schema_path = NULL;
    int result = -1;
    if (
        spatialacc_read_string_args(
            &state_path,
            &root_name,
            &schema_path
        ) == 0
    ) {
        result = spatialacc_capture_impl(state_path, root_name, schema_path);
    }
    spatialacc_set_result(result);
    free(state_path);
    free(root_name);
    free(schema_path);
}

void spatialacc_state_restore(void) {
    char *state_path = NULL;
    char *root_name = NULL;
    char *schema_path = NULL;
    int result = -1;
    if (
        spatialacc_read_string_args(
            &state_path,
            &root_name,
            &schema_path
        ) == 0
    ) {
        result = spatialacc_restore_impl(state_path, root_name, schema_path);
    }
    spatialacc_set_result(result);
    free(state_path);
    free(root_name);
    free(schema_path);
}
