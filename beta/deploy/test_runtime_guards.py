"""Focused bootstrap checks; no cloud resources, mount or UID claims."""
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('genius_start',Path(__file__).with_name('start.py'))
start=importlib.util.module_from_spec(spec)
spec.loader.exec_module(start)


class RuntimeGuardTests(unittest.TestCase):
    def test_production_refuses_baked_directory_without_real_mount(self):
        with patch.dict(start.os.environ, {'GENIUS_ENV':'production'}, clear=True), patch.object(start.os.path,'ismount',return_value=False), patch.object(start,'prepare_identity') as identity:
            with self.assertRaisesRegex(RuntimeError,'mounted at /data'):
                start.main()
            identity.assert_not_called()

    def test_railway_requires_provider_volume_metadata(self):
        env={'GENIUS_ENV':'production','RAILWAY_SERVICE_ID':'synthetic-service'}
        with patch.dict(start.os.environ,env,clear=True), patch.object(start.os.path,'ismount',return_value=True):
            with self.assertRaisesRegex(RuntimeError,'metadata'):
                start.validate_runtime_environment()
            start.os.environ['RAILWAY_VOLUME_NAME']='synthetic-volume'
            start.os.environ['RAILWAY_VOLUME_MOUNT_PATH']='/other'
            with self.assertRaisesRegex(RuntimeError,'metadata'):
                start.validate_runtime_environment()
            start.os.environ['RAILWAY_VOLUME_MOUNT_PATH']='/data'
            start.validate_runtime_environment()

    def test_management_credentials_are_rejected_without_exposure(self):
        for name in start.MANAGEMENT_VARIABLES:
            with self.subTest(name=name), patch.dict(start.os.environ,{name:'synthetic-secret-do-not-print'},clear=True):
                out=io.StringIO()
                with contextlib.redirect_stdout(out),contextlib.redirect_stderr(out):
                    with self.assertRaises(RuntimeError) as raised:
                        start.validate_runtime_environment()
                self.assertNotIn('synthetic-secret-do-not-print',str(raised.exception)+out.getvalue())

    def test_production_rejects_wrong_data_path_and_local_development_remains_local(self):
        with patch.dict(start.os.environ,{'GENIUS_ENV':'production','GENIUS_DATA_DIR':'/tmp/ephemeral'},clear=True):
            with self.assertRaisesRegex(RuntimeError,'GENIUS_DATA_DIR'):
                start.validate_runtime_environment()
        with patch.dict(start.os.environ,{'GENIUS_ENV':'development'},clear=True), patch.object(start.os.path,'ismount',return_value=False):
            start.validate_runtime_environment()

    def test_symlink_data_directory_is_rejected_before_writes_for_every_uid(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            outside=base/'outside'
            outside.mkdir()
            link=base/'genius'
            link.symlink_to(outside,target_is_directory=True)
            for uid in (0,10001):
                with self.subTest(uid=uid), patch.dict(start.os.environ,{'GENIUS_DATA_DIR':str(link)},clear=True), patch.object(start.os,'geteuid',return_value=uid), patch.object(start.os,'chown') as chown, patch.object(start.Path,'mkdir') as mkdir:
                    with self.assertRaisesRegex(RuntimeError,'symbolic links'):
                        start.prepare_identity()
                    mkdir.assert_not_called()
                    chown.assert_not_called()
            with patch.dict(start.os.environ,{'GENIUS_ENV':'production'},clear=True), patch.object(start,'Path',return_value=link), patch.object(start.os.path,'ismount',return_value=True), patch.object(start,'prepare_identity') as identity:
                with self.assertRaisesRegex(RuntimeError,'symbolic links'):
                    start.main()
                identity.assert_not_called()
            self.assertEqual(list(outside.iterdir()),[])


if __name__=='__main__':
    unittest.main(verbosity=2)
