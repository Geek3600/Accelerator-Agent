from __future__ import annotations

import unittest

from accagent.framework.stage_input import redact_sensitive_text, sanitize_llm_payload


class StageInputSanitizationTest(unittest.TestCase):
    def test_sensitive_material_lines_are_removed_from_stage0_prompts(self) -> None:
        secret = "example-secret-value"
        text = f"remote host: build@example.org\npassword is {secret}\npasswordless login: true\n"

        redacted = redact_sensitive_text(text)

        self.assertNotIn(secret, redacted)
        self.assertIn("remote host: build@example.org", redacted)
        self.assertIn("passwordless login: true", redacted)

    def test_credential_field_evidence_is_not_persisted(self) -> None:
        payload = {
            "evidence": [
                {"field": "tool.remote.host", "value": "build@example.org"},
                {"field": "tool.remote.ssh_password", "value": "example-secret-value"},
            ],
            "tool_api_key": "another-secret",
        }

        sanitized = sanitize_llm_payload(payload)

        self.assertEqual(sanitized["evidence"], [{"field": "tool.remote.host", "value": "build@example.org"}])
        self.assertNotIn("tool_api_key", sanitized)


if __name__ == "__main__":
    unittest.main()
