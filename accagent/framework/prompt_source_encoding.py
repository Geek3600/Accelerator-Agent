"""Lossless prompt encoding of mechanically numbered source declarations."""

import hashlib
import re


def decode_numbered_source(value):
    chunks = []
    for segment in value["segments"]:
        if isinstance(segment, str):
            chunks.append(segment)
            continue
        for index in range(segment["count"]):
            fields = segment["line_parts"].copy()
            for column, (start, step) in enumerate(segment["numeric_columns"]):
                fields[2 * column + 1] = str(start + index * step)
            chunks.append("".join(fields))
    return "".join(chunks)


def encode_numbered_source(source):
    if len(source) < 32000:
        return source
    lines = source.splitlines(keepends=True)
    parts = [re.split(r"(\d+)", line) for line in lines]
    segments = []
    literal = []
    index = 0
    while index < len(parts):
        first = parts[index]
        count = 1
        columns = []
        if len(first) > 1 and index + 1 < len(parts):
            second = parts[index + 1]
            if (first[::2] == second[::2]
                    and all(str(int(token)) == token for token in first[1::2] + second[1::2])):
                columns = [(int(a), int(b) - int(a)) for a, b in zip(first[1::2], second[1::2])]
                count = 2
                while index + count < len(parts):
                    row = parts[index + count]
                    if row[::2] != first[::2] or row[1::2] != [str(a + count * b) for a, b in columns]:
                        break
                    count += 1
        if count >= 4:
            if literal:
                segments.append("".join(literal))
                literal = []
            segments.append({"line_parts": first, "numeric_columns": columns, "count": count})
            index += count
        else:
            literal.append(lines[index])
            index += 1
    if literal:
        segments.append("".join(literal))
    value = {"encoding": "lossless_numbered_source_lines_v1", "segments": segments,
             "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
             "decoding": "Concatenate segments in order. A string is literal. For each numbered segment, "
                         "iterate i=0..count-1, replace line_parts[2*c+1] with decimal "
                         "numeric_columns[c][0]+i*numeric_columns[c][1], then concatenate all line_parts. "
                         "Reconstruct exact original text before deriving replace_text anchors."}
    if decode_numbered_source(value) != source:
        raise ValueError("numbered-source encoding did not preserve exact original text")
    import json
    return value if len(json.dumps(value)) < len(source) // 2 else source


def encode_prompt_source_documents(value):
    if isinstance(value, list):
        return [encode_prompt_source_documents(row) for row in value]
    if not isinstance(value, dict):
        return value
    return {key: (encode_numbered_source(child)
                  if key in {"content", "module_header"} and isinstance(child, str)
                  and str(value.get("path", "")).split("#")[0].endswith((".sv", ".v", ".scala"))
                  else encode_prompt_source_documents(child))
            for key, child in value.items()}
