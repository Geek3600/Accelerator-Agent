import json
import urllib.error
import urllib.request
import unittest
from unittest.mock import patch

from accagent.framework.llm_io import (
    ResponseDecodeError,
    build_prompt,
    chat_completion_payload,
    parse_json_object,
    read_response_text,
    response_text,
    response_stream_text,
    structured_output_payload,
    validate_schema,
)


def sse(*events: dict) -> list[bytes]:
    return [f"data: {json.dumps(event)}\n".encode("utf-8") for event in events]


class BuildPromptTests(unittest.TestCase):
    def test_selected_large_json_block_is_compact_and_lossless(self) -> None:
        evidence = {"cells": [{"id": index, "pins": ["a", "b"]} for index in range(1000)]}
        schema = {"type": "object"}
        prompt = build_prompt(
            "selector",
            "review evidence",
            {"chunk": evidence},
            schema,
            compact_json_blocks=("chunk",),
        )
        encoded = prompt.split("<chunk>\n", 1)[1].split("\n</chunk>", 1)[0]

        self.assertEqual(json.loads(encoded), evidence)
        self.assertNotIn("\n  ", encoded)
        self.assertLess(len(encoded), len(json.dumps(evidence, indent=2, sort_keys=True)))


class ResponseStreamTextTests(unittest.TestCase):
    def test_blank_completed_text_is_not_a_successful_response(self) -> None:
        for text in ("", " \n\t"):
            for body in (
                {"output_text": text},
                {"output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]},
                {"choices": [{"message": {"content": text}}]},
            ):
                with self.subTest(body=body):
                    with self.assertRaisesRegex(ValueError, "no output text"):
                        response_text(body)

    def test_blank_stream_text_is_not_a_successful_response(self) -> None:
        for events in (
            [{"type": "response.output_text.delta", "delta": " \n"}],
            [{"type": "response.output_text.done", "text": "\t"}],
            [{"type": "response.completed", "response": {"output_text": ""}}],
            [{"choices": [{"delta": {"content": " \n"}}]}],
        ):
            with self.subTest(events=events):
                with self.assertRaisesRegex(ValueError, "no output text"):
                    response_stream_text(sse(*events))

    def test_nonblank_response_keeps_its_original_whitespace(self) -> None:
        text = ' \n{"ok":true}\n '
        self.assertEqual(response_text({"output_text": text}), text)
        self.assertEqual(
            response_stream_text(sse({"type": "response.output_text.delta", "delta": text})),
            text,
        )

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

    def test_anthropic_message_stream_returns_text_deltas(self) -> None:
        stream = sse(
            {"type": "message_start", "message": {"type": "message"}},
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": '{"ok":'},
            },
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "true}"},
            },
            {"type": "message_stop"},
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


class ParseJsonObjectTests(unittest.TestCase):
    def test_keeps_complete_root_object_before_trailing_model_text(self) -> None:
        parsed = parse_json_object(
            '{"status":"blocked","file_edits":[]} trailing model commentary'
        )

        self.assertEqual(parsed, {"status": "blocked", "file_edits": []})

    def test_still_rejects_truncated_root_object(self) -> None:
        with self.assertRaises(json.JSONDecodeError):
            parse_json_object('{"status":"blocked","file_edits":[')


class ChatCompletionPayloadTests(unittest.TestCase):
    def test_chat_completion_uses_structured_json_schema(self) -> None:
        schema = {
            "type": "object",
            "properties": {"ready": {"type": "boolean"}},
            "required": ["ready"],
            "additionalProperties": False,
        }

        payload = chat_completion_payload(
            "claude-opus-5",
            "system prompt",
            "user prompt",
            "test schema",
            schema,
            max_output_tokens=128,
            stream=True,
        )

        self.assertEqual(payload["model"], "claude-opus-5")
        self.assertEqual(
            payload["messages"],
            [
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "user prompt"},
            ],
        )
        self.assertEqual(
            payload["response_format"]["json_schema"]["schema"], schema
        )
        self.assertEqual(payload["max_tokens"], 128)
        self.assertTrue(payload["stream"])

    def test_structured_payload_uses_configured_chat_wire_api(self) -> None:
        payload = structured_output_payload(
            "chat/completions",
            "claude-opus-5",
            "system",
            "prompt",
            "probe",
            {"type": "object"},
        )

        self.assertIn("messages", payload)
        self.assertNotIn("input", payload)

    def test_structured_payload_keeps_responses_as_default(self) -> None:
        payload = structured_output_payload(
            "responses",
            "gpt-6.1-sol",
            "system",
            "prompt",
            "probe",
            {"type": "object"},
        )

        self.assertIn("input", payload)
        self.assertNotIn("messages", payload)

    def test_anthropic_messages_payload_uses_prompt_schema_and_required_budget(self) -> None:
        payload = structured_output_payload(
            "anthropic/messages",
            "claude-opus-5",
            "system prompt",
            "user prompt including output schema",
            "probe",
            {"type": "object"},
            stream=True,
        )

        self.assertEqual(payload["model"], "claude-opus-5")
        self.assertEqual(payload["system"], "system prompt")
        self.assertEqual(payload["messages"], [{"role": "user", "content": "user prompt including output schema"}])
        self.assertEqual(payload["max_tokens"], 8192)
        self.assertTrue(payload["stream"])
        self.assertNotIn("response_format", payload)

    def test_anthropic_output_budget_uses_configured_limit(self) -> None:
        payload = structured_output_payload(
            "anthropic/messages",
            "claude-opus-5",
            "system",
            "prompt",
            "probe",
            {"type": "object"},
            max_output_tokens=2048,
        )
        self.assertEqual(payload["max_tokens"], 2048)

    def test_unsupported_temperature_retries_once_without_parameter(self) -> None:
        payload = chat_completion_payload(
            "claude-opus-5", "system", "prompt", "probe", {"type": "object"}
        )
        req = urllib.request.Request(
            "https://example.invalid/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": "Bearer test"},
            method="POST",
        )
        rejected = urllib.error.HTTPError(
            req.full_url,
            400,
            "Bad Request; response_body={\"message\":\"model does not support non-default temperature\"}",
            {},
            None,
        )

        with patch(
            "accagent.framework.llm_io._read_response_text_once",
            side_effect=[rejected, "{\"ok\":true}"],
        ) as send:
            result = read_response_text(req, timeout_sec=10, stream=False)

        self.assertEqual(result, "{\"ok\":true}")
        self.assertEqual(send.call_count, 2)
        retry_req = send.call_args_list[1].args[0]
        self.assertEqual(retry_req.full_url, req.full_url)
        self.assertEqual(retry_req.get_method(), "POST")
        self.assertEqual(retry_req.get_header("Authorization"), "Bearer test")
        self.assertNotIn("temperature", json.loads(retry_req.data))

    def test_unavailable_json_schema_retries_chat_request_in_json_object_mode(self) -> None:
        payload = chat_completion_payload(
            "deepseek-v4-pro", "system", "prompt", "probe", {"type": "object"}
        )
        req = urllib.request.Request(
            "https://example.invalid/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": "Bearer test"},
            method="POST",
        )
        rejected = urllib.error.HTTPError(
            req.full_url,
            400,
            "Bad Request; response_body={\"error\":{\"message\":\"This response_format type is unavailable now\"}}",
            {},
            None,
        )

        with patch(
            "accagent.framework.llm_io._read_response_text_once",
            side_effect=[rejected, "{\"ready\":true}"],
        ) as send:
            result = read_response_text(req, timeout_sec=10, stream=False)

        self.assertEqual(result, "{\"ready\":true}")
        self.assertEqual(send.call_count, 2)
        retry_req = send.call_args_list[1].args[0]
        retry_payload = json.loads(retry_req.data)
        self.assertEqual(retry_payload["response_format"], {"type": "json_object"})
        self.assertEqual(retry_payload["model"], "deepseek-v4-pro")
        self.assertEqual(retry_req.get_header("Authorization"), "Bearer test")

    def test_unrelated_http_error_is_not_retried(self) -> None:
        req = urllib.request.Request(
            "https://example.invalid/v1/chat/completions",
            data=b'{"temperature":0}',
            method="POST",
        )
        rejected = urllib.error.HTTPError(req.full_url, 400, "bad request", {}, None)

        with patch(
            "accagent.framework.llm_io._read_response_text_once",
            side_effect=rejected,
        ) as send:
            with self.assertRaises(urllib.error.HTTPError):
                read_response_text(req, timeout_sec=10, stream=False)

        send.assert_called_once_with(req, 10, False)


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
