"""Registry routing and Media integration are fail-closed."""
import sys
import unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"studio"))
import model_runtime
class ModelRouteTests(unittest.TestCase):
    def test_unconfigured_generators_are_unavailable(self):
        for cap in ("image_generation","video_generation","3d_generation"):
            r=model_runtime.select(cap)
            self.assertFalse(r["available"])
    def test_registry_contains_real_onnx_and_dsp(self):
        d=model_runtime.options()
        names={x["id"] for x in d["providers"]}
        self.assertIn("beat-this-onnx",names);self.assertIn("micro-dsp",names)
    def test_music_requires_real_boot(self):
        with mock.patch.object(model_runtime.CORE,"status",return_value={"bootstrapped":False}):
            with self.assertRaises(RuntimeError):model_runtime.music_analysis("/fake.wav")
    def test_available_backend_reports_kind(self):
        if model_runtime.select("image_to_video")["available"]:
            self.assertEqual(model_runtime.select("image_to_video")["chosen"]["kind"],"deterministic_render")
if __name__=="__main__":unittest.main()
