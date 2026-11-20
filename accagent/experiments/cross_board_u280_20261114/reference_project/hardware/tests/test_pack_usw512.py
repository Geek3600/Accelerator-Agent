import unittest

import numpy as np

from hardware.pack_usw512 import (
    pack_matrix_to_usw512,
    unpack_matrix_from_usw512,
)


class PackUsw512Tests(unittest.TestCase):
    def test_fixed_record_layout_roundtrip_and_gamma_order(self):
        ternary = np.zeros((1, 256), dtype=np.int8)
        ternary[0, :10] = [-1, 0, 1, -1, 0, -1, 0, 1, -1, 0]
        sparse = np.zeros_like(ternary, dtype=np.float64)
        sparse[0, 10] = 3.0
        sparse[0, 255] = -4.0

        packed, gamma, effective_ternary, sparse_q4_12 = pack_matrix_to_usw512(
            ternary, sparse, np.array([2.0]), np.array([[1.0], [2.0]])
        )

        self.assertEqual(len(packed), 64)
        self.assertEqual(packed[:12], bytes.fromhex("00 e0 ff 00 18 0a 00 00 00 00 00 00"))
        self.assertEqual(packed[12], 102)
        self.assertEqual(packed[13], 102)
        self.assertEqual(packed[14], 121)
        self.assertEqual(packed[15:63], bytes([121]) * 48)
        self.assertEqual(packed[63], 1)
        self.assertEqual(gamma.shape, (2, 1))
        self.assertEqual(gamma.tobytes(), bytes.fromhex("00 40 00 44"))

        decoded_ternary, decoded_sparse = unpack_matrix_from_usw512(packed, 1, 256)
        np.testing.assert_array_equal(decoded_ternary, effective_ternary)
        np.testing.assert_array_equal(decoded_ternary, ternary)
        expected_sparse = np.zeros((1, 256), dtype=np.int16)
        expected_sparse[0, 10] = 6144
        expected_sparse[0, 255] = -8192
        np.testing.assert_array_equal(sparse_q4_12, expected_sparse)
        np.testing.assert_array_equal(decoded_sparse, expected_sparse)

    def test_partial_window_padding_is_zero_and_decodes(self):
        ternary = np.zeros((1, 257), dtype=np.int8)
        ternary[0, 256] = 1
        sparse = np.zeros_like(ternary, dtype=np.float32)

        packed, _, effective_ternary, sparse_q4_12 = pack_matrix_to_usw512(
            ternary, sparse, [1.0], [[1.0]]
        )

        self.assertEqual(len(packed), 2 * 64)
        last_record = packed[64:]
        self.assertEqual(last_record[:12], bytes(12))
        self.assertEqual(last_record[12], 122)
        self.assertEqual(last_record[13:63], bytes([121]) * 50)
        self.assertEqual(last_record[63], 1)
        decoded_ternary, decoded_sparse = unpack_matrix_from_usw512(packed, 1, 257)
        np.testing.assert_array_equal(decoded_ternary, effective_ternary)
        np.testing.assert_array_equal(decoded_ternary, ternary)
        np.testing.assert_array_equal(decoded_sparse, sparse_q4_12)
        self.assertFalse(decoded_sparse.any())

    def test_folds_window_overflow_and_keeps_largest_magnitudes_sparse(self):
        ternary = np.zeros((1, 256), dtype=np.int8)
        sparse = np.zeros((1, 256), dtype=np.float64)
        sparse[0, :5] = [0.4, 7.0, 6.0, 5.0, 4.0]

        packed, _, effective_ternary, sparse_q4_12 = pack_matrix_to_usw512(
            ternary, sparse, [1.0], [[1.0]]
        )

        self.assertEqual(effective_ternary[0, 0], 0)
        expected_sparse = np.zeros((1, 256), dtype=np.int16)
        expected_sparse[0, 1:5] = [28672, 24576, 20480, 16384]
        np.testing.assert_array_equal(sparse_q4_12, expected_sparse)
        decoded_ternary, decoded_sparse = unpack_matrix_from_usw512(packed, 1, 256)
        np.testing.assert_array_equal(decoded_ternary, effective_ternary)
        np.testing.assert_array_equal(decoded_sparse, expected_sparse)

    def test_rejects_sparse_overlap_and_saturates_q4_12(self):
        ternary = np.zeros((1, 256), dtype=np.int8)
        sparse = np.zeros((1, 256), dtype=np.float64)
        sparse[0, :5] = [1, 2, 3, 4, 5]

        ternary[0, 3] = 1
        with self.assertRaisesRegex(ValueError, "W_tern must be zero"):
            pack_matrix_to_usw512(ternary, sparse, [1.0], [[1.0]])

        ternary[0, 3] = 0
        sparse.fill(0)
        sparse[0, 0] = 8.0
        packed, _, _, sparse_q4_12 = pack_matrix_to_usw512(ternary, sparse, [1.0], [[1.0]])
        self.assertEqual(sparse_q4_12[0, 0], 32767)
        _, decoded_sparse = unpack_matrix_from_usw512(packed, 1, 256)
        self.assertEqual(decoded_sparse[0, 0], 32767)

    def test_rejects_invalid_quantization_inputs(self):
        ternary = np.zeros((1, 256), dtype=np.int8)
        sparse = np.zeros((1, 256), dtype=np.float64)
        sparse[0, 0] = 1e-6
        packed, _, _, sparse_q4_12 = pack_matrix_to_usw512(ternary, sparse, [1.0], [[1.0]])
        self.assertEqual(sparse_q4_12[0, 0], 0)
        _, decoded_sparse = unpack_matrix_from_usw512(packed, 1, 256)
        self.assertFalse(decoded_sparse.any())

        sparse.fill(0)
        sparse[0, 0] = 1.0
        with self.assertRaisesRegex(ValueError, "positive alpha"):
            pack_matrix_to_usw512(ternary, sparse, [0.0], [[1.0]])

        with self.assertRaisesRegex(ValueError, "exactly -1, 0, or \+1"):
            pack_matrix_to_usw512(np.full((1, 256), 2), np.zeros((1, 256)), [1.0], [[1.0]])
        with self.assertRaisesRegex(ValueError, "beta_steps values"):
            pack_matrix_to_usw512(ternary, np.zeros((1, 256)), [1.0], [[0.5]])

        sparse.fill(0)
        sparse[0, 0] = 1.0
        _, _, _, sparse_q4_12 = pack_matrix_to_usw512(ternary, sparse, [3.0], [[1.0]])
        self.assertEqual(sparse_q4_12[0, 0], 1365)

    def test_unpack_rejects_invalid_radix_and_sparse_coordinates(self):
        invalid_radix = bytearray(64)
        invalid_radix[12] = 243
        with self.assertRaisesRegex(ValueError, "radix-3 byte"):
            unpack_matrix_from_usw512(invalid_radix, 1, 256)

        invalid_sparse = bytearray(64)
        invalid_sparse[:3] = bytes.fromhex("00 10 00")
        with self.assertRaisesRegex(ValueError, "must be zero"):
            unpack_matrix_from_usw512(invalid_sparse, 1, 256)

        with self.assertRaisesRegex(ValueError, "exactly 64 bytes"):
            unpack_matrix_from_usw512(bytes(63), 1, 256)


if __name__ == "__main__":
    unittest.main()
