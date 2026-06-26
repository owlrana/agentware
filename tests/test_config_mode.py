"""Tests for the workspace KB-mode + per-user-handle config flags.

Feature 260625-team-mode-onboarding-fork. These flags are DISTINCT from the
pre-existing retrieval `--set-mode` (deterministic|semantic): the new
`--set-kb-mode power|team` / `--kb-mode-only` and `--set-user-handle` /
`--user-handle-only` record the workspace mode and per-user provenance handle.

Hermetic: the CLI persists to ~/.agentware/config.env, so every test redirects
the module's HOME_CONFIG/CONFIG_PATHS to a fresh tempfile and clears the relevant
env vars — the operator's real config is NEVER touched (R-LOC-03).
"""

import contextlib
import io
import os
import tempfile
import unittest

from tests._fixtures import load_cli


@contextlib.contextmanager
def isolated_config(env=None):
    """Run with HOME_CONFIG/CONFIG_PATHS redirected to a temp file + clean env."""
    mod = load_cli()
    tmpd = tempfile.mkdtemp(prefix="agentware-cfgtest-")
    cfg = os.path.join(tmpd, "config.env")
    saved = (mod.HOME_CONFIG, mod.CONFIG_PATHS)
    saved_env = {}
    for k in ("AGENTWARE_KB_MODE", "AGENTWARE_USER_HANDLE",
              "AGENTWARE_RETRIEVAL_MODE"):
        saved_env[k] = os.environ.pop(k, None)
    if env:
        os.environ.update(env)
    mod.HOME_CONFIG = cfg
    mod.CONFIG_PATHS = (cfg,)
    try:
        yield mod, cfg
    finally:
        mod.HOME_CONFIG, mod.CONFIG_PATHS = saved
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        if env:
            for k in env:
                if k not in saved_env:
                    os.environ.pop(k, None)
        import shutil
        shutil.rmtree(tmpd, ignore_errors=True)


def run(mod, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mod.main(argv)
    return code, out.getvalue(), err.getvalue()


class KbModeTests(unittest.TestCase):
    def test_default_is_power(self):
        with isolated_config() as (mod, _cfg):
            code, out, _ = run(mod, ["config", "--kb-mode-only"])
            self.assertEqual(code, 0)
            self.assertEqual(out.strip(), "power")

    def test_set_team_roundtrips(self):
        with isolated_config() as (mod, cfg):
            code, _, _ = run(mod, ["config", "--set-kb-mode", "team"])
            self.assertEqual(code, 0)
            code, out, _ = run(mod, ["config", "--kb-mode-only"])
            self.assertEqual(out.strip(), "team")
            # Persisted to the config file, not lost.
            self.assertIn("AGENTWARE_KB_MODE=team", open(cfg).read())

    def test_set_power_roundtrips(self):
        with isolated_config() as (mod, _cfg):
            run(mod, ["config", "--set-kb-mode", "team"])
            run(mod, ["config", "--set-kb-mode", "power"])
            code, out, _ = run(mod, ["config", "--kb-mode-only"])
            self.assertEqual(out.strip(), "power")

    def test_bogus_rejected(self):
        with isolated_config() as (mod, _cfg):
            code, _, err = run(mod, ["config", "--set-kb-mode", "bogus"])
            self.assertNotEqual(code, 0)
            self.assertIn("invalid --set-kb-mode", err)

    def test_env_overrides_config(self):
        with isolated_config() as (mod, _cfg):
            run(mod, ["config", "--set-kb-mode", "power"])
        with isolated_config(env={"AGENTWARE_KB_MODE": "team"}) as (mod, _cfg):
            code, out, _ = run(mod, ["config", "--kb-mode-only"])
            self.assertEqual(out.strip(), "team")

    def test_does_not_collide_with_retrieval_set_mode(self):
        # The pre-existing retrieval --set-mode must still work and be independent.
        with isolated_config() as (mod, cfg):
            run(mod, ["config", "--set-mode", "semantic"])
            run(mod, ["config", "--set-kb-mode", "team"])
            txt = open(cfg).read()
            self.assertIn("AGENTWARE_RETRIEVAL_MODE=semantic", txt)
            self.assertIn("AGENTWARE_KB_MODE=team", txt)
            code, out, _ = run(mod, ["config", "--kb-mode-only"])
            self.assertEqual(out.strip(), "team")


class UserHandleTests(unittest.TestCase):
    def test_unset_prints_empty(self):
        with isolated_config() as (mod, _cfg):
            code, out, _ = run(mod, ["config", "--user-handle-only"])
            self.assertEqual(code, 0)
            self.assertEqual(out.strip(), "")

    def test_roundtrip(self):
        with isolated_config() as (mod, _cfg):
            run(mod, ["config", "--set-user-handle", "alice"])
            code, out, _ = run(mod, ["config", "--user-handle-only"])
            self.assertEqual(out.strip(), "alice")

    def test_spaces_quotes_sanitized_no_corruption(self):
        with isolated_config() as (mod, cfg):
            code, _, _ = run(mod, ["config", "--set-user-handle", 'Alice "The" Smith!'])
            self.assertEqual(code, 0)
            # The persisted config must remain a single clean KEY=VALUE line.
            lines = [l for l in open(cfg).read().splitlines()
                     if l.startswith("AGENTWARE_USER_HANDLE=")]
            self.assertEqual(len(lines), 1)
            val = lines[0].split("=", 1)[1]
            self.assertNotIn(" ", val)
            self.assertNotIn('"', val)
            # Reads back as a safe token.
            code, out, _ = run(mod, ["config", "--user-handle-only"])
            self.assertTrue(out.strip())
            self.assertNotIn(" ", out)

    def test_all_invalid_handle_rejected(self):
        with isolated_config() as (mod, _cfg):
            code, _, err = run(mod, ["config", "--set-user-handle", "!!! @@@"])
            self.assertNotEqual(code, 0)
            self.assertIn("invalid --set-user-handle", err)


if __name__ == "__main__":
    unittest.main()
