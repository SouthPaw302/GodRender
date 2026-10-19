"""Native publishing and remote dispatch require explicit approval and configured token."""
import sys,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"studio"))
import native_workspaces,github_actions
class ActionsTests(unittest.TestCase):
    def test_dispatch_without_approval_is_denied(self):
        with self.assertRaises(PermissionError):
            github_actions.dispatch(project_id="p",ref="song/p",manifest="projects/p/render.json",fixture=False,
                    approval=False,native_status={"remote_published":True,"branch":"song/p"})
    def test_dispatch_unpublished_branch_is_denied(self):
        with self.assertRaises(RuntimeError):
            github_actions.dispatch(project_id="p",ref="song/p",manifest="",fixture=True,
                    approval=True,native_status={"remote_published":False,"branch":"song/p"})
    def test_native_publish_requires_explicit_approval(self):
        with self.assertRaises(PermissionError):
            native_workspaces.publish("p")
    def test_dispatch_without_token_is_denied(self):
        with mock.patch.dict("os.environ",{"GODRENDER_GITHUB_TOKEN":"","GH_TOKEN":""}):
            with self.assertRaises(RuntimeError):
                github_actions.dispatch(project_id="p",ref="song/p",manifest="",fixture=True,
                    approval=True,native_status={"remote_published":True,"branch":"song/p"})
if __name__=="__main__":unittest.main()
