#!/usr/bin/env python3
"""一次性遷移：替既有的星標筆記補上來源標記。

用法：backfill_source_marker.py [--apply]     （不加 --apply 只演練，不寫檔）

ADR-0002 之前寫出來的星標筆記沒有來源標記，會被新規則判成使用者檔案而永遠
跳過，所以必須在新規則生效前補上。既有筆記無法用正式規則辨識，這裡**破例**
用「位於星標管道的地盤」加上「frontmatter 有 repo 欄位（索引檔則是 tags 含
moc）」這組啟發式認定。這是刻意的一次性例外，回填完就不該再有任何程式碼靠
位置判斷歸屬。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vault_notes import (  # noqa: E402
    PIPELINE_SOURCES,
    parse_frontmatter,
    resolve_subfolder,
)

CONFIG_PATH = os.path.expanduser("~/.claude/obsidian-memory/config.json")
PIPELINE = "githubStars"


def looks_like_star_note(fm):
    if "repo" in fm:
        return True
    return "moc" in fm.get("tags", "")


def add_source_line(content, source):
    head, _, rest = content.partition("\n---\n\n")
    return f"{head}\nsource: {source}\n---\n\n{rest}"


def main():
    apply_changes = "--apply" in sys.argv[1:]

    if not os.path.exists(CONFIG_PATH):
        print("尚未設定 vault，請先執行 /obsidian-memory-init。")
        return 1
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    vault_path = config.get("vaultPath")
    if not vault_path or not os.path.isdir(vault_path):
        print(f"設定的 vault 路徑無效：{vault_path!r}")
        return 1

    target_dir = os.path.join(vault_path, resolve_subfolder(config, PIPELINE))
    if not os.path.isdir(target_dir):
        print(f"星標資料夾不存在，沒有東西要回填：{target_dir}")
        return 0

    source = PIPELINE_SOURCES[PIPELINE]
    added, already, skipped = [], [], []

    for name in sorted(os.listdir(target_dir)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(target_dir, name)
        with open(path) as f:
            content = f.read()
        fm, _ = parse_frontmatter(content)
        if fm is None:
            skipped.append((name, "沒有 frontmatter"))
            continue
        if "source" in fm:
            already.append(name)
            continue
        if not looks_like_star_note(fm):
            skipped.append((name, "看起來不是星標筆記"))
            continue
        if apply_changes:
            with open(path, "w") as f:
                f.write(add_source_line(content, source))
        added.append(name)

    verb = "已補上" if apply_changes else "將補上"
    print(f"{verb}來源標記：{len(added)} 篇")
    print(f"已經有標記，跳過：{len(already)} 篇")
    if skipped:
        print(f"視為使用者檔案，不動：{len(skipped)} 篇")
        for name, why in skipped:
            print(f"  - {name}（{why}）")
    if not apply_changes and added:
        print("\n這是演練。確認無誤後加上 --apply 實際寫入。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"回填失敗：{e}", file=sys.stderr)
        sys.exit(1)
