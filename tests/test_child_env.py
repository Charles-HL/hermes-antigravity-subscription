"""Tests for build_child_env and SSH environment variable scrubbing (issue #18).

agy 1.2.16 detects SSH sessions via SSH_CONNECTION, SSH_CLIENT, or SSH_TTY and
switches to file-based token storage ("Using file-based token storage because SSH
session detected"). When credentials live in the OS keyring and no real token file
exists, build_child_env must strip those variables on POSIX while leaving
SSH_AUTH_SOCK intact and preserving parent os.environ.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

plugin_dir = Path(__file__).resolve().parent.parent
if str(plugin_dir) not in sys.path:
    sys.path.insert(0, str(plugin_dir))

from process import build_child_env


class ChildEnvTests(unittest.TestCase):
    def test_posix_no_token_file_strips_ssh_session_vars_and_keeps_auth_sock(self):
        env_sample = {
            "HOME": "/original/home",
            "PATH": "/usr/bin:/bin",
            "SSH_CONNECTION": "192.168.1.50 54321 192.168.1.1 22",
            "SSH_CLIENT": "192.168.1.50 54321 22",
            "SSH_TTY": "/dev/pts/2",
            "SSH_AUTH_SOCK": "/tmp/ssh-agent.sock",
        }
        with patch.dict(os.environ, env_sample, clear=True):
            with patch("process.os.name", "posix"):
                with patch("process.resolve_real_token_path", return_value=None):
                    child_env = build_child_env("/isolated/home")

        self.assertEqual(child_env["HOME"], "/isolated/home")
        self.assertNotIn("SSH_CONNECTION", child_env)
        self.assertNotIn("SSH_CLIENT", child_env)
        self.assertNotIn("SSH_TTY", child_env)
        self.assertIn("SSH_AUTH_SOCK", child_env)
        self.assertEqual(child_env["SSH_AUTH_SOCK"], "/tmp/ssh-agent.sock")

    def test_posix_with_token_file_preserves_all_ssh_vars(self):
        token_path = Path("/path/to/jetski-standalone-oauth-token")
        env_sample = {
            "HOME": "/original/home",
            "SSH_CONNECTION": "192.168.1.50 54321 192.168.1.1 22",
            "SSH_CLIENT": "192.168.1.50 54321 22",
            "SSH_TTY": "/dev/pts/2",
            "SSH_AUTH_SOCK": "/tmp/ssh-agent.sock",
        }
        with patch.dict(os.environ, env_sample, clear=True):
            with patch("process.os.name", "posix"):
                with patch("process.resolve_real_token_path", return_value=token_path):
                    child_env = build_child_env("/isolated/home")

        self.assertEqual(child_env["HOME"], "/isolated/home")
        self.assertEqual(child_env["SSH_CONNECTION"], "192.168.1.50 54321 192.168.1.1 22")
        self.assertEqual(child_env["SSH_CLIENT"], "192.168.1.50 54321 22")
        self.assertEqual(child_env["SSH_TTY"], "/dev/pts/2")
        self.assertEqual(child_env["SSH_AUTH_SOCK"], "/tmp/ssh-agent.sock")

    def test_parent_os_environ_remains_intact(self):
        env_sample = {
            "HOME": "/original/home",
            "SSH_CONNECTION": "10.0.0.1 12345 10.0.0.2 22",
            "SSH_CLIENT": "10.0.0.1 12345 22",
            "SSH_TTY": "/dev/pts/0",
            "SSH_AUTH_SOCK": "/run/user/1000/keyring/ssh",
        }
        with patch.dict(os.environ, env_sample, clear=True):
            with patch("process.os.name", "posix"):
                with patch("process.resolve_real_token_path", return_value=None):
                    build_child_env("/isolated/home")

            # Parent os.environ must still contain all original keys and values
            self.assertEqual(os.environ["HOME"], "/original/home")
            self.assertEqual(os.environ["SSH_CONNECTION"], "10.0.0.1 12345 10.0.0.2 22")
            self.assertEqual(os.environ["SSH_CLIENT"], "10.0.0.1 12345 22")
            self.assertEqual(os.environ["SSH_TTY"], "/dev/pts/0")
            self.assertEqual(os.environ["SSH_AUTH_SOCK"], "/run/user/1000/keyring/ssh")

    def test_windows_nt_does_not_strip_ssh_vars(self):
        env_sample = {
            "USERPROFILE": r"C:\Users\tester",
            "HOMEPATH": r"\Users\tester",
            "SSH_CONNECTION": "192.168.1.50 54321 192.168.1.1 22",
            "SSH_CLIENT": "192.168.1.50 54321 22",
            "SSH_TTY": "pty1",
            "SSH_AUTH_SOCK": r"\\.\pipe\openssh-ssh-agent",
        }
        with patch.dict(os.environ, env_sample, clear=True):
            with patch("process.os.name", "nt"):
                with patch("process.resolve_real_token_path", return_value=None):
                    child_env = build_child_env(r"C:\isolated\home")

        self.assertEqual(child_env["USERPROFILE"], r"C:\isolated\home")
        self.assertEqual(child_env["HOMEPATH"], r"C:\isolated\home")
        self.assertIn("SSH_CONNECTION", child_env)
        self.assertIn("SSH_CLIENT", child_env)
        self.assertIn("SSH_TTY", child_env)
        self.assertIn("SSH_AUTH_SOCK", child_env)


if __name__ == "__main__":
    unittest.main()
