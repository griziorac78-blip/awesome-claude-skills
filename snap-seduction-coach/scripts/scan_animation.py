#!/usr/bin/env python3
"""Génère l'animation de scan de VEXA : une page HTML autonome (JPEG embarqué
en base64) avec démarrage holographique, balayage, glitch et verdict.

Usage :
  python3 scan_animation.py --interet 72 --humeur positif \
      --titre "Scan : Léa" --ligne "Elle relance avec une question" \
      --ligne "Emojis en miroir" --out scan.html

--humeur : positif | neutre | alerte  (choisit l'expression du personnage)
"""
import argparse
import base64
import html
import json
import os

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
EXPR = {"positif": ("wink", "#ff28aa"), "neutre": ("neutral", "#00f0ff"), "alerte": ("alert", "#faf03c")}

TEMPLATE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VEXA Scan</title>
<style>
:root{--neon:__COLOR__;--cyan:#00f0ff;--mag:#ff28aa;--yel:#faf03c;--bg:#0c0818}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);
 font-family:"Courier New",ui-monospace,monospace;color:#e8e6ff;overflow-x:hidden;padding:16px}
.card{position:relative;width:min(420px,100%);border:2px solid var(--neon);padding:14px;
 background:linear-gradient(160deg,#1a0f33,#0c0818);box-shadow:0 0 24px var(--neon),inset 0 0 18px #000;
 animation:boot .6s steps(6) both}
.card:before,.card:after{content:"";position:absolute;width:34px;height:34px;border:5px solid var(--yel)}
.card:before{top:-5px;left:-5px;border-right:0;border-bottom:0}
.card:after{bottom:-5px;right:-5px;border-left:0;border-top:0}
.head{display:flex;justify-content:space-between;font-size:12px;letter-spacing:2px;color:var(--neon)}
.blink{animation:blink 1s steps(2) infinite}
.holo{position:relative;margin:10px 0;aspect-ratio:1;overflow:hidden;border:1px solid #3a2a5a}
.holo img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
 animation:materialize 1.6s ease-out both, float 3s ease-in-out 1.6s infinite}
.holo img.r{mix-blend-mode:screen;filter:url(#r) ;opacity:.7;animation:glitch 2.2s steps(1) infinite}
.holo img.b{mix-blend-mode:screen;filter:hue-rotate(180deg);opacity:.5;animation:glitch 1.7s steps(1) .3s infinite reverse}
.scan{position:absolute;left:0;right:0;height:18%;top:-20%;
 background:linear-gradient(transparent,color-mix(in srgb,var(--neon) 55%,transparent),transparent);
 animation:sweep 1.8s linear 3}
.lines{position:absolute;inset:0;background:repeating-linear-gradient(transparent 0 2px,#0005 2px 3px);pointer-events:none}
.grid{position:absolute;inset:0;background:
 linear-gradient(var(--neon) 1px,transparent 1px) 0 0/32px 32px,
 linear-gradient(90deg,var(--neon) 1px,transparent 1px) 0 0/32px 32px;opacity:.08}
h1{font-size:18px;margin:6px 0;color:#fff;text-shadow:2px 0 var(--mag),-2px 0 var(--cyan)}
.typed{min-height:1.4em;color:var(--cyan);font-size:13px}
.gauge{height:14px;border:1px solid var(--neon);margin:10px 0 4px;position:relative;background:#000}
.gauge i{position:absolute;inset:0 auto 0 0;width:0;background:linear-gradient(90deg,var(--cyan),var(--mag));
 box-shadow:0 0 10px var(--mag);animation:fill 1.4s cubic-bezier(.2,.9,.3,1) 2.2s forwards}
.gl{display:flex;justify-content:space-between;font-size:11px;opacity:.8}
ul{list-style:none;padding:0;margin:10px 0 0;font-size:13px}
li{opacity:0;transform:translateX(-12px);animation:in .4s ease-out forwards;padding:3px 0}
li:before{content:"▸ ";color:var(--neon)}
@keyframes boot{0%{clip-path:inset(50% 0 50% 0);filter:brightness(3)}100%{clip-path:inset(0);filter:none}}
@keyframes materialize{0%{opacity:0;filter:blur(8px) brightness(3);transform:scaleY(.02)}
 40%{opacity:1;transform:scaleY(1.05)}100%{filter:none;transform:none}}
@keyframes float{50%{transform:translateY(-6px)}}
@keyframes glitch{0%,86%{transform:none;clip-path:none}88%{transform:translate(-6px,0);clip-path:inset(20% 0 60% 0)}
 92%{transform:translate(5px,0);clip-path:inset(55% 0 25% 0)}96%{transform:translate(-3px,0);clip-path:inset(8% 0 80% 0)}}
@keyframes sweep{to{top:110%}}
@keyframes fill{to{width:__PCT__%}}
@keyframes in{to{opacity:1;transform:none}}
@keyframes blink{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation-duration:.01s!important;animation-iteration-count:1!important}}
</style></head><body>
<svg width="0" height="0" style="position:absolute"><filter id="r"><feColorMatrix values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0"/></filter></svg>
<div class="card">
 <div class="head"><span>VEXA.OS // LOVE-SCAN</span><span class="blink">● LIVE</span></div>
 <div class="holo">
  <div class="grid"></div>
  <img src="data:image/jpeg;base64,__IMG__" alt="VEXA, coach holographique">
  <img class="r" src="data:image/jpeg;base64,__IMG__" alt="">
  <img class="b" src="data:image/jpeg;base64,__IMG__" alt="">
  <div class="scan"></div><div class="lines"></div>
 </div>
 <h1>__TITRE__</h1>
 <div class="typed" id="t"></div>
 <div class="gauge"><i></i></div>
 <div class="gl"><span>INTÉRÊT DÉTECTÉ</span><span id="pct">0%</span></div>
 <ul>__LIGNES__</ul>
</div>
<script>
const msgs=["> connexion au flux snap...","> lecture des messages...","> décodage des signaux...",__FINAL__];
const el=document.getElementById("t");let i=0;
(function next(){if(i>=msgs.length)return;let s=msgs[i++],k=0;
 const iv=setInterval(()=>{el.textContent=s.slice(0,++k);if(k>=s.length){clearInterval(iv);setTimeout(next,i<msgs.length?380:0)}},22)})();
const target=__PCT__,p=document.getElementById("pct");
setTimeout(()=>{const t0=performance.now();(function f(t){const v=Math.min(1,(t-t0)/1400);
 p.textContent=Math.round(target*(1-Math.pow(1-v,3)))+"%";if(v<1)requestAnimationFrame(f)})(t0)},2200);
document.querySelectorAll("li").forEach((li,n)=>li.style.animationDelay=(3.6+n*.25)+"s");
</script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--interet", type=int, default=50, help="score d'intérêt 0-100")
    ap.add_argument("--humeur", choices=EXPR, default="neutre")
    ap.add_argument("--titre", default="Scan terminé")
    ap.add_argument("--ligne", action="append", default=[], help="signal clé (répétable)")
    ap.add_argument("--out", default="vexa-scan.html")
    a = ap.parse_args()

    expr, color = EXPR[a.humeur]
    with open(os.path.join(ASSETS, f"vexa-{expr}.jpg"), "rb") as f:
        img = base64.b64encode(f.read()).decode()
    pct = max(0, min(100, a.interet))
    verdict = {"positif": "> verdict : feu vert ✓", "neutre": "> verdict : à creuser",
               "alerte": "> verdict : prudence ⚠"}[a.humeur]
    page = (TEMPLATE.replace("__COLOR__", color).replace("__IMG__", img).replace("__PCT__", str(pct))
            .replace("__TITRE__", html.escape(a.titre))
            .replace("__LIGNES__", "".join(f"<li>{html.escape(l)}</li>" for l in a.ligne))
            .replace("__FINAL__", json.dumps(verdict)))
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(page)
    print(os.path.abspath(a.out))


if __name__ == "__main__":
    main()
