import json
import unittest

from accagent.framework.llm_io import (
    ResponseDecodeError,
    response_stream_text,
    validate_schema,
)


def sse(*events: dict) -> list[bytes]:
    return [f"data: {json.dumps(event)}\n".encode("utf-8") for event in events]


class ResponseStreamTextTests(unittest.TestCase):
    def test_response_deltas_are_not_duplicated_by_done_events(self) -> None:
        output = {"ok": True}
        text = json.dumps(output, separators=(",", ":"))
        response = {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": text}],
                }
            ]
        }
        stream = sse(
            {"type": "response.created", "response": {"status": "in_progress"}},
            {"type": "response.output_text.delta", "delta": '{"ok":'},
            {"type": "response.output_text.delta", "delta": "true}"},
            {"type": "response.output_text.done", "text": text},
            {
                "type": "response.content_part.done",
                "part": {"type": "output_text", "text": text},
            },
            {
                "type": "response.output_item.done",
                "item": {
                    "type": "message",
                    "content": [{"type": "output_text", "text": text}],
                },
            },
            {"type": "response.completed", "response": response},
        )

        self.assertEqual(response_stream_text(stream), text)

    def test_output_text_done_is_used_when_no_deltas_exist(self) -> None:
        stream = sse({"type": "response.output_text.done", "text": '{"ok":true}'})
        self.assertEqual(response_stream_text(stream), '{"ok":true}')

    def test_completed_response_is_the_final_fallback(self) -> None:
        stream = sse(
            {
                "type": "response.completed",
                "response": {
                    "output": [
                        {
                            "type": "message",
                            "content": [{"type": "output_text", "text": '{"ok":true}'}],
                        }
                    ]
                },
            }
        )
        self.assertEqual(response_stream_text(stream), '{"ok":true}')

    def test_chat_style_stream_remains_supported(self) -> None:
        stream = sse(
            {"choices": [{"delta": {"content": '{"ok":'}}]},
            {"choices": [{"delta": {"content": "true}"}}]},
        )
        self.assertEqual(response_stream_text(stream), '{"ok":true}')

    def test_truncated_sse_event_is_reported_as_provider_decode_failure(self) -> None:
        stream = [
            b'data: {"type":"response.output_text.delta","delta":"unterminated}\n'
        ]

        with self.assertRaises(ResponseDecodeError) as raised:
            response_stream_text(stream)

        self.assertEqual(raised.exception.transport, "SSE event")
        self.assertIn("malformed or truncated JSON", str(raised.exception))


class SchemaValidationTests(unittest.TestCase):
    def test_nested_array_items_must_match_object_schema(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "file_edits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "operation": {
                                "type": "string",
                                "enum": ["replace"],
                            },
                        },
                        "required": ["path", "operation"],
                    },
                }
            },
            "required": ["file_edits"],
        }

        with self.assertRaisesRegex(
            ValueError,
            r"file_edits\[0\]\.operation is required.*file_edits\[1\] expected object",
        ):
            validate_schema(
                {"file_edits": [{"path": "a"}, "operation", "replace"]},
                schema,
                "agent",
            )

    def test_nested_types_enum_and_additional_properties_are_checked(self) -> None:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "status": {"type": "string", "enum": ["ready"]},
                "count": {"type": "integer", "minimum": 1},
            },
            "required": ["status", "count"],
        }

        with self.assertRaisesRegex(ValueError, "not an allowed field"):
            validate_schema(
                {"status": "wrong", "count": 0, "extra": True},
                schema,
                "agent",
            )


if __name__ == "__main__":
    unittest.main()
