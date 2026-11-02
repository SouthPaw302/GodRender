"""GodRender pinned-source and renderer safety tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"render"))
from godrender_runtime import manifest_load, within, sha256, plan, SCHEMA

class RenderManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.im=self.root/"source.png";self.im.write_bytes(b"pixel-authenticated")
        self.data={"schema":SCHEMA,"fps":24,"width":320,"height":180,
                   "shots":[{"id":"first","seconds":1.0,"mode":"still_fx","image":{"path":"source.png","sha256":sha256(self.im)},"fx_ids":["FX2-ATM-001"]}]}
        self.man=self.root/"manifest.json"
    def load(self):
        self.man.write_text(json.dumps(self.data))
        return manifest_load(self.man,self.root)
    def test_hashed_source_accepted(self):
        self.assertEqual(self.load()["shots"][0]["id"],"first")
    def test_hash_mismatch_fails_closed(self):
        self.data["shots"][0]["image"]["sha256"]="0"*64
        with self.assertRaises(ValueError):self.load()
    def test_path_escape_fails_closed(self):
        with self.assertRaises(ValueError):within(self.root,"../private.wav")
    def test_unapproved_scene_fails_closed(self):
        self.data["shots"][0]={"id":"first","mode":"godot","seconds":1,"scene":"/tmp/hack.tscn"}
        with self.assertRaises(ValueError):self.load()
    def test_arbitrary_mode_fails_closed(self):
        self.data["shots"][0]["mode"]="fictional_ai_video"
        with self.assertRaises(ValueError):self.load()
    def test_duplicate_shot_rejected(self):
        self.data["shots"].append(self.data["shots"][0].copy())
        with self.assertRaises(ValueError):self.load()
    def test_structured_fx_params_are_accepted(self):
        self.data["shots"][0]["fx_ids"]=["FX2-MOTION-002","FX2-CAMERA-023"]
        self.data["shots"][0]["fx"]=[
            {"id":"FX2-MOTION-002","params":{"roi":[0.45,0.25,1.0,0.70],"strength":0.20}},
            {"id":"FX2-CAMERA-023","params":{"zoom_start":1.0,"zoom_end":1.018,"easing":"cosine","zoom_cap":1.04}},
        ]
        loaded=self.load()
        self.assertEqual(loaded["shots"][0]["fx"][0]["params"]["strength"],0.20)

    def test_structured_fx_mismatch_fails_closed(self):
        self.data["shots"][0]["fx"]=[{"id":"FX2-LIGHT-002","params":{}}]
        with self.assertRaises(ValueError):self.load()

    def test_parallel_plan_has_stable_identity(self):
        p=self.root/"plan.json";d=self.load()
        self.assertEqual(plan(d,p)["include"][0]["shot_id"],"first")
        self.assertEqual(json.loads(p.read_text())["include"][0]["index"],0)

if __name__=="__main__":unittest.main()
