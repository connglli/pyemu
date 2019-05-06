import re
import shlex
from pathlib import Path
from telnetlib import Telnet
from typing import List, Optional


class AndroidEmuCommand:
    AUTH = 'auth'
    AVD = 'avd'


class AndroidEmuException(Exception):

    def __init__(self, message):
        super().__init__(message)


class AndroidEmu:

    RET_OK = re.compile(b'.*?OK\r\n$')
    RET_KO = re.compile(b'.*?KO: .*?$')

    def __init__(self, log_command: bool = True, log_output: bool = True):
        self._is_log_command_enabled = log_command
        self._is_log_output_enabled = log_output
        self._host = None
        self._port = None
        self._client = None

    def open(self, host='localhost', port=5554):
        self._host = host
        self._port = port

        if self._is_log_command_enabled:
            print('-> open {}:{}'.format(host, port))

        self._client = Telnet(host, port)
        output = AndroidEmu._decode_output(self._client.read_until(b'OK\r\n'))

        if self._is_log_output_enabled:
            print(output + '\n')

    def close(self):
        self._client.close()

    def enable_logging_command(self, enabled: bool = True):
        """
        Enable or disable logging command
        :param enabled: enable or not
        :return:
        """
        self._is_log_command_enabled = enabled
        return self

    def enable_logging_output(self, enabled: bool = True):
        """
        Enable or disable logging output
        :param enabled: enable or not
        :return:
        """
        self._is_log_output_enabled = enabled
        return self

    def auth(self, auth_path: Path):
        with auth_path.open(mode='r', encoding='utf-8') as f:
            token = f.read()
        emu_command = [AndroidEmuCommand.AUTH, token.strip(' \t\r\n')]
        return self._exec_command(emu_command)

    def avd(self, command: str, args):
        emu_command = [AndroidEmuCommand.AVD, command]
        emu_command.extend(shlex.split(args))
        return self._exec_command(emu_command)

    def _exec_command(self, emu_cmd: List[str], timeout=10):
        if self._client is None:
            raise AndroidEmuException('AndroidEmu is not by far opened')

        cmd = AndroidEmu._from_command(emu_cmd)
        if self._is_log_command_enabled:
            print('-> {}'.format(cmd))

        # send commands
        self._client.write(AndroidEmu._encode_command(cmd + '\n'))
        # read output, trick: we can directly use index as the returncode
        returncode, _, output = self._client.expect([AndroidEmu.RET_OK, AndroidEmu.RET_KO],
                                                    timeout=timeout)
        output = AndroidEmu._decode_output(output)

        if self._is_log_output_enabled:
            print(output + '\n')

        return returncode, output

    @staticmethod
    def _from_command(emu_cmd: List[str]):
        return ' '.join(emu_cmd)

    @staticmethod
    def _encode_command(cmd: Optional[str]):
        return b'' if cmd is None else cmd.encode(encoding='ascii')

    @staticmethod
    def _decode_output(output: Optional[bytes]):
        return '' if output is None else output.decode(encoding='utf-8').strip(' \t\r\n')


if __name__ == '__main__':
    emu = AndroidEmu(log_output=False, log_command=True)
    emu.open(host='localhost', port=5554)

    try:
        retc, result = emu.auth(Path.home() / '.emulator_console_auth_token')
        print('>> [{}]\n{}\n'.format(retc, result))

        retc, result = emu.avd('snapshot', 'list')
        print('>> [{}]\n{}\n'.format(retc, result))
    except Exception as e:
        print(e)
    finally:
        emu.close()
