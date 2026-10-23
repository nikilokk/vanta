# core/blobs.py
"""
Генератор процедурных анимированных SVG-клякс (Animated Blobs).
Каждый пресет имеет выразительную геометрию и встроенную SMIL-анимацию морфинга.
"""
from pathlib import Path
from config import DATA_DIR

AVATARS_DIR = DATA_DIR / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

# Сильно различающиеся силуэты (парные пути A -> B для живого перетекания внутри SVG)
BLOB_SHAPES = {
    "plasma": (
        "M42,-72C55,-64,66,-54,75,-41C84,-28,91,-14,89,-1C87,12,76,24,67,37C58,50,51,64,39,73C27,82,13,86,-2,89C-17,92,-34,94,-47,86C-60,78,-69,60,-76,44C-83,28,-88,14,-87,0C-86,-14,-79,-28,-70,-41C-61,-54,-50,-66,-37,-74C-24,-82,-12,-86,1,-88C14,-90,29,-80,42,-72Z",
        "M51,-68C64,-56,71,-39,76,-21C81,-3,84,15,78,31C72,47,57,61,40,70C23,79,4,83,-15,82C-34,81,-53,75,-66,61C-79,47,-86,25,-85,4C-84,-17,-75,-37,-61,-51C-47,-65,-28,-73,-8,-75C12,-77,38,-80,51,-68Z",
    ),
    "liquid": (
        "M33,-65C46,-56,62,-53,73,-43C84,-33,90,-16,83,-3C76,10,56,19,47,34C38,49,40,70,31,79C22,88,2,85,-17,81C-36,77,-54,72,-62,59C-70,46,-68,25,-71,5C-74,-15,-82,-34,-76,-48C-70,-62,-50,-71,-33,-76C-16,-81,-2,-82,9,-77C20,-72,20,-74,33,-65Z",
        "M25,-58C38,-50,58,-52,69,-43C80,-34,82,-14,76,2C70,18,56,30,46,45C36,60,30,78,17,83C4,88,-16,80,-35,72C-54,64,-72,56,-79,41C-86,26,-82,4,-75,-15C-68,-34,-58,-50,-44,-59C-30,-68,-12,-70,-1,-68C10,-66,12,-66,25,-58Z",
    ),
    "crystal": (
        # Острый гранёный полигон (Кристалл)
        "M0,-88 L62,-62 L88,0 L62,62 L0,88 L-62,62 L-88,0 L-62,-62 Z",
        "M0,-92 L70,-50 L84,12 L50,74 L-12,86 L-72,52 L-86,-12 L-52,-72 Z",
    ),
    "droplet": (
        # Выраженная форма капли / кометы с острым верхом
        "M0,-92 C28,-55 68,-25 74,18 C80,58 44,88 0,88 C-44,88 -80,58 -74,18 C-68,-25 -28,-55 0,-92 Z",
        "M8,-90 C35,-50 74,-20 76,22 C78,62 40,86 -4,86 C-48,86 -78,54 -72,14 C-66,-26 -19,-50 8,-90 Z",
    ),
    "nucleus": (
        # Четырехлепестковая энергетическая звезда / атом
        "M0,-88 C22,-88 28,-38 52,-52 C76,-66 88,-22 88,0 C88,22 38,28 52,52 C66,76 22,88 0,88 C-22,88 -28,38 -52,52 C-76,66 -88,22 -88,0 C-88,-22 -38,-28 -52,-52 C-66,-76 -22,-88 0,-88 Z",
        "M0,-78 C30,-78 38,-48 62,-62 C86,-76 78,-30 78,0 C78,30 48,38 62,62 C76,86 30,78 0,78 C-30,78 -38,48 -62,62 C-86,76 -78,30 -78,0 C-78,-30 -48,-38 -62,-62 C-76,-86 -30,-78 0,-78 Z",
    ),
}

# Для обратной совместимости импортов в dashboard.py
BLOB_PATHS = BLOB_SHAPES

# Контрастные неоновые палитры
BLOB_PALETTES = {
    "cyber_indigo": ("#6366f1", "#a855f7", "#ec4899"),   # Фиолетово-розовый
    "neon_cyan":    ("#00f2fe", "#4facfe", "#0061ff"),   # Ярко-голубой лед
    "toxic_lime":   ("#00ff87", "#60efff", "#059669"),   # Кислотно-зеленый изумруд
    "solar_amber":  ("#ff8008", "#ffc837", "#ff0844"),   # Огненно-золотой
    "deep_void":    ("#f43f5e", "#7e22ce", "#09090b"),   # Багрово-черный космос
}


def generate_blob_svg(preset: str = "plasma", palette: str = "cyber_indigo", size: int = 64) -> str:
    """Генерирует анимированный SVG с перетеканием геометрии и уникальными градиентами."""
    colors = BLOB_PALETTES.get(palette, BLOB_PALETTES["cyber_indigo"])
    c1, c2, c3 = colors
    path_a, path_b = BLOB_SHAPES.get(preset, BLOB_SHAPES["plasma"])

    # Уникальные ID, чтобы браузер не путал градиенты разных карточек на одной странице
    uid = f"{preset}_{palette}_{size}"
    grad_id = f"g_{uid}"
    glow_id = f"f_{uid}"

    return f"""<svg viewBox="0 0 200 200" width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="{grad_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c1}" />
      <stop offset="55%" stop-color="{c2}" />
      <stop offset="100%" stop-color="{c3}" />
    </linearGradient>
    <filter id="{glow_id}" x="-25%" y="-25%" width="150%" height="150%">
      <feGaussianBlur stdDeviation="7" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <g transform="translate(100 100)" filter="url(#{glow_id})">
    <path d="{path_a}" fill="url(#{grad_id})">
      <animate attributeName="d" dur="6s" repeatCount="indefinite"
        values="{path_a}; {path_b}; {path_a}" />
    </path>
  </g>
  <circle cx="74" cy="66" r="11" fill="white" opacity="0.4" />
  <circle cx="62" cy="82" r="5" fill="white" opacity="0.2" />
</svg>"""


def get_agent_avatar_path(agent_id: str, preset: str, palette: str) -> str:
    """Сохраняет актуальный SVG-аватар агента на диск."""
    file_path = AVATARS_DIR / f"{agent_id}_{preset}_{palette}.svg"
    svg_content = generate_blob_svg(preset=preset, palette=palette, size=120)
    file_path.write_text(svg_content, encoding="utf-8")
    return str(file_path)