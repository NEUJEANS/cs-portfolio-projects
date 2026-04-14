import argparse
import heapq
import json
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


def serialize_archive(data: bytes) -> bytes:
    result = encode_bytes(data)
    header = {
        "bit_length": result.bit_length,
        "frequencies": {str(symbol): count for symbol, count in result.frequencies.items()},
        "original_size": len(data),
    }
    return MAGIC + json.dumps(header, sort_keys=True).encode("utf-8") + HEADER_DELIMITER + result.encoded


def deserialize_archive(payload: bytes) -> tuple[dict[int, int], int, int, bytes]:
    if not payload.startswith(MAGIC):
        raise ValueError("Invalid archive format")

    body = payload[len(MAGIC) :]
    try:
        header_blob, encoded = body.split(HEADER_DELIMITER, 1)
    except ValueError as exc:
        raise ValueError("Archive header is incomplete") from exc

    header = json.loads(header_blob.decode("utf-8"))
    frequencies = {int(symbol): count for symbol, count in header["frequencies"].items()}
    return frequencies, header["bit_length"], header["original_size"], encoded


def compress_file(source: str, output: Optional[str] = None) -> Path:
    source_path = Path(source)
    data = source_path.read_bytes()
    if not data:
        raise ValueError("Cannot compress an empty file")

    destination = Path(output) if output else source_path.with_suffix(source_path.suffix + ".huf")
    destination.write_bytes(serialize_archive(data))
    return destination


def decompress_file(source: str, output: Optional[str] = None) -> Path:
    source_path = Path(source)
    frequencies, bit_length, original_size, encoded = deserialize_archive(source_path.read_bytes())
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
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compress and decompress files with Huffman coding")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compress_parser = subparsers.add_parser("compress", help="Compress a file into a .huf archive")
    compress_parser.add_argument("source")
    compress_parser.add_argument("-o", "--output")

    decompress_parser = subparsers.add_parser("decompress", help="Restore a file from a .huf archive")
    decompress_parser.add_argument("source")
    decompress_parser.add_argument("-o", "--output")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compress":
        destination = compress_file(args.source, args.output)
        print(f"Compressed to {destination}")
    elif args.command == "decompress":
        destination = decompress_file(args.source, args.output)
        print(f"Decompressed to {destination}")


if __name__ == "__main__":
    main()
