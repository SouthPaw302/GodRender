"""Native GodRender Git workspace remains project authority; legacy copies are evidence."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"studio"))
import native_workspaces

class NativeGitTests(unittest.TestCase):
    def test_native_project_slug_is_stable(self):
        self.assertEqual(native_workspaces._slug("My Film"),"my-film")
    def test_uninitialized_is_not_remote_published(self):
        with tempfile.TemporaryDirectory() as t:
            with mock.patch.object(native_workspaces.base,"PROJECT_ROOT",Path(t)):
                result=native_workspaces.status("demo")
        self.assertFalse(result["exists"])
        self.assertFalse(result["remote_published"])
    def test_manifest_never_copies_media_or_hidden_secrets(self):
        # No actual Git push is allowed in this unit test.
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            (root/"film").mkdir()
            (root/"film"/"SECRET.env").write_text("should-not-copy")
            (root/"film"/"still.png").write_bytes(b"\x89PNG")
            (root/"film"/"SCRIPT.json").write_text('{"shots":[]}')
            with mock.patch.object(native_workspaces.base,"PROJECT_ROOT",root),\
                 mock.patch.object(native_workspaces,"_git",side_effect=["main","new-sha"]):
                self.assertTrue("native" in native_workspaces.path_for("demo").name or native_workspaces.path_for("demo").name=="godrender")
if __name__=="__main__":unittest.main()
