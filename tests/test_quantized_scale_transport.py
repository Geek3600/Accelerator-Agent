"""Unit coverage for generated quantization wiring, not board execution evidence."""
import unittest

from accagent.framework.stage_artifacts import generated_scale_interface
from scripts.synthesis.compute_slot_adapter_generator import (
    _generated_scale_port_bindings,
    _scale_transport_wires,
)


class QuantizedScaleTransportTests(unittest.TestCase):
    def test_declared_unsigned_q31_identity_is_representable(self):
        rtl = _scale_transport_wires([{
            'generated_port': 'io_qkvScale_activationScale',
            'internal_wire': 'unit_scale', 'width': 32, 'value': 1 << 31,
        }])
        self.assertIn("32'h80000000", rtl)
        for value in (0, (1 << 31) + 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _scale_transport_wires([{
                    'generated_port': 'io_qkvScale_activationScale',
                    'internal_wire': 'unit_scale', 'width': 32, 'value': value,
                }])

    def test_checkpoint_channel_values_drive_internal_wires(self):
        widths = {
            'io_qkvScale_channelScale_0': 32,
            'io_qkvScale_channelScale_1': 32,
            'io_qkvScale_channelShift_0': 8,
            'io_qkvScale_channelShift_1': 8,
        }
        route = {
            'target_kind': 'linear_weight_matrix',
            'target_id': 'attention.qkv.weight',
            'logical_shape': [2, 4],
            'start': 0,
            'scale_payload': {'channels': [
                {'multiplier_unsigned_q31': 1073741824, 'binary_shift': -4},
                {'multiplier_unsigned_q31': 1610612736, 'binary_shift': 2},
            ]},
        }
        bindings = _generated_scale_port_bindings(set(widths), widths, [route])
        by_port = {row['generated_port']: row for row in bindings}
        self.assertEqual(by_port['io_qkvScale_channelScale_1']['value'], 1610612736)
        self.assertEqual(by_port['io_qkvScale_channelShift_0']['value'], -4)
        rtl = _scale_transport_wires(bindings)
        self.assertRegex(rtl, r"gen_scale_qkvScale_channelShift_0(?:_bank[01]_q)?\s*(?:<=|=)\s*8'hfc;")
        self.assertRegex(rtl, r"gen_scale_qkvScale_channelScale_1(?:_bank[01]_q)?\s*(?:<=|=)\s*32'h60000000;")
        self.assertNotIn('input ', rtl)
        self.assertTrue(all('external_port' not in row for row in bindings))

    def test_missing_checkpoint_payload_is_rejected(self):
        port = 'io_qkvScale_channelScale_0'
        with self.assertRaises(ValueError):
            _generated_scale_port_bindings({port}, {port: 32}, [{
                'target_kind': 'linear_weight_matrix',
                'target_id': 'attention.qkv.weight',
                'logical_shape': [1, 4], 'start': 0,
            }])

    def test_both_norm_families_connect_each_scale_bundle(self):
        for family, role in [('GPT2PreLNBlock', 'ffnUpScale'), ('Qwen2Block', 'mlpGateScale')]:
            declarations, connections = generated_scale_interface(family)
            self.assertIn(f'val {role} = Input(chiselTypeOf(core.io.{role}))', declarations)
            self.assertIn(f'core.io.{role} := io.{role}', connections)
            self.assertIn('core.io.attentionOutScale := io.attentionOutScale', connections)


if __name__ == '__main__':
    unittest.main()
