"""P5 Browser Explorer: source-grade data, Second Brain integrity, and safe handoff."""
from __future__ import annotations
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("american_empire_web",ROOT/"tools"/"build_web.py")
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

class BrowserExplorerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.brain=mod.brain_index()

    def test_source_registry_and_second_brain_are_inherited(self):
        x=self.brain
        self.assertEqual(x["schema"],"american-empire.browser-brain.v1")
        self.assertGreaterEqual(x["counts"]["fx"],90)
        self.assertGreaterEqual(x["counts"]["workflows"],10)
        self.assertGreaterEqual(x["counts"]["media_capabilities"],20)
        self.assertGreaterEqual(x["counts"]["models"],2)
        self.assertEqual(x["source_snapshot_date"],"2026-10-18")
        self.assertEqual(x["drive_links"][0]["url"],mod.DRIVE_BRAIN)
        self.assertEqual(len(x["repository_sources"]),6)
        self.assertTrue(all(len(y["git_blob_sha1"])==40 for y in x["repository_sources"]))
        self.assertEqual(x["native_studio"]["browser_automation"],"not_connected_to_this_static_explorer")

    def test_effect_authority_and_evidence_not_overstated(self):
        allfx=self.brain["fx"]
        self.assertEqual(len({e["id"] for e in allfx}),len(allfx))
        self.assertTrue(any(e["gate_status"]=="proof_required" for e in allfx))
        self.assertTrue(any(e["gate_status"]=="approved" for e in allfx))
        for effect in allfx:
            self.assertEqual(effect["authority"],"registry_metadata_only_not_execution")
            self.assertTrue(effect["source"]["path"].startswith("general/reusable/fx_v2/"))
            self.assertTrue(effect["source"]["url"].startswith(mod.GIT_BASE))
            self.assertTrue(len(effect["source"]["git_blob_sha1"])==40)
        for record in self.brain["models"]:
            self.assertEqual(record["authority"],"configured_not_executed")

    def test_source_archive_protected_and_build_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"dist"
            report=mod.build(output)
            self.assertEqual(report["schema"],"american-empire.web-build.v1")
            world=json.loads((output/"data/world.json").read_text())
            brain=json.loads((output/"data/brain.json").read_text())
            self.assertEqual(world["bundle_sha256"],brain["world_bundle_sha256"])
            self.assertEqual(world["source"],brain["world_source"])
            self.assertEqual(len(world["nodes"]),16)
            self.assertEqual(len(world["years"]),12)
            self.assertEqual(len(world["scenarios"]),3)
            self.assertTrue((output/"index.html").is_file())
            self.assertTrue((output/"app.js").is_file())
            self.assertTrue((output/"styles.css").is_file())
            self.assertTrue((output/"simulator.js").is_file())
            self.assertTrue((output/"live.js").is_file())
            self.assertTrue((output/"data/model.json").is_file())
            self.assertTrue((output/"data/geo.json").is_file())
            self.assertTrue((output/"data/land.geojson").is_file())
            self.assertTrue((output/"regions.js").is_file())
            self.assertTrue((output/"earth.js").is_file())
            self.assertTrue((output/"inhabitants.js").is_file())
            self.assertTrue((output/"people.js").is_file())
            self.assertTrue((output/"cinema.js").is_file())
            self.assertTrue((output/"data/media_inventory.json").is_file())
            media=json.loads((output/"data/media_inventory.json").read_text())
            self.assertEqual(media["fictional_world_membership"],"shared_american_empire_timeline")
            self.assertGreaterEqual(len(media["media"]),10)
            self.assertTrue(all(v["visibility"]=="private_drive_requires_permission" for v in media["media"]))
            self.assertTrue((output/"data/inhabitants.json").is_file())
            self.assertTrue((output/"data/people_source.json").is_file())
            actors=json.loads((output/"data/inhabitants.json").read_text())
            self.assertEqual(len(actors["protagonists"]),5)
            self.assertEqual(len(actors["organizations"]),5)
            self.assertEqual(len(actors["trust_links"]),36)
            self.assertEqual(len(actors["source_manifest_sha256"]),64)
            self.assertEqual(len(actors["film_cast"]),2)
            self.assertTrue((output/"data/film_bridge.json").is_file())
            film=json.loads((output/"data/film_bridge.json").read_text())
            self.assertEqual(film["film_event"]["story_year"],"undated_in_checked_scripts")
            self.assertEqual({x["id"] for x in film["agents"]},{"claire","daniel"})
            self.assertEqual(len(json.loads((output/"data/geo.json").read_text())["nodes"]),13)
            self.assertEqual(len(json.loads((output/"data/geo.json").read_text())["routes"]),18)
            self.assertTrue((output/"data/reference_scenarios.json").is_file())
            sources=json.loads((output/"data/reference_scenarios.json").read_text())
            self.assertEqual([s["id"] for s in sources],["baseline","independent-corridor","high-integration"])
            self.assertEqual(json.loads((output/"data/model.json").read_text())["schema"],"american-empire.simulation-model.v1")
            standalone = (output/"standalone.html").read_text(encoding="utf-8")
            self.assertIn('id="embeddedWorld"', standalone)
            self.assertIn('id="embeddedBrain"', standalone)
            self.assertIn('id="embeddedModel"', standalone)
            self.assertIn('id="embeddedReference"', standalone)
            self.assertIn('id="embeddedGeo"', standalone)
            self.assertIn('id="embeddedLand"', standalone)
            self.assertIn('id="embeddedInhabitants"', standalone)
            self.assertIn('id="embeddedPeopleSource"', standalone)
            self.assertIn('id="embeddedMediaInventory"', standalone)
            self.assertIn('id="embeddedFilmBridge"', standalone)
            self.assertIn('P5 browser-native deterministic P3 simulation', standalone)
            self.assertIn('<style>', standalone)
            self.assertIn('counterfactual_adaptation_not_canon', standalone)
            first={str(p.relative_to(output)):p.read_bytes() for p in output.rglob("*") if p.is_file()}
            mod.build(output)
            second={str(p.relative_to(output)):p.read_bytes() for p in output.rglob("*") if p.is_file()}
            self.assertEqual(first,second)
            self.assertNotIn("secret",str(brain).lower())
            self.assertNotIn("access_token",str(brain).lower())

    def test_refuses_source_overwrite(self):
        for p in [ROOT/"archive"/"no.json",ROOT/"web"/"src",ROOT/"web"/"src"/"subdir",ROOT/"engine"]:
            with self.subTest(p=p):
                with self.assertRaises(ValueError):
                    mod.build(p)

    def test_interface_references_existing_controls(self):
        html=(ROOT/"web/src/index.html").read_text()
        js=(ROOT/"web/src/app.js").read_text() + (ROOT/"web/src/live.js").read_text() + (ROOT/"web/src/earth.js").read_text() + (ROOT/"web/src/people.js").read_text() + (ROOT/"web/src/cinema.js").read_text()
        css=(ROOT/"web/src/styles.css").read_text()
        for ident in ["world","chronology","brain","production","simulation","earth","inhabitants","cinema","cinemaItems","cinemaPlay","cinemaOpen","cinemaFrame","cinemaFindClaire","cinemaFindDaniel","peopleYear","peopleCards","personApply","personExport","geoYear","earthMap","geoApply","geoExport","liveScenario","liveApply","liveIntensity","liveCompare","liveReplay","liveSave","liveExport","liveImportFile","scenarioSelect","yearSlider",
                      "brainSearch","brainGate","brainCategory","copyBrief","downloadBrief",
                      "brainSelected","entityDetail","timelineList","graph"]:
            self.assertIn('id="'+ident+'"',html)
            self.assertIn(ident,js)
        self.assertIn('not_connected_to_this_static_explorer',json.dumps(self.brain))
        self.assertIn("counterfactual_adaptation_not_canon",js)
        self.assertIn("--gold:",css)

if __name__=="__main__":
    unittest.main()
