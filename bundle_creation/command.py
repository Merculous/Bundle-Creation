
import subprocess

# I would like to get rid shell completely...


class Command:
    def __init__(self) -> None:
        pass

    def runCommand(self, cmd_args):
        cmd = subprocess.run(cmd_args, capture_output=True, text=True)

        to_return = (
            cmd_args,
            cmd.returncode,
            cmd.stdout,
            cmd.stderr
        )

        return to_return
