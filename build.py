#!/usr/bin/env python3
"""Build the DenoHearth addon site (GitHub Pages, plain HTML).

    py -3 build.py

Everything on the pages comes from the addons themselves: version and one-line description
from each .toc, the feature list from the "What it does" part of each repo README, the
pictures from the gallery folder. Change an addon, run this again, commit, push.
"""
import html, re, shutil
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
SRC = Path(r"C:\Dev\wow-forever-addons")
REPOS = Path(r"C:\Dev\wow-addons")
GALLERY = SRC / "_release" / "gallery"
GITHUB = "https://github.com/DenoHearth"

# slug, addon folder, display name, short pitch, logo, CurseForge project id, toc folder, how to get it
ADDONS = [
    dict(slug="deno-map", folder="DenoMap", name="Deno Map 4K", kind="Map & minimap",
         pitch="Every world map and the minimap in four times the resolution.",
         logo=SRC / "_release" / "DenoMap-logo.jpg", curse=None, toc=SRC / "DenoMap" / "DenoMap.toc",
         readme=REPOS / "DenoMap" / "README.md", banner=REPOS / "DenoMap" / "docs" / "banner.jpg",
         pictures=["DenoMap-2-", "DenoMap-5-", "DenoMap-1-", "DenoMap-4-", "DenoMap-11-", "DenoMap-10-", "DenoMap-14-", "DenoMap-13-"],
         download="zip", size="about 6.4 GB"),
    dict(slug="button-drawer", folder="ButtonDrawer", name="Button Drawer", kind="Minimap",
         pitch="One minimap button that holds all the others, with a Lua error button built in.",
         logo=SRC / "_release" / "ButtonDrawer-logo.png", curse=1728651, toc=SRC / "ButtonDrawer" / "ButtonDrawer.toc",
         readme=REPOS / "ButtonDrawer" / "README.md", pictures=["ButtonDrawer-"], download="release"),
    dict(slug="deno-dots", folder="DenoDots", name="Deno Dots", kind="Combat",
         pitch="Your damage-over-time effects and buffs as small icons with timers, and a red mark on what is missing.",
         logo=SRC / "_release" / "DenoDots-logo.png", curse=None,   # project 1732241 is still under review on CurseForge; put the id back when approved
          toc=SRC / "DenoDots" / "DenoDots.toc",
         readme=REPOS / "DenoDots" / "README.md", pictures=["DenoDots-1", "DenoDots-2", "DenoDots-3", "DenoDots-4-glow-small", "DenoDots-5"], download="release"),
    dict(slug="deno-nameplate", folder="DenoNameplate", name="Deno Nameplate", kind="Nameplates",
         pitch="Clean, compact nameplates with health text, cast bars and quest icons.",
         logo=SRC / "_release" / "DenoNameplate-logo.png", curse=1728681, toc=SRC / "DenoNameplate" / "DenoNameplate.toc",
         readme=REPOS / "DenoNameplate" / "README.md", pictures=["DenoNameplate-"], download="release"),
    dict(slug="raid-recruiter", folder="RaidRecruiter", name="Raid Recruiter", kind="Groups & raids",
         pitch="One window for building and running a raid: LFG feed, recruiting, roles, loot rolls.",
         logo=SRC / "_release" / "RaidRecruiter-logo.png", curse=None,   # project 1733417 is still under review on CurseForge; put the id back when approved
          toc=SRC / "RaidRecruiter" / "RaidRecruiter.toc",
         readme=REPOS / "RaidRecruiter" / "README.md", pictures=["RaidRecruiter-"], download="release"),
]

e = html.escape


def toc(path):
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"## (\w+): (.*)", line)
        if m:
            out[m.group(1).lower()] = m.group(2).strip()
    return out


def inline(text):
    """README inline marks to HTML: `code`, **bold**."""
    text = e(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)


def features(readme):
    """(intro, [(title, text)]) from the README's 'What it does' part: list or table."""
    text = readme.read_text(encoding="utf-8")
    m = re.search(r"## What (?:it does|you get)\n(.*?)(?=\n## )", text, re.S)
    if not m:
        return "", []
    body = m.group(1)
    items = []
    for row in re.findall(r"^\| \*\*(.+?)\*\* \| (.+?) \|$", body, re.M):          # table rows
        items.append((row[0], row[1]))
    if not items:
        joined = re.sub(r"\n  +", " ", body)                                        # wrapped bullets
        for line in joined.splitlines():
            b = re.match(r"- \*\*(.+?)[:.]?\*\*:? ?(.*)", line)
            if b:
                items.append((b.group(1).rstrip(":."), b.group(2)))
    intro = ""
    first = body.strip().split("\n\n")[0]
    if not first.startswith(("-", "|")):
        intro = " ".join(first.split())
    return intro, items


def picture(src, name):
    """Copy a gallery picture into img/ at web size. Returns (file, width, height)."""
    out = HERE / "img"
    out.mkdir(exist_ok=True)
    if src.suffix.lower() == ".gif":
        shutil.copy2(src, out / name)
        with Image.open(src) as im:
            return name, im.width, im.height
    with Image.open(src) as im:
        im = im.convert("RGB")
        if im.width > 1800:
            im = im.resize((1800, round(im.height * 1800 / im.width)), Image.LANCZOS)
        target = Path(name).with_suffix(".jpg").name
        im.save(out / target, quality=88)
        return target, im.width, im.height


def caption(filename):
    """'DenoDots-3-editor.png' -> 'Editor'; before/after pictures name their zone."""
    stem = Path(filename).stem
    stem = re.sub(r"^[A-Za-z]+-\d+-", "", stem)
    stem = stem.replace("-before-after", "").replace("-small", "").replace("-", " ")
    stem = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", stem)
    return stem[:1].upper() + stem[1:]


def page(title, description, body, depth=0):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="https://denohearth.github.io/img/banner.jpg">
<meta name="keywords" content="World of Warcraft Forever addons, WoW Forever addon, Classic Plus addons, 4K world map, HD minimap, nameplates, raid recruiting, DoT tracker, minimap button">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/site.css">
<link rel="icon" href="{up}img/favicon.png">
</head>
<body>
<header class="top">
  <a class="brand" href="{up}index.html">Deno<span>Hearth</span></a>
  <nav>
    <a href="{up}index.html#addons">Addons</a>
    <a href="{GITHUB}">GitHub</a>
  </nav>
</header>
{body}
<footer>
  <p>Addons for World of Warcraft: Forever, made by Deniz. Free, open source, MIT licence for the code.</p>
  <p class="small">World of Warcraft and its art belong to Blizzard Entertainment. This site is not affiliated with Blizzard.</p>
</footer>
</body>
</html>
"""


def build():
    (HERE / "addons").mkdir(exist_ok=True)
    (HERE / "img").mkdir(exist_ok=True)
    banner = REPOS / "DenoMap" / "docs" / "banner.jpg"
    cards = []
    for a in ADDONS:
        meta = toc(a["toc"])
        a["version"] = meta.get("version", "")
        a["notes"] = meta.get("notes", a["pitch"])
        with Image.open(a["logo"]) as im:
            im.convert("RGB").resize((256, 256), Image.LANCZOS).save(HERE / "img" / f"{a['slug']}-logo.jpg", quality=90)
        shots = []
        for prefix in a["pictures"]:
            for src in sorted(GALLERY.glob(prefix + "*")):
                if "glow.gif" in src.name and "small" not in src.name:
                    continue                                   # the small one is the web copy
                shots.append((picture(src, src.name), caption(src.name)))
        a["shots"] = shots
        intro, items = features(a["readme"])
        repo = f"{GITHUB}/{a['folder']}"
        buttons = []
        if a["download"] == "release":
            buttons.append(f'<a class="btn primary" href="{repo}/releases/latest">Download v{e(a["version"])}</a>')
        else:
            buttons.append(f'<a class="btn primary" href="{repo}/archive/refs/heads/main.zip">Download v{e(a["version"])} ({a["size"]})</a>')
        if a["curse"]:
            buttons.append(f'<a class="btn" href="https://www.curseforge.com/projects/{a["curse"]}">CurseForge</a>')
        buttons.append(f'<a class="btn" href="{repo}">Source on GitHub</a>')

        hero_img = ""
        if a.get("banner"):
            shutil.copy2(a["banner"], HERE / "img" / "banner.jpg")
            hero_img = '<img class="wide" src="../img/banner.jpg" alt="">'
        feats = "".join(f"<li><h3>{inline(t)}</h3><p>{inline(x[:1].upper() + x[1:])}</p></li>" for t, x in items)
        gallery = "".join(
            f'<a class="shot" href="../img/{f}"><img loading="lazy" src="../img/{f}" width="{w}" height="{h}" alt="{e(a["name"])}: {e(c)}"><span>{e(c)}</span></a>'
            for (f, w, h), c in shots)
        if a["download"] == "release":
            steps = (f'<li>Download the zip from the <a href="{repo}/releases/latest">latest release</a>, or install it from CurseForge.</li>'
                     f'<li>Extract the <code>{a["folder"]}</code> folder into <code>World of Warcraft\\&lt;Forever folder&gt;\\Interface\\AddOns\\</code>.</li>'
                     '<li>Restart the game.</li>')
        else:
            steps = (f'<li>Download the <a href="{repo}/archive/refs/heads/main.zip">whole addon as a zip</a> ({a["size"]}).</li>'
                     f'<li>Open it. Inside the top folder is a folder named <code>{a["folder"]}</code>.</li>'
                     f'<li>Move that folder into <code>World of Warcraft\\&lt;Forever folder&gt;\\Interface\\AddOns\\</code> and restart the game.</li>')
        body = f"""
<main class="addon">
  {hero_img}
  <section class="head">
    <img class="logo" src="../img/{a['slug']}-logo.jpg" alt="" width="128" height="128">
    <div>
      <p class="kind">{e(a['kind'])} · WoW: Forever</p>
      <h1>{e(a['name'])}</h1>
      <p class="lead">{inline(a['notes'])}</p>
      <div class="buttons">{''.join(buttons)}</div>
    </div>
  </section>
  {f'<p class="intro">{inline(intro)}</p>' if intro else ''}
  <section>
    <h2>What it does</h2>
    <ul class="features">{feats}</ul>
  </section>
  <section>
    <h2>Pictures</h2>
    <div class="gallery">{gallery}</div>
  </section>
  <section>
    <h2>Install</h2>
    <ol class="steps">{steps}</ol>
  </section>
</main>
"""
        (HERE / "addons" / f"{a['slug']}.html").write_text(
            page(f"{a['name']} - addon for WoW: Forever", a["notes"], body, depth=1), encoding="utf-8", newline="\n")
        first = shots[0][0][0] if shots else f"{a['slug']}-logo.jpg"
        cards.append(f"""
    <a class="card" href="addons/{a['slug']}.html">
      <div class="thumb"><img loading="lazy" src="img/{first}" alt=""></div>
      <div class="meta">
        <img class="logo" src="img/{a['slug']}-logo.jpg" alt="" width="56" height="56">
        <div><h3>{e(a['name'])}</h3><p class="kind">{e(a['kind'])} · v{e(a['version'])}</p></div>
      </div>
      <p>{e(a['pitch'])}</p>
    </a>""")

    with Image.open(ADDONS[0]["logo"]) as im:
        im.convert("RGB").resize((64, 64), Image.LANCZOS).save(HERE / "img" / "favicon.png")
    shutil.copy2(banner, HERE / "img" / "banner.jpg")
    # the front page's backdrop: a whole 4K map, no lettering of ours on it
    with Image.open(GALLERY / "DenoMap-9-ZephrasIsle-whole-map.jpg") as im:
        im.convert("RGB").resize((1920, 1280), Image.LANCZOS).save(HERE / "img" / "hero.jpg", quality=85)
    index = f"""
<section class="hero">
  <div class="inner">
    <p class="kind">Addons for World of Warcraft: Forever</p>
    <h1>Deno<span>Hearth</span></h1>
    <p class="lead">Five addons written from scratch for Forever and its addon rules. Free, open source, no libraries to install.</p>
    <div class="buttons"><a class="btn primary" href="#addons">See the addons</a><a class="btn" href="{GITHUB}">GitHub</a></div>
  </div>
</section>
<main>
  <section id="addons">
    <h2>The addons</h2>
    <div class="cards">{''.join(cards)}
    </div>
  </section>
  <section class="about">
    <h2>How they are made</h2>
    <ul class="features">
      <li><h3>For Forever, not ported</h3><p>Forever hides combat data from addons. Each addon here is built around what the game allows, with the game's own display tools.</p></li>
      <li><h3>Buttons you can see</h3><p>The things you do often are visible buttons with a tooltip, not hidden clicks to remember.</p></li>
      <li><h3>Standalone</h3><p>No libraries to install and no addon depends on another.</p></li>
      <li><h3>Open</h3><p>All code is on GitHub under the MIT licence, with the scripts that build the textures.</p></li>
    </ul>
  </section>
</main>
"""
    (HERE / "index.html").write_text(
        page("DenoHearth - addons for World of Warcraft: Forever",
             "Five free addons for World of Warcraft: Forever: 4K world map and minimap, minimap button drawer, DoT tracker, nameplates and a raid recruiter.",
             index), encoding="utf-8", newline="\n")
    (HERE / ".nojekyll").write_text("", encoding="utf-8")
    print("built", len(ADDONS), "addon pages,", sum(len(a["shots"]) for a in ADDONS), "pictures")


if __name__ == "__main__":
    build()
