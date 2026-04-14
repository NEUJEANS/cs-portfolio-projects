import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from huffman_compressor import (
    MAGIC,
    build_tree,
    compress_file,
    decode_bytes,
    decompress_file,
    deserialize_archive,
    encode_bytes,
    generate_codes,
)


class HuffmanCompressorTests(unittest.TestCase):
    def test_encode_decode_round_trip_for_text(self):
        data = b"banana bandana"
        result = encode_bytes(data)
        decoded = decode_bytes(result.frequencies, result.encoded, result.bit_length)
        self.assertEqual(decoded, data)

    def test_generate_codes_for_single_symbol_uses_zero_bit(self):
        tree = build_tree(b"aaaa")
        codes = generate_codes(tree)
        self.assertEqual(codes, {97: "0"})

    def test_compress_and_decompress_file_round_trip(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source = tmp_path / "sample.txt"
            source.write_bytes(b"the quick brown fox jumps over the lazy dog" * 5)

            archive = compress_file(str(source))
            restored = decompress_file(str(archive), str(tmp_path / "restored.txt"))

            self.assertTrue(archive.exists())
            self.assertEqual(restored.read_bytes(), source.read_bytes())

    def test_archive_contains_metadata_and_magic_header(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source = tmp_path / "input.bin"
            source.write_bytes(bytes(range(32)))

            archive = compress_file(str(source))
            payload = archive.read_bytes()
            frequencies, bit_length, original_size, encoded = deserialize_archive(payload)

            self.assertTrue(payload.startswith(MAGIC))
            self.assertEqual(original_size, 32)
            self.assertGreater(bit_length, 0)
            self.assertGreater(len(encoded), 0)
            self.assertEqual(frequencies[0], 1)
            self.assertEqual(frequencies[31], 1)

    def test_decompress_rejects_invalid_magic(self):
        with TemporaryDirectory() as tmpdir:
            archive = Path(tmpdir) / "broken.huf"
            archive.write_bytes(b"not-a-valid-archive")

            with self.assertRaisesRegex(ValueError, "Invalid archive format"):
                decompress_file(str(archive))

    def test_compress_rejects_empty_files(self):
        with TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "empty.txt"
            source.write_text("")

            with self.assertRaisesRegex(ValueError, "empty file"):
                compress_file(str(source))


if __name__ == "__main__":
    unittest.main()
