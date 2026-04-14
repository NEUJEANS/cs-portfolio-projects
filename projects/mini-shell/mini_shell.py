import os, shlex, subprocess

BUILTINS = {'cd', 'pwd', 'exit'}


def run_command(command, cwd=None):
    parts = shlex.split(command)
    if not parts:
        return cwd or os.getcwd(), ''
    if parts[0] == 'cd':
        new_cwd = os.path.abspath(os.path.join(cwd or os.getcwd(), parts[1]))
        return new_cwd, ''
    if parts[0] == 'pwd':
        return cwd or os.getcwd(), cwd or os.getcwd()
    result = subprocess.run(parts, capture_output=True, text=True, cwd=cwd)
    return cwd or os.getcwd(), result.stdout.strip()


def repl():
    cwd = os.getcwd()
    while True:
        command = input(f'{cwd}$ ')
        if command.strip() == 'exit':
            break
        cwd, output = run_command(command, cwd)
        if output:
            print(output)

if __name__ == '__main__':
    repl()
