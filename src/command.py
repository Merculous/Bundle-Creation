
import subprocess


def runCommand(args):
    cmd = subprocess.run(args)

    if cmd.returncode < 0:
        raise Exception


def runShellCommand(args):
    cmd = subprocess.run(args, shell=True)

    if cmd.returncode < 0:
        raise Exception


def runCommandWithOutput(args):
    cmd = subprocess.run(
        args,
        capture_output=True,
        text=True
    )

    if cmd.returncode < 0:
        print('Subprocess failed!')
        print(f'Got returncode: {cmd.returncode}')
        print(f'Ran with args: {args}')
        print(f'Stdout: {cmd.stdout}')
        print(f'Stderr: {cmd.stderr}')
        raise Exception
    else:
        return cmd.stdout, cmd.stderr


def runShellCommandWithOutput(args):
    cmd = subprocess.run(
        args,
        capture_output=True,
        text=True,
        shell=True
    )

    if cmd.returncode < 0:
        print('Subprocess failed!')
        print(f'Got returncode: {cmd.returncode}')
        print(f'Ran with args: {args}')
        print(f'Stdout: {cmd.stdout}')
        print(f'Stderr: {cmd.stderr}')
        raise Exception
    else:
        return cmd.stdout, cmd.stderr
