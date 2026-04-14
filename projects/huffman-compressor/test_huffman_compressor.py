import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from huffman_compressor import (
    MAGIC,
    build_tree,
    calculate_entropy,
    compress_file,
    decode_bytes,
    decompress_file,
    deserialize_archive,
    encode_bytes,
    format_stats_lines,
    generate_codes,
    inspect_archive,
    main,
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

            archive, compress_stats = compress_file(str(source))
            restored, decompress_stats = decompress_file(str(archive), str(tmp_path / "restored.txt"))

            self.assertTrue(archive.exists())
            self.assertEqual(restored.read_bytes(), source.read_bytes())
            self.assertEqual(compress_stats.original_size, len(source.read_bytes()))
            self.assertEqual(decompress_stats.decoded_size, len(source.read_bytes()))

    def test_archive_contains_metadata_and_magic_header(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source = tmp_path / "input.bin"
            source.write_bytes(bytes(range(32)))

            archive, _ = compress_file(str(source))
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

    def test_decompress_rejects_invalid_header_json(self):
        with TemporaryDirectory() as tmpdir:
            archive = Path(tmpdir) / "broken.huf"
            archive.write_bytes(MAGIC + b"not-json\n\nabc")

            with self.assertRaisesRegex(ValueError, "Archive header is invalid"):
                decompress_file(str(archive))

    def test_decompress_rejects_truncated_payload(self):
        with TemporaryDirectory() as tmpdir:
            archive = Path(tmpdir) / "broken.huf"
            archive.write_bytes(
                MAGIC
                + b'{"bit_length": 16, "frequencies": {"97": 2}, "original_size": 2}'
                + b"\n\n"
                + b"\x00"
            )

            with self.assertRaisesRegex(ValueError, "Archive payload is truncated"):
                decompress_file(str(archive))

    def test_entropy_matches_uniform_two_symbol_distribution(self):
        entropy = calculate_entropy({ord("a"): 5, ord("b"): 5})
        self.assertAlmostEqual(entropy, 1.0, places=5)

    def test_inspect_archive_reports_metadata_without_decompressing(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source = tmp_path / "input.txt"
            source.write_bytes(b"aaaaabbbbcccdde")
            archive, compress_stats = compress_file(str(source))

            stats = inspect_archive(str(archive))

            self.assertEqual(stats.archive_size, archive.stat().st_size)
            self.assertEqual(stats.decoded_size, len(source.read_bytes()))
            self.assertEqual(stats.encoded_size, compress_stats.encoded_size)
            self.assertEqual(stats.unique_symbols, 5)

    def test_format_stats_lines_includes_ratio_and_entropy_for_compression(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source = tmp_path / "sample.txt"
            source.write_bytes(b"abracadabra abracadabra")
            _, stats = compress_file(str(source))

            lines = format_stats_lines(stats, "compress")

            self.assertTrue(any(line.startswith("Compression ratio:") for line in lines))
            self.assertTrue(any(line.startswith("Entropy estimate:") for line in lines))
            self.assertTrue(any(line.startswith("Space savings:") for line in lines))

    def test_cli_compress_with_stats_prints_statistics_block(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source = tmp_path / "sample.txt"
            source.write_bytes(b"mississippi river" * 4)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                main(["compress", str(source), "--stats"])

            output = buffer.getvalue()
            self.assertIn("Compressed to", output)
            self.assertIn("Statistics:", output)
            self.assertIn("Compression ratio:", output)

    def test_cli_inspect_prints_archive_summary(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source = tmp_path / "sample.txt"
            source.write_bytes(b"datastructuresandalgorithms")
            archive, _ = compress_file(str(source))

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                main(["inspect", str(archive)])

            output = buffer.getvalue()
            self.assertIn("Archive:", output)
            self.assertIn("Decoded size:", output)
            self.assertIn("Entropy estimate:", output)


if __name__ == "__main__":
    unittest.main()
