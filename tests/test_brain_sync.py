"""Google Drive sync publishes only actual technical, never artistic, evidence."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"render"))
import brain_sync
class BrainSyncTests(unittest.TestCase):
    def setUp(self):
        self.d={"schema":"godrender.film-receipt.v1","status":"TECHNICAL_RENDER_PASS_VISUAL_REVIEW_PENDING",
                "production_complete":False,"human_visual_approval":False,
                "sha256":"f"*64,"shards":[{"shot":"s01","video_sha256":"a"*64}]}
        self.url="https://github.com/SouthPaw302/GodRender/actions/runs/123456"
    def test_row_contains_evidence_and_is_unapproved(self):
        row=brain_sync.proof_row(self.d,self.url)
        self.assertEqual(row[0],"GR-RUN-123456")
        self.assertIn("PENDING",row[3])
    def test_forged_creative_approval_refused(self):
        self.d["human_visual_approval"]=True
        with self.assertRaises(ValueError):brain_sync.proof_row(self.d,self.url)
    def test_external_run_link_refused(self):
        with self.assertRaises(ValueError):
            brain_sync.proof_row(self.d,"https://github.com/stranger/repo/actions/runs/123")
if __name__=="__main__":unittest.main()
