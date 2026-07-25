"""管道產物的純邏輯：合併、設定解析、來源判斷。

這個模組不碰檔案系統、不呼叫外部程式，輸入字串輸出字串或布林，
是整個 repo 唯一的測試接縫。see docs/adr/0001, docs/adr/0002
"""
import re

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n\n", re.DOTALL)

PIPELINE_DEFAULTS = {
    "conversations": "Claude Code",
    "githubStars": "GitHub Stars",
}

PIPELINE_SOURCES = {
    "conversations": "claude-code",
    "githubStars": "github-stars",
}

LEGACY_SUBFOLDER_KEYS = {
    "conversations": "archiveSubfolder",
}

# 這個字串必須與 commands/stars-to-obsidian.md 筆記模板裡的分界標題逐字相符，
# 對不上人類區就永遠不會被保留。tests 有一條一致性測試守著。
HUMAN_BOUNDARY = "## 我的笔记"


def parse_frontmatter(content):
    m = FRONTMATTER_RE.match(content)
    if not m:
        return None, content
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, content[m.end():]


def boundary_offsets(content, boundary=HUMAN_BOUNDARY):
    """分界所在行的位移，只認整行相符的情況。

    行首以外的位置、或後面還接著其他字的標題（`## 我的筆記補充`）都不算，
    因此人類區裡的二階標題與程式碼區塊不會被誤判成分界。
    """
    target = boundary.strip()
    offsets = []
    pos = 0
    for line in content.splitlines(keepends=True):
        if line.strip() == target:
            offsets.append(pos)
        pos += len(line)
    return offsets


def split_human_region(content, boundary=HUMAN_BOUNDARY):
    """切成 (分界之前, 分界起至結尾)。沒有分界時後者為 None。

    有多個分界時取最前面那個——其後的一切原樣落在人類區裡，不會遺失。
    """
    offsets = boundary_offsets(content, boundary)
    if not offsets:
        return content, None
    return content[:offsets[0]], content[offsets[0]:]


def merge_note(existing, machine_region, boundary=HUMAN_BOUNDARY):
    """把新生成的機器區併回舊筆記，人類區原樣保留。

    machine_region 本身結尾就帶著模板附的空白人類區，所以舊檔有人類區時
    要用舊的換掉模板那份，而不是接在後面（否則會出現兩個分界）。
    """
    if existing is None:
        return machine_region
    _, human = split_human_region(existing, boundary)
    if human is None:
        return machine_region
    machine_head, _ = split_human_region(machine_region, boundary)
    return machine_head + human


def resolve_subfolder(config, pipeline):
    """管道在 vault 下的子資料夾：新結構 > 舊結構 > 預設值。"""
    if pipeline not in PIPELINE_DEFAULTS:
        raise KeyError(f"未知的管道：{pipeline!r}")
    entry = (config.get("pipelines") or {}).get(pipeline) or {}
    subfolder = entry.get("subfolder")
    if subfolder:
        return subfolder
    legacy_key = LEGACY_SUBFOLDER_KEYS.get(pipeline)
    if legacy_key and config.get(legacy_key):
        return config[legacy_key]
    return PIPELINE_DEFAULTS[pipeline]


def is_pipeline_output(content, pipeline):
    """檔案是否為該管道的產物。沒有來源標記的一律是使用者的東西。"""
    if pipeline not in PIPELINE_SOURCES:
        raise KeyError(f"未知的管道：{pipeline!r}")
    fm, _ = parse_frontmatter(content)
    if not fm:
        return False
    return fm.get("source") == PIPELINE_SOURCES[pipeline]
