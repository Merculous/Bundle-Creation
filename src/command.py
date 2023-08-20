
import subprocess

# TODO
# Get rid of shell. I do use it for asr bit, but I should
# be able to get rid of shell usage completely.


def runCommand(args):
    cmd = subprocess.run(
        args,
        capture_output=True,
        universal_newlines=True
    )

    if cmd.returncode < 0:
        print('Subprocess failed!')
        print(f'Got returncode: {cmd.returncode}')
        print(f'Ran with args: {args}')
        print(f'Stdout: {cmd.stdout}')
        print(f'Stderr: {cmd.stderr}')
        raise Exception
    else:
        return (cmd.stdout, cmd.stderr)


def runShellCommand(args):
    cmd = subprocess.run(
        ' '.join(args),
        capture_output=True,
        universal_newlines=True,
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
        return (cmd.stdout, cmd.stderr)


def runHdutil(args):
    cmd = ('bin/hdutil', *args)
    return runShellCommand(cmd)


def runXpwntool(args):
    cmd = ('bin/xpwntool', *args)
    return runShellCommand(cmd)


def runDmg(args):
    cmd = ('bin/dmg', *args)
    return runShellCommand(cmd)


def runAsrPatch(args):
    cmd = ('bin/asrpatch', *args)
    return runCommand(cmd)


def runiBoot32Patcher(args):
    cmd = ('bin/iBoot32Patcher', *args)
    return runShellCommand(cmd)


def run7zip(args):
    cmd = ('bin/7z', *args)
    return runCommand(cmd)
