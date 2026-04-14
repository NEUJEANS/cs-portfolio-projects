import argparse, re
from collections import Counter

STATUS_RE = re.compile(r'"\s(\d{3})\s')
IP_RE = re.compile(r'^(\S+)')


def analyze_lines(lines):
    status_counts = Counter()
    ip_counts = Counter()
    for line in lines:
        status = STATUS_RE.search(line)
        ip = IP_RE.search(line)
        if status:
            status_counts[status.group(1)] += 1
        if ip:
            ip_counts[ip.group(1)] += 1
    return {
        'status_counts': dict(status_counts),
        'top_ips': ip_counts.most_common(3),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description='Log analyzer')
    p.add_argument('logfile')
    args = p.parse_args(argv)
    with open(args.logfile, encoding='utf-8') as f:
        result = analyze_lines(f)
    print(result)

if __name__ == '__main__':
    main()
