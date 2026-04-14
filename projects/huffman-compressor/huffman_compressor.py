import argparse
import heapq
import json
import math
from collections import Counter
from dataclasses import dataclass, field
from itertools import count
from pathlib import Path
from typing import Optional


MAGIC = b"HUF1"
HEADER_DELIMITER = b"\n\n"
NODE_COUNTER = count()


@dataclass(order=True)
class Node:
    frequency: int
    order: int = field(default_factory=lambda: next(NODE_COUNTER))
    symbol: Optional[int] = field(default=None, compare=False)
    left: Optional["Node"] = field(default=None, compare=False)
    right: Optional["Node"] = field(default=None, compare=False)


@dataclass
class HuffmanResult:
    frequencies: dict[int, int]
    encoded: bytes
    bit_length: int


@dataclass
class CompressionStats:
    original_size: int
    encoded_size: int
    archive_size: int
    bit_length: int
    symbol_count: int
    unique_symbols: int
    average_bits_per_symbol: float
    entropy_estimate: float
    compression_ratio: float
    space_saving_ratio: float
    header_size: int


@dataclass
class DecompressionStats:
    archive_size: int
    encoded_size: int
    decoded_size: int
    bit_length: int
    unique_symbols: int
    average_bits_per_symbol: float
    entropy_estimate: float
    header_size: int


def build_tree_from_frequencies(frequencies: dict[int, int]) -> Node:
    if not frequencies:
        raise ValueError("Cannot build a Huffman tree from empty data")

    heap = [
        Node(frequency=count, symbol=symbol)
        for symbol, count in sorted(frequencies.items(), key=lambda item: (item[1], item[0]))
    ]
    heapq.heapify(heap)

    if len(heap) == 1:
        only = heap[0]
        return Node(frequency=only.frequency, left=only)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        heapq.heappush(heap, Node(frequency=left.frequency + right.frequency, left=left, right=right))

    return heap[0]


def build_tree(data: bytes) -> Node:
    return build_tree_from_frequencies(dict(Counter(data)))


def generate_codes(node: Node, prefix: str = "", codes: Optional[dict[int, str]] = None) -> dict[int, str]:
    if codes is None:
        codes = {}

    if node.symbol is not None:
        codes[node.symbol] = prefix or "0"
        return codes

    if node.left is not None:
        generate_codes(node.left, prefix + "0", codes)
    if node.right is not None:
        generate_codes(node.right, prefix + "1", codes)
    return codes


def calculate_entropy(frequencies: dict[int, int]) -> float:
    total = sum(frequencies.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in frequencies.values():
        probability = count / total
        entropy -= probability * math.log2(probability)
    return entropy


def calculate_average_bits_per_symbol(bit_length: int, symbol_count: int) -> float:
    if symbol_count == 0:
        return 0.0
    return bit_length / symbol_count


def build_compression_stats(frequencies: dict[int, int], bit_length: int, encoded_size: int, archive_size: int) -> CompressionStats:
    original_size = sum(frequencies.values())
    symbol_count = original_size
    entropy_estimate = calculate_entropy(frequencies)
    average_bits = calculate_average_bits_per_symbol(bit_length, symbol_count)
    header_size = archive_size - encoded_size
    compression_ratio = archive_size / original_size if original_size else 0.0
    space_saving_ratio = 1 - compression_ratio if original_size else 0.0
    return CompressionStats(
        original_size=original_size,
        encoded_size=encoded_size,
        archive_size=archive_size,
        bit_length=bit_length,
        symbol_count=symbol_count,
        unique_symbols=len(frequencies),
        average_bits_per_symbol=average_bits,
        entropy_estimate=entropy_estimate,
        compression_ratio=compression_ratio,
        space_saving_ratio=space_saving_ratio,
        header_size=header_size,
    )


def build_decompression_stats(frequencies: dict[int, int], bit_length: int, encoded_size: int, archive_size: int) -> DecompressionStats:
    decoded_size = sum(frequencies.values())
    return DecompressionStats(
        archive_size=archive_size,
        encoded_size=encoded_size,
        decoded_size=decoded_size,
        bit_length=bit_length,
        unique_symbols=len(frequencies),
        average_bits_per_symbol=calculate_average_bits_per_symbol(bit_length, decoded_size),
        entropy_estimate=calculate_entropy(frequencies),
        header_size=archive_size - encoded_size,
    )


def format_percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def format_stats_lines(stats: CompressionStats | DecompressionStats, mode: str) -> list[str]:
    if mode == "compress":
        assert isinstance(stats, CompressionStats)
        return [
            f"Original size: {stats.original_size} bytes",
            f"Archive size: {stats.archive_size} bytes",
            f"Header size: {stats.header_size} bytes",
            f"Encoded payload size: {stats.encoded_size} bytes",
            f"Unique symbols: {stats.unique_symbols}",
            f"Bit length: {stats.bit_length}",
            f"Average bits/symbol: {stats.average_bits_per_symbol:.3f}",
            f"Entropy estimate: {stats.entropy_estimate:.3f} bits/symbol",
            f"Compression ratio: {stats.compression_ratio:.3f} ({format_percentage(stats.compression_ratio)})",
            f"Space savings: {stats.space_saving_ratio:.3f} ({format_percentage(stats.space_saving_ratio)})",
        ]

    assert isinstance(stats, DecompressionStats)
    return [
        f"Archive size: {stats.archive_size} bytes",
        f"Header size: {stats.header_size} bytes",
        f"Encoded payload size: {stats.encoded_size} bytes",
        f"Decoded size: {stats.decoded_size} bytes",
        f"Unique symbols: {stats.unique_symbols}",
        f"Bit length: {stats.bit_length}",
        f"Average bits/symbol: {stats.average_bits_per_symbol:.3f}",
        f"Entropy estimate: {stats.entropy_estimate:.3f} bits/symbol",
    ]


def print_stats(stats: CompressionStats | DecompressionStats, mode: str) -> None:
    print("Statistics:")
    for line in format_stats_lines(stats, mode):
        print(f"  {line}")


def encode_bytes(data: bytes) -> HuffmanResult:
    tree = build_tree(data)
    frequencies = dict(Counter(data))
    codes = generate_codes(tree)
    bit_string = "".join(codes[byte] for byte in data)
    padding = (8 - len(bit_string) % 8) % 8
    padded = bit_string + ("0" * padding)
    encoded = bytes(int(padded[i : i + 8], 2) for i in range(0, len(padded), 8))
    return HuffmanResult(frequencies=frequencies, encoded=encoded, bit_length=len(bit_string))


def decode_bytes(frequencies: dict[int, int], encoded: bytes, bit_length: int) -> bytes:
    if not frequencies:
        return b""

    tree = build_tree_from_frequencies(frequencies)
    if tree.left and tree.left.symbol is not None and tree.right is None:
        return bytes([tree.left.symbol] * bit_length)

    bit_string = "".join(f"{byte:08b}" for byte in encoded)[:bit_length]
    output = bytearray()
    node = tree
    for bit in bit_string:
        node = node.left if bit == "0" else node.right
        if node is None:
            raise ValueError("Encoded stream is invalid for the provided Huffman tree")
        if node.symbol is not None:
            output.append(node.symbol)
            node = tree
    return bytes(output)


def serialize_result(result: HuffmanResult, original_size: int) -> bytes:
    header = {
        "bit_length": result.bit_length,
        "frequencies": {str(symbol): count for symbol, count in result.frequencies.items()},
        "original_size": original_size,
    }
    return MAGIC + json.dumps(header, sort_keys=True).encode("utf-8") + HEADER_DELIMITER + result.encoded


def serialize_archive(data: bytes) -> bytes:
    result = encode_bytes(data)
    return serialize_result(result, len(data))


def deserialize_archive(payload: bytes) -> tuple[dict[int, int], int, int, bytes]:
    if not payload.startswith(MAGIC):
        raise ValueError("Invalid archive format")

    body = payload[len(MAGIC) :]
    try:
        header_blob, encoded = body.split(HEADER_DELIMITER, 1)
    except ValueError as exc:
        raise ValueError("Archive header is incomplete") from exc

    try:
        header = json.loads(header_blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Archive header is invalid") from exc

    try:
        bit_length = int(header["bit_length"])
        original_size = int(header["original_size"])
        frequencies = {int(symbol): int(count) for symbol, count in header["frequencies"].items()}
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ValueError("Archive metadata is invalid") from exc

    if bit_length < 0 or original_size < 0:
        raise ValueError("Archive metadata contains negative sizes")
    if any(count <= 0 for count in frequencies.values()):
        raise ValueError("Archive metadata contains non-positive frequencies")

    required_bytes = (bit_length + 7) // 8
    if len(encoded) < required_bytes:
        raise ValueError("Archive payload is truncated")

    return frequencies, bit_length, original_size, encoded


def inspect_archive(source: str) -> DecompressionStats:
    source_path = Path(source)
    payload = source_path.read_bytes()
    frequencies, bit_length, original_size, encoded = deserialize_archive(payload)
    if sum(frequencies.values()) != original_size:
        raise ValueError("Archive metadata is inconsistent with symbol frequencies")
    return build_decompression_stats(
        frequencies=frequencies,
        bit_length=bit_length,
        encoded_size=len(encoded),
        archive_size=len(payload),
    )


def compress_file(source: str, output: Optional[str] = None) -> tuple[Path, CompressionStats]:
    source_path = Path(source)
    data = source_path.read_bytes()
    if not data:
        raise ValueError("Cannot compress an empty file")

    destination = Path(output) if output else source_path.with_suffix(source_path.suffix + ".huf")
    result = encode_bytes(data)
    archive = serialize_result(result, len(data))
    destination.write_bytes(archive)
    stats = build_compression_stats(
        result.frequencies,
        bit_length=result.bit_length,
        encoded_size=len(result.encoded),
        archive_size=len(archive),
    )
    return destination, stats


def decompress_file(source: str, output: Optional[str] = None) -> tuple[Path, DecompressionStats]:
    source_path = Path(source)
    payload = source_path.read_bytes()
    frequencies, bit_length, original_size, encoded = deserialize_archive(payload)
    decoded = decode_bytes(frequencies, encoded, bit_length)
    if len(decoded) != original_size:
        raise ValueError("Decoded data size does not match archive metadata")

    if output:
        destination = Path(output)
    elif source_path.suffix == ".huf":
        destination = source_path.with_suffix("")
    else:
        destination = source_path.with_name(source_path.name + ".decoded")

    destination.write_bytes(decoded)
    stats = build_decompression_stats(
        frequencies=frequencies,
        bit_length=bit_length,
        encoded_size=len(encoded),
        archive_size=len(payload),
    )
    return destination, stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compress and decompress files with Huffman coding")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compress_parser = subparsers.add_parser("compress", help="Compress a file into a .huf archive")
    compress_parser.add_argument("source")
    compress_parser.add_argument("-o", "--output")
    compress_parser.add_argument("--stats", action="store_true", help="Print compression statistics")

    decompress_parser = subparsers.add_parser("decompress", help="Restore a file from a .huf archive")
    decompress_parser.add_argument("source")
    decompress_parser.add_argument("-o", "--output")
    decompress_parser.add_argument("--stats", action="store_true", help="Print archive statistics after decompression")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect archive metadata without decompressing")
    inspect_parser.add_argument("source")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compress":
        destination, stats = compress_file(args.source, args.output)
        print(f"Compressed to {destination}")
        if args.stats:
            print_stats(stats, "compress")
    elif args.command == "decompress":
        destination, stats = decompress_file(args.source, args.output)
        print(f"Decompressed to {destination}")
        if args.stats:
            print_stats(stats, "decompress")
    elif args.command == "inspect":
        stats = inspect_archive(args.source)
        print(f"Archive: {args.source}")
        print_stats(stats, "decompress")


if __name__ == "__main__":
    main()
