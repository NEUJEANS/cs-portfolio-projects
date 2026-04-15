import argparse
import json
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PRIME = 257


@dataclass(frozen=True)
class Share:
    x: int
    values: list[int]

    def to_dict(self) -> dict:
        return {"x": self.x, "values": self.values}

    @classmethod
    def from_dict(cls, data: dict) -> "Share":
        x = data.get("x")
        values = data.get("values")
        if not isinstance(x, int) or not 1 <= x < PRIME:
            raise ValueError("share x must be an integer between 1 and 256")
        if not isinstance(values, list) or not values:
            raise ValueError("share values must be a non-empty list")
        if any(type(value) is not int or not 0 <= value < PRIME for value in values):
            raise ValueError("share values must be integers between 0 and 256")
        return cls(x=x, values=list(values))


def evaluate_polynomial(coefficients: list[int], x: int, prime: int = PRIME) -> int:
    result = 0
    for coefficient in reversed(coefficients):
        result = (result * x + coefficient) % prime
    return result


def modular_inverse(value: int, prime: int = PRIME) -> int:
    if value % prime == 0:
        raise ZeroDivisionError("cannot invert zero in a finite field")
    return pow(value, -1, prime)


def lagrange_interpolate_at_zero(points: Iterable[tuple[int, int]], prime: int = PRIME) -> int:
    points = list(points)
    if not points:
        raise ValueError("at least one point is required")
    xs = [x for x, _ in points]
    if len(xs) != len(set(xs)):
        raise ValueError("shares must use distinct x coordinates")

    total = 0
    for i, (x_i, y_i) in enumerate(points):
        numerator = 1
        denominator = 1
        for j, (x_j, _) in enumerate(points):
            if i == j:
                continue
            numerator = (numerator * (-x_j % prime)) % prime
            denominator = (denominator * (x_i - x_j)) % prime
        total = (total + y_i * numerator * modular_inverse(denominator, prime)) % prime
    return total


def split_secret(secret_bytes: bytes, threshold: int, total_shares: int, prime: int = PRIME) -> list[Share]:
    if not secret_bytes:
        raise ValueError("secret must not be empty")
    if not 2 <= threshold <= total_shares:
        raise ValueError("threshold must satisfy 2 <= threshold <= total_shares")
    if total_shares >= prime:
        raise ValueError("total_shares must be smaller than the finite field size")

    shares = [Share(x=index, values=[]) for index in range(1, total_shares + 1)]
    mutable_values = {share.x: [] for share in shares}

    for byte in secret_bytes:
        coefficients = [byte] + [secrets.randbelow(prime) for _ in range(threshold - 1)]
        for share in shares:
            mutable_values[share.x].append(evaluate_polynomial(coefficients, share.x, prime))

    return [Share(x=share.x, values=mutable_values[share.x]) for share in shares]


def recover_secret(shares: list[Share], threshold: int, prime: int = PRIME) -> bytes:
    if len(shares) < threshold:
        raise ValueError("not enough shares to satisfy the threshold")
    selected = shares[:threshold]
    lengths = {len(share.values) for share in selected}
    if len(lengths) != 1:
        raise ValueError("all shares must have the same payload length")

    recovered = bytearray()
    for byte_index in range(len(selected[0].values)):
        points = [(share.x, share.values[byte_index]) for share in selected]
        secret_value = lagrange_interpolate_at_zero(points, prime)
        if not 0 <= secret_value <= 255:
            raise ValueError("recovered byte fell outside byte range; shares may be corrupted")
        recovered.append(secret_value)
    return bytes(recovered)


def encode_secret(text: str) -> bytes:
    if not text:
        raise ValueError("secret text must not be empty")
    return text.encode("utf-8")


def decode_secret(secret_bytes: bytes) -> str:
    return secret_bytes.decode("utf-8")


def save_shares(path: Path, threshold: int, shares: list[Share], encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scheme": "shamir-secret-sharing",
        "prime": PRIME,
        "threshold": threshold,
        "share_count": len(shares),
        "encoding": encoding,
        "shares": [share.to_dict() for share in shares],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_shares(path: Path) -> tuple[int, str, list[Share]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("scheme") != "shamir-secret-sharing":
        raise ValueError("unsupported share file format")
    threshold = payload.get("threshold")
    encoding = payload.get("encoding", "utf-8")
    if not isinstance(threshold, int) or threshold < 2:
        raise ValueError("share file threshold must be an integer >= 2")
    shares_data = payload.get("shares")
    if not isinstance(shares_data, list) or not shares_data:
        raise ValueError("share file must contain at least one share")
    shares = [Share.from_dict(item) for item in shares_data]
    if len({share.x for share in shares}) != len(shares):
        raise ValueError("share bundle contains duplicate share ids")
    lengths = {len(share.values) for share in shares}
    if len(lengths) != 1:
        raise ValueError("share bundle contains inconsistent payload lengths")
    return threshold, encoding, shares


def split_command(args: argparse.Namespace) -> int:
    shares = split_secret(encode_secret(args.secret), threshold=args.threshold, total_shares=args.shares)
    save_shares(Path(args.output), threshold=args.threshold, shares=shares)
    print(json.dumps({"output": args.output, "threshold": args.threshold, "share_count": len(shares)}, indent=2))
    return 0


def recover_command(args: argparse.Namespace) -> int:
    threshold, encoding, shares = load_shares(Path(args.input))
    if len(set(args.use)) != len(args.use):
        raise ValueError("requested share ids must be distinct")
    selected = [share for share in shares if share.x in args.use]
    if len(selected) != len(args.use):
        raise ValueError("requested share ids were not all present in the input file")
    secret = recover_secret(selected, threshold=threshold)
    print(json.dumps({"threshold": threshold, "selected_share_ids": args.use, "encoding": encoding, "secret": decode_secret(secret)}, indent=2))
    return 0


def inspect_command(args: argparse.Namespace) -> int:
    threshold, encoding, shares = load_shares(Path(args.input))
    print(json.dumps({
        "threshold": threshold,
        "share_count": len(shares),
        "encoding": encoding,
        "share_ids": [share.x for share in shares],
        "secret_length_bytes": len(shares[0].values),
    }, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shamir secret sharing lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    split_parser = subparsers.add_parser("split", help="split a UTF-8 secret into threshold shares")
    split_parser.add_argument("--secret", required=True)
    split_parser.add_argument("--threshold", type=int, required=True)
    split_parser.add_argument("--shares", type=int, required=True)
    split_parser.add_argument("--output", required=True)
    split_parser.set_defaults(func=split_command)

    recover_parser = subparsers.add_parser("recover", help="recover a secret from enough shares")
    recover_parser.add_argument("--input", required=True)
    recover_parser.add_argument("--use", nargs="+", type=int, required=True)
    recover_parser.set_defaults(func=recover_command)

    inspect_parser = subparsers.add_parser("inspect", help="inspect a share bundle")
    inspect_parser.add_argument("--input", required=True)
    inspect_parser.set_defaults(func=inspect_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
