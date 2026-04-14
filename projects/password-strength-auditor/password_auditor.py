import argparse, math, string

COMMON = {'password', '123456', 'qwerty', 'letmein', 'admin'}

def evaluate(password):
    reasons = []
    pool = 0
    if len(password) < 10:
        reasons.append('too short')
    lowers = any(c.islower() for c in password)
    uppers = any(c.isupper() for c in password)
    digits = any(c.isdigit() for c in password)
    punct = any(c in string.punctuation for c in password)
    for ok, size, name in [(lowers,26,'lowercase'),(uppers,26,'uppercase'),(digits,10,'digits'),(punct,len(string.punctuation),'symbols')]:
        if ok: pool += size
        else: reasons.append(f'missing {name}')
    entropy = round(len(password) * math.log2(max(pool, 1)), 2) if pool else 0
    if password.lower() in COMMON:
        reasons.append('common password')
    rating = 'strong' if entropy >= 60 and len(reasons) <= 1 else 'medium' if entropy >= 40 else 'weak'
    return {'rating': rating, 'entropy_bits': entropy, 'reasons': reasons}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Password strength auditor')
    parser.add_argument('password')
    args = parser.parse_args(argv)
    result = evaluate(args.password)
    print(result)

if __name__ == '__main__':
    main()
