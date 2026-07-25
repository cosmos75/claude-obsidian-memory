#!/usr/bin/env python3
"""把生成好的機器區併進既有筆記，人類區原樣保留。

用法：merge_note.py <pipeline> <目標筆記路徑> <機器區內容檔>

機器區的內容由呼叫端（LLM）先寫進一個暫存檔，再交給這支腳本合併。
人類區的文字全程不經過 LLM 的手。see docs/adr/0001
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vault_notes import (  # noqa: E402
    HUMAN_BOUNDARY,
    boundary_offsets,
    is_pipeline_output,
    merge_note,
)


def main():
    if len(sys.argv) != 4:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    pipeline, target, body_path = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(body_path) as f:
        machine_region = f.read()

    existing = None
    if os.path.exists(target):
        with open(target) as f:
            existing = f.read()
        if not is_pipeline_output(existing, pipeline):
            print(
                f"拒絕寫入：{target} 沒有 {pipeline} 的來源標記，視為使用者自己的檔案。",
                file=sys.stderr,
            )
            return 1
        extra = len(boundary_offsets(existing)) - 1
        if extra > 0:
            print(f"注意：既有筆記有 {extra + 1} 個「{HUMAN_BOUNDARY}」分界，"
                  f"以最前面那個為準，其後全部保留。")

    merged = merge_note(existing, machine_region)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "w") as f:
        f.write(merged)

    if existing is None:
        print(f"已建立：{target}")
    elif merged == existing:
        print(f"內容無變化：{target}")
    else:
        kept = "保留了人類區" if boundary_offsets(existing) else "舊檔沒有人類區，整篇重寫"
        print(f"已更新（{kept}）：{target}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"合併失敗：{e}", file=sys.stderr)
        sys.exit(1)
