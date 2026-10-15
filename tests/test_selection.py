import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from image_lib import valid_base_update

spec = importlib.util.spec_from_file_location('changed', Path(__file__).resolve().parents[1] / 'scripts/changed-images.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        for name in ['first', 'second']:
            p = self.root / 'images' / name / 'Dockerfile'
            p.parent.mkdir(parents=True)
            p.write_text('FROM scratch\n')
        self.base = self.commit()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True).strip()

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def change(self, path):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('changed\n')
        return module.changed(self.base, self.commit(), self.root)

    def test_only_changed_image(self):
        self.assertEqual(self.change('images/first/packages.txt'), ['first'])

    def test_base_lock_selects_only_its_image(self):
        self.assertEqual(self.change('images/second/base-image.json'), ['second'])

    def test_common_script_selects_all(self):
        self.assertEqual(self.change('scripts/build.sh'), ['first', 'second'])

    def test_readme_does_not_build(self):
        self.assertEqual(self.change('README.md'), [])

    def test_deleted_image_file_still_selects_image(self):
        self.change('images/first/packages.txt')
        self.base = self.git('rev-parse', 'HEAD')
        (self.root / 'images/first/packages.txt').unlink()
        self.assertEqual(module.changed(self.base, self.commit(), self.root), ['first'])

    def test_initial_push_selects_all(self):
        self.assertEqual(module.changed('0' * 40, self.base, self.root), ['first', 'second'])

    def test_image_smoke_change_is_selected(self):
        self.assertEqual(self.change('images/first/tests/smoke.sh'), ['first'])

    def test_workflow_change_selects_all(self):
        self.assertEqual(self.change('.github/workflows/verify.yml'), ['first', 'second'])


class UpdateGuardTests(unittest.TestCase):
    def setUp(self):
        self.before = {'image': 'ghcr.io/actions/actions-runner', 'tracking_tag': 'latest',
                       'platform': 'linux/amd64', 'digest': 'sha256:' + 'a' * 64}
        self.after = dict(self.before, digest='sha256:' + 'b' * 64)

    def test_digest_only_is_allowed(self):
        self.assertTrue(valid_base_update(self.before, self.after))

    def test_registry_change_is_rejected(self):
        self.after['image'] = 'example.invalid/other/runner'
        self.assertFalse(valid_base_update(self.before, self.after))

    def test_extra_field_is_rejected(self):
        self.after['command'] = 'unexpected'
        self.assertFalse(valid_base_update(self.before, self.after))

    def test_malformed_or_unchanged_digest_is_rejected(self):
        self.assertFalse(valid_base_update(self.before, self.before))
        self.after['digest'] = 'not-a-digest'
        self.assertFalse(valid_base_update(self.before, self.after))


if __name__ == '__main__':
    unittest.main()
