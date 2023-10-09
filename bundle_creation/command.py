
import subprocess


def runCommand(args):
    cmd = subprocess.run(args)

    if cmd.returncode < 0:
        raise Exception


def runShellCommand(args):
    cmd = subprocess.run(' '.join(args), shell=True)

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
        ' '.join(args),
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


def runDmg(args):
    cmd = (
        'bin/dmg',
        *args
    )
    return runShellCommand(cmd)


def run7zip(args):
    cmd = (
        'bin/7z',
        *args
    )
    return runShellCommandWithOutput(cmd)


def runiBoot32Patcher(args):
    cmd = (
        'bin/iBoot32Patcher',
        *args
    )
    return runShellCommand(cmd)


def runXpwntool(args):
    cmd = (
        'bin/xpwntool',
        *args
    )
    return runShellCommand(cmd)


def runHdutil(args):
    cmd = (
        'bin/hdutil',
        *args
    )
    return runShellCommand(cmd)


def runLdid(args):
    cmd = (
        'bin/ldid',
        *args
    )
    return runCommand(cmd)


def runImagetool(args):
    cmd = (
        'bin/imagetool',
        *args
    )
    return runCommand(cmd)
