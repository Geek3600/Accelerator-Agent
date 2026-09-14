import json
from types import SimpleNamespace
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from accagent.framework import llm_io
from accagent.framework.llm_config import LlmCfg


class CurlDirectHttpTransportTests(unittest.TestCase):
    def _request(self) -> urllib.request.Request:
        return urllib.request.Request(
            "https://example.invalid/v1/responses",
            data=b'{"model":"test"}',
            headers={
                "Authorization": "Bearer secret-for-test",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

    @staticmethod
    def _runner(status: int, body: bytes, returncode: int = 0):
        def run(command, **kwargs):
            write_out = command[command.index("--write-out") + 1]
            suffix = write_out.replace("%{http_code}", str(status)).encode("utf-8")
            return SimpleNamespace(
                returncode=returncode,
                stdout=body + suffix,
                stderr=b"",
            )

        return run

    def test_curl_direct_http1_parses_structured_response_without_secret_argv(self) -> None:
        response = {
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": '{"ok":true}'}],
                }
            ]
        }
        captured: dict[str, object] = {}

        def run(command, **kwargs):
            captured["command"] = command
            captured["input"] = kwargs["input"]
            return self._runner(200, json.dumps(response).encode("utf-8"))(
                command, **kwargs
            )

        with (
            patch.object(
                llm_io,
                "resolved_llm_cfg",
                return_value=LlmCfg(http_transport="curl_direct_http1"),
            ),
            patch.object(llm_io.subprocess, "run", side_effect=run),
        ):
            text = llm_io.read_response_text(self._request(), 10, stream=False)

        self.assertEqual(text, '{"ok":true}')
        self.assertEqual(captured["input"], b'{"model":"test"}')
        self.assertNotIn(
            "secret-for-test", " ".join(str(item) for item in captured["command"])
        )
        self.assertIn("--noproxy", captured["command"])
        self.assertIn("@-", captured["command"])

    def test_curl_direct_http1_parses_sse_response(self) -> None:
        stream = (
            b'data: {"type":"response.output_text.delta","delta":"hello"}\n'
            b"\n"
            b"data: [DONE]\n"
        )
        with (
            patch.object(
                llm_io,
                "resolved_llm_cfg",
                return_value=LlmCfg(http_transport="curl_direct_http1"),
            ),
            patch.object(
                llm_io.subprocess,
                "run",
                side_effect=self._runner(200, stream),
            ),
        ):
            text = llm_io.read_response_text(self._request(), 10, stream=True)

        self.assertEqual(text, "hello")

    def test_stream_incomplete_exposes_output_budget_reason(self) -> None:
        stream = (
            b'data: {"type":"response.incomplete","response":{"id":"resp-test",'
            b'"incomplete_details":{"reason":"max_output_tokens"}}}\n'
        )

        with self.assertRaises(llm_io.ResponseIncompleteError) as raised:
            llm_io.response_stream_text(stream.splitlines(keepends=True))

        self.assertEqual(raised.exception.reason, "max_output_tokens")
        self.assertEqual(raised.exception.response_id, "resp-test")

    def test_response_payload_accepts_optional_output_budget(self) -> None:
        payload = llm_io.response_payload(
            "test-model",
            "system",
            "prompt",
            "schema",
            {"type": "object"},
            max_output_tokens=32768,
        )

        self.assertEqual(payload["max_output_tokens"], 32768)

    def test_curl_direct_http1_preserves_http_error_semantics(self) -> None:
        with (
            patch.object(
                llm_io,
                "resolved_llm_cfg",
                return_value=LlmCfg(http_transport="curl_direct_http1"),
            ),
            patch.object(
                llm_io.subprocess,
                "run",
                side_effect=self._runner(502, b'{"error":"upstream"}'),
            ),
            self.assertRaises(urllib.error.HTTPError) as raised,
        ):
            llm_io.read_response_text(self._request(), 10, stream=False)

        self.assertEqual(raised.exception.code, 502)
        self.assertIn("response_body", str(raised.exception.reason))


if __name__ == "__main__":
    unittest.main()
