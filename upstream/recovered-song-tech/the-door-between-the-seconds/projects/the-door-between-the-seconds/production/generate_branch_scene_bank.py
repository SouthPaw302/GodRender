#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "production" / "generated_scene_bank"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 960, 540
SEED = 302

SCENES = {
    "rainy_gothic_castle_entrance.jpg": ("castle", 1),
    "gothic_moonlit_departure.jpg": ("threshold", 2),
    "gothic_noblewoman_by_the_rainy_moonlit_window.jpg": ("window", 3),
    "gothic_temptress_in_the_rain.jpg": ("rain_portrait", 4),
    "a_cinematic_moody_gothic_fantasy_realistic_inte.jpg": ("memory_room", 5),
    "gothic_moonlit_rose_chamber.jpg": ("rose_chamber", 6),
    "gothic_moonlit_corridor_portrait.jpg": ("corridor", 7),
    "gothic_moonlit_victorian_portrait.jpg": ("portrait", 8),
    "candlelit_gothic_cathedral_romance.jpg": ("cathedral", 9),
    "gothic_moonlit_baroque_sanctuary.jpg": ("sanctuary", 10),
    "moonlit_gothic_aristocrat_by_the_window.jpg": ("window", 11),
    "gothic_noblewoman_s_temporal_echo.jpg": ("temporal", 12),
    "gothic_dawn_in_the_cathedral_of_roses.jpg": ("dawn_cathedral", 13),
    "moonlit_gothic_romance_by_candlelight.jpg": ("candle_contact", 14),
    "gothic_romance_by_moonlit_rain.jpg": ("rain_contact", 15),
    "moonlit_gothic_romance_by_the_window.jpg": ("window_contact", 16),
    "gothic_vampiric_reverie_by_moonlit_window.jpg": ("vampire_window", 17),
    "gothic_crypt_empress_in_morning_light.jpg": ("crypt", 18),
    "gothic_rose_studded_crypt_romance.jpg": ("crypt_roses", 19),
    "rainlit_gothic_aristocrat_at_the_window.jpg": ("window", 20),
    "gothic_velvet_candlelit_chamber.jpg": ("velvet_chamber", 21),
    "gothic_rainfall_by_candlelight.jpg": ("rain_candle", 22),
    "moonlit_gothic_velvet_reverie.jpg": ("velvet_reverie", 23),
    "moonlit_gothic_rose_chamber.jpg": ("rose_chamber", 24),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gradient(top, bottom):
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    a = np.array(top, np.float32)[None, None, :]
    b = np.array(bottom, np.float32)[None, None, :]
    return np.repeat(a * (1 - t) + b * t, W, axis=1).astype(np.uint8)


def glow_circle(im, center, radius, color, strength=1.0):
    layer = np.zeros_like(im)
    cv2.circle(layer, center, radius, color, -1, cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), radius * .38)
    return cv2.addWeighted(im, 1.0, layer, strength, 0)


def arch(im, x, y, w, h, color=(36, 31, 39), thickness=20):
    cv2.rectangle(im, (x, y + h // 3), (x + w, y + h), color, thickness)
    cv2.ellipse(im, (x + w // 2, y + h // 3), (w // 2, h // 3), 180, 0, 180, color, thickness, cv2.LINE_AA)


def candles(im, rng, count=10, base_y=H - 70):
    for _ in range(count):
        x = int(rng.uniform(55, W - 55)); y = int(base_y + rng.uniform(-55, 20))
        hh = int(rng.uniform(22, 58))
        cv2.rectangle(im, (x - 3, y - hh), (x + 3, y), (105, 95, 84), -1)
        cv2.ellipse(im, (x, y - hh - 6), (3, 8), 0, 0, 360, (55, 175, 255), -1, cv2.LINE_AA)
        im[:] = glow_circle(im, (x, y - hh - 6), 16, (12, 46, 95), .34)


def roses(im, rng, count=35, y_range=(320, 525)):
    for _ in range(count):
        x = int(rng.uniform(25, W - 25)); y = int(rng.uniform(*y_range)); r = int(rng.uniform(3, 9))
        c = (int(rng.uniform(18, 38)), int(rng.uniform(16, 31)), int(rng.uniform(82, 145)))
        for k in range(5):
            a = k * math.tau / 5
            cv2.circle(im, (x + int(math.cos(a) * r * .55), y + int(math.sin(a) * r * .45)), max(2, r // 2), c, -1, cv2.LINE_AA)


def rain_lines(im, rng, count=150):
    overlay = im.copy()
    for _ in range(count):
        x = int(rng.uniform(0, W)); y = int(rng.uniform(-30, H)); ln = int(rng.uniform(8, 28))
        cv2.line(overlay, (x, y), (x - 4, y + ln), (135, 147, 160), 1, cv2.LINE_AA)
    cv2.addWeighted(overlay, .22, im, .78, 0, im)


def pandora(im, x=.55, scale=1.0, facing=1, echo=False, eyes=True):
    cx = int(W * x); ground = int(H * .91); s = scale
    layer = np.zeros_like(im)
    # velvet gown and shoulders
    body = np.array([
        [cx - int(43*s), ground - int(230*s)], [cx + int(42*s), ground - int(230*s)],
        [cx + int(108*s), ground], [cx - int(115*s), ground]
    ], np.int32)
    cv2.fillConvexPoly(layer, body, (24, 24, 92), cv2.LINE_AA)
    cv2.polylines(layer, [body], True, (12, 12, 25), max(2, int(4*s)), cv2.LINE_AA)
    # neck and pale face
    cv2.rectangle(layer, (cx-int(13*s), ground-int(285*s)), (cx+int(13*s), ground-int(225*s)), (155, 164, 176), -1)
    face_center = (cx, ground-int(315*s))
    cv2.ellipse(layer, face_center, (int(34*s), int(45*s)), 0, 0, 360, (166, 174, 187), -1, cv2.LINE_AA)
    # hair mass, then reveal face again to keep a pale mask framed by black hair
    cv2.ellipse(layer, (cx, ground-int(308*s)), (int(55*s), int(72*s)), 0, 0, 360, (12, 10, 18), -1, cv2.LINE_AA)
    cv2.ellipse(layer, face_center, (int(31*s), int(42*s)), 0, 0, 360, (166, 174, 187), -1, cv2.LINE_AA)
    # hair curtains
    cv2.ellipse(layer, (cx-int(39*s), ground-int(270*s)), (int(24*s), int(76*s)), -8*facing, 0, 360, (10, 9, 16), -1, cv2.LINE_AA)
    cv2.ellipse(layer, (cx+int(39*s), ground-int(270*s)), (int(24*s), int(76*s)), 8*facing, 0, 360, (10, 9, 16), -1, cv2.LINE_AA)
    # eyes, brows, lips: subtle vampire cues
    ey = ground-int(322*s); sep=int(12*s)
    cv2.line(layer, (cx-sep-int(8*s), ey-int(7*s)), (cx-sep+int(7*s), ey-int(9*s)), (44, 41, 47), max(1,int(2*s)), cv2.LINE_AA)
    cv2.line(layer, (cx+sep-int(7*s), ey-int(9*s)), (cx+sep+int(8*s), ey-int(7*s)), (44, 41, 47), max(1,int(2*s)), cv2.LINE_AA)
    if eyes:
        cv2.circle(layer, (cx-sep, ey), max(1,int(2*s)), (22, 34, 132), -1, cv2.LINE_AA)
        cv2.circle(layer, (cx+sep, ey), max(1,int(2*s)), (22, 34, 132), -1, cv2.LINE_AA)
    cv2.ellipse(layer, (cx, ground-int(296*s)), (int(10*s), int(3*s)), 0, 0, 180, (35, 34, 103), 2, cv2.LINE_AA)
    # lace tracery
    for yy in range(ground-int(210*s), ground-int(25*s), max(12,int(22*s))):
        cv2.line(layer, (cx-int(62*s), yy), (cx+int(62*s), yy+int(8*s)), (38, 31, 49), 1, cv2.LINE_AA)
    if echo:
        ghost = cv2.GaussianBlur(layer, (0, 0), 2.2)
        M = np.float32([[1,0,-54*facing],[0,1,-3]])
        ghost = cv2.warpAffine(ghost, M, (W,H), borderMode=cv2.BORDER_CONSTANT)
        im[:] = cv2.addWeighted(im, 1.0, ghost, .22, 0)
    mask = cv2.cvtColor(layer, cv2.COLOR_BGR2GRAY)
    mask = np.clip(mask.astype(np.float32)/170.0, 0, 1)[...,None]
    im[:] = np.clip(im.astype(np.float32)*(1-mask)+layer.astype(np.float32)*mask,0,255).astype(np.uint8)


def environment(family, variant):
    rng = np.random.default_rng(SEED + variant * 101)
    dawn = family in {"dawn_cathedral", "crypt", "crypt_roses"}
    top = (20, 17, 28) if not dawn else (38, 40, 56)
    bottom = (7, 7, 12) if not dawn else (18, 20, 31)
    im = gradient(top, bottom)
    # moon / dawn source
    if dawn:
        im[:] = glow_circle(im, (int(W*.80), int(H*.13)), 92, (44, 67, 112), .34)
    else:
        im[:] = glow_circle(im, (int(W*.80), int(H*.15)), 54, (62, 72, 86), .42)
        cv2.circle(im, (int(W*.80), int(H*.15)), 28, (159, 162, 167), -1, cv2.LINE_AA)

    if family in {"castle", "threshold"}:
        cv2.rectangle(im, (0, 300), (W, H), (14, 14, 20), -1)
        for x in (70, 315, 560, 805): arch(im, x, 65, 120, 360, (30, 28, 38), 18)
        cv2.rectangle(im, (int(W*.40), 170), (int(W*.62), H), (4, 4, 8), -1)
        arch(im, int(W*.40), 105, int(W*.22), 435, (47, 37, 48), 15)
        # wet reflection streaks
        for _ in range(45):
            x=int(rng.uniform(0,W)); y=int(rng.uniform(365,H)); cv2.line(im,(x,y),(x+int(rng.uniform(-20,20)),y),(38,36,43),1)
        rain_lines(im, rng, 180)
    elif family in {"window", "vampire_window", "window_contact"}:
        cv2.rectangle(im, (0, 0), (W, H), (14, 11, 19), -1)
        for i,x in enumerate((80, 345, 610)):
            cv2.rectangle(im,(x,65),(x+190,430),(29,35,50),-1)
            arch(im,x,0,190,430,(58,49,60),12)
            cv2.line(im,(x+95,65),(x+95,430),(68,66,72),4)
        rain_lines(im, rng, 130)
        cv2.rectangle(im,(0,430),(W,H),(19,14,21),-1)
    elif family in {"corridor"}:
        vp=(W//2,180)
        cv2.rectangle(im,(0,390),(W,H),(15,13,18),-1)
        for x0 in range(0,W+1,120): cv2.line(im,(x0,H),vp,(46,39,48),3,cv2.LINE_AA)
        for y in (95,155,225,305):
            span=int((H-y)*1.22); arch(im,max(0,W//2-span//2),y-80,min(W,span),H-y,(42,36,46),8)
    elif family in {"cathedral", "sanctuary", "dawn_cathedral"}:
        for depth,(x,wid,th) in enumerate(((45,870,22),(150,660,16),(255,450,12),(350,260,8))):
            arch(im,x,20+depth*32,wid,470-depth*45,(46+depth*5,38+depth*4,48+depth*6),th)
        # rose window
        rc=(W//2,155); cv2.circle(im,rc,58,(64,48,65),5,cv2.LINE_AA)
        for a in np.linspace(0,math.tau,12,endpoint=False): cv2.line(im,rc,(rc[0]+int(math.cos(a)*55),rc[1]+int(math.sin(a)*55)),(73,53,73),2,cv2.LINE_AA)
        candles(im,rng,18,H-45); roses(im,rng,32,(405,530))
    elif family in {"memory_room", "rose_chamber", "velvet_chamber", "velvet_reverie", "rain_candle"}:
        cv2.rectangle(im,(0,330),(W,H),(17,11,19),-1)
        cv2.rectangle(im,(70,95),(360,350),(22,18,26),-1)
        for y in range(120,340,55): cv2.line(im,(80,y),(345,y),(48,39,45),3)
        cv2.rectangle(im,(610,90),(865,390),(23,27,38),-1); arch(im,610,25,255,365,(55,45,57),10)
        candles(im,rng,14,H-48); roses(im,rng,26,(360,525))
        if "rain" in family: rain_lines(im,rng,110)
    elif family in {"crypt", "crypt_roses"}:
        cv2.rectangle(im,(0,330),(W,H),(13,12,16),-1)
        for y in range(350,H,34):
            inset=int((y-350)*.5); cv2.line(im,(200-inset,y),(760+inset,y),(35,31,38),2)
        for x in (70,275,605,810): arch(im,x,70,90,330,(40,36,42),15)
        cv2.rectangle(im,(345,350),(615,410),(24,20,27),-1)
        if family=="crypt_roses": roses(im,rng,65,(330,525))
        candles(im,rng,8,H-35)
    elif family in {"portrait", "rain_portrait"}:
        cv2.rectangle(im,(0,0),(W,H),(13,9,17),-1)
        arch(im,90,20,780,500,(43,34,45),18)
        candles(im,rng,10,H-45)
        if family=="rain_portrait": rain_lines(im,rng,160)
    elif family in {"temporal", "candle_contact", "rain_contact"}:
        arch(im,85,25,790,500,(45,37,48),18)
        candles(im,rng,15,H-45)
        if family=="rain_contact": rain_lines(im,rng,150)

    # subject staging
    if family in {"portrait", "rain_portrait", "vampire_window"}:
        pandora(im, .52, 1.28, 1, echo=(family=="vampire_window"), eyes=True)
    elif family=="temporal":
        pandora(im,.50,1.02,1,echo=True); pandora(im,.30,.82,-1,echo=True); pandora(im,.72,.78,1,echo=True)
    elif family in {"candle_contact", "rain_contact", "window_contact"}:
        pandora(im,.42,.96,1,echo=False)
        # an unresolved opposite presence: deliberately translucent, not literal romance
        ghost=im.copy(); pandora(ghost,.70,.84,-1,echo=True,eyes=False)
        im=cv2.addWeighted(im,.82,ghost,.18,0)
    elif family in {"cathedral", "sanctuary", "dawn_cathedral"}:
        pandora(im,.52,.72,1,echo=False)
    elif family in {"crypt", "crypt_roses"}:
        pandora(im,.50,.91,1,echo=False)
    elif family=="corridor":
        pandora(im,.50,.82,1,echo=True)
    else:
        pandora(im,.55,.90,1,echo=False)

    # painterly treatment: restrained bloom, grain, vignette
    soft=cv2.GaussianBlur(im,(0,0),1.35)
    im=cv2.addWeighted(im,.83,soft,.17,0)
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    vig=np.clip(1-.34*(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2),.55,1)[...,None]
    im=np.clip(im.astype(np.float32)*vig,0,255)
    noise=rng.normal(0,2.2,(H,W,1)).astype(np.float32)
    im=np.clip(im+noise,0,255).astype(np.uint8)
    return im


manifest={"schema":"door-seconds.generated-scene-bank.v1","seed":SEED,"resolution":[W,H],"assets":[]}
for name,(family,variant) in SCENES.items():
    p=OUT/name
    frame=environment(family,variant)
    if not cv2.imwrite(str(p),frame,[cv2.IMWRITE_JPEG_QUALITY,94]):
        raise RuntimeError(f"failed to write {p}")
    manifest["assets"].append({"name":name,"family":family,"sha256":sha256(p),"bytes":p.stat().st_size,"status":"generated_production_source"})
    print(name, family, p.stat().st_size)

(OUT/"SCENE_BANK_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"assets":len(manifest["assets"]),"out":str(OUT)},indent=2))
