import json
import urllib.error
import urllib.request
from contextlib import nullcontext
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from accagent.framework import stage_team


class DecomposerTransportRetryTests(TestCase):
    def test_upgrade_response_switches_transport_without_changing_route(self):
        request = urllib.request.Request(
            "https://example.invalid/v1/responses",
            data=json.dumps({"model": "test", "input": "unchanged", "stream": True}).encode(),
            headers={"Authorization": "Bearer test", "Accept": "text/event-stream"},
            method="POST",
        )
        seen = []

        def respond(req, timeout, stream):
            seen.append((req.full_url, json.loads(req.data), stream, req.get_header("Authorization")))
            if len(seen) == 1:
                raise urllib.error.HTTPError(req.full_url, 426, "Upgrade Required", {}, None)
            return "{}"

        with patch.object(stage_team, "read_response_text", side_effect=respond), \
             patch.object(stage_team, "llm_inflight_slot", return_value=nullcontext()), \
             patch.object(stage_team, "llm_transient_retry_unbounded", return_value=False), \
             patch.object(stage_team, "llm_transient_attempts", return_value=2), \
             patch.object(stage_team, "resolved_llm_cfg", return_value=SimpleNamespace(fallback_endpoint="", fallback_api_key="")), \
             patch.object(stage_team, "stream_transport_fallback_error", return_value=True), \
             patch.object(stage_team.time, "sleep"):
            result, errors = stage_team.post_decomposer_json(request, 10, "test", True)
        self.assertEqual(result, "{}")
        self.assertEqual(len(errors), 1)
        self.assertEqual(seen[0][0], seen[1][0])
        self.assertEqual(seen[0][3], seen[1][3])
        self.assertEqual(seen[1][1]["input"], "unchanged")
        self.assertFalse(seen[1][1]["stream"])
        self.assertFalse(seen[1][2])
