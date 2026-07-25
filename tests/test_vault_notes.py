import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from vault_notes import (  # noqa: E402
    HUMAN_BOUNDARY,
    archived_turns_for_session,
    is_pipeline_output,
    merge_note,
    project_name,
    resolve_subfolder,
    split_human_region,
)

# 機器區結尾固定帶著模板附的空白人類區，合併時要被舊檔的人類區換掉。
MACHINE = (
    "---\nrepo: foo/bar\nstars: 100\nsource: github-stars\n---\n\n"
    "# bar\n\n## 是什麼\n\n一個工具。\n\n"
    f"{HUMAN_BOUNDARY}\n\n（在這行以下寫的東西不會被覆寫）\n"
)
MACHINE_HEAD = MACHINE.split(HUMAN_BOUNDARY)[0]


def with_human(body):
    return MACHINE_HEAD + HUMAN_BOUNDARY + "\n\n" + body


class MergeNote(unittest.TestCase):
    def test_no_existing_file_writes_machine_region_as_is(self):
        self.assertEqual(merge_note(None, MACHINE), MACHINE)

    def test_existing_without_human_region_is_fully_rewritten(self):
        stale = "---\nstars: 1\n---\n\n# bar\n\n## 是什麼\n\n舊的描述。\n"
        self.assertEqual(merge_note(stale, MACHINE), MACHINE)

    def test_human_region_survives_and_machine_region_updates(self):
        existing = with_human("試用過，arm64 下要自己編譯。\n")
        merged = merge_note(existing, MACHINE)
        self.assertIn("試用過，arm64 下要自己編譯。", merged)
        self.assertIn("stars: 100", merged)
        self.assertNotIn("（在這行以下寫的東西不會被覆寫）", merged)

    def test_merge_produces_exactly_one_boundary(self):
        merged = merge_note(with_human("心得。\n"), MACHINE)
        self.assertEqual(merged.count(HUMAN_BOUNDARY), 1)

    def test_h2_heading_inside_human_region_is_not_treated_as_boundary(self):
        existing = with_human("## 我的評估\n\n值得用。\n\n## 待辦\n\n測 arm64。\n")
        merged = merge_note(existing, MACHINE)
        self.assertIn("## 我的評估", merged)
        self.assertIn("## 待辦", merged)
        self.assertIn("測 arm64。", merged)

    def test_boundary_string_inside_fenced_block_is_preserved(self):
        existing = with_human(f"範例：\n\n```md\n{HUMAN_BOUNDARY}\n```\n\n就這樣。\n")
        merged = merge_note(existing, MACHINE)
        self.assertIn("```md", merged)
        self.assertIn("就這樣。", merged)

    def test_boundary_mid_line_is_not_a_boundary(self):
        stale = MACHINE_HEAD + f"提到 {HUMAN_BOUNDARY} 這個標題但不是分界。\n"
        self.assertEqual(merge_note(stale, MACHINE), MACHINE)

    def test_heading_with_trailing_words_is_not_a_boundary(self):
        stale = MACHINE_HEAD + f"{HUMAN_BOUNDARY}補充\n\n這不算分界。\n"
        self.assertEqual(merge_note(stale, MACHINE), MACHINE)

    def test_empty_human_region_is_preserved_as_empty(self):
        existing = MACHINE_HEAD + HUMAN_BOUNDARY + "\n"
        merged = merge_note(existing, MACHINE)
        self.assertTrue(merged.endswith(HUMAN_BOUNDARY + "\n"))
        self.assertNotIn("（在這行以下寫的東西不會被覆寫）", merged)

    def test_multiple_boundaries_keep_everything_after_the_first(self):
        existing = with_human(f"第一段。\n\n{HUMAN_BOUNDARY}\n\n第二段。\n")
        merged = merge_note(existing, MACHINE)
        self.assertIn("第一段。", merged)
        self.assertIn("第二段。", merged)

    def test_split_reports_no_human_region_when_absent(self):
        head, human = split_human_region("# bar\n\n沒有分界。\n")
        self.assertIsNone(human)
        self.assertEqual(head, "# bar\n\n沒有分界。\n")


class BoundaryMatchesCommandTemplate(unittest.TestCase):
    """分界字串是跨檔案的約定：程式碼認的字串與指令模板產生的字串必須逐字相同。

    對不上的話所有單元測試仍會全綠（它們都引用同一個常數），但實際跑起來
    人類區永遠不會被保留——正是 ADR-0001 要防的那種靜默資料遺失。
    """

    def test_command_template_uses_the_same_boundary_string(self):
        path = os.path.join(
            os.path.dirname(__file__), "..", "commands", "stars-to-obsidian.md"
        )
        with open(path, encoding="utf-8") as f:
            command = f.read()
        self.assertIn(
            "\n" + HUMAN_BOUNDARY + "\n",
            command,
            f"指令模板裡找不到分界標題 {HUMAN_BOUNDARY!r}——"
            "兩邊對不上時人類區會被靜默覆寫。",
        )


class ResolveSubfolder(unittest.TestCase):
    def test_new_schema_only(self):
        config = {"pipelines": {"githubStars": {"subfolder": "我的收藏"}}}
        self.assertEqual(resolve_subfolder(config, "githubStars"), "我的收藏")

    def test_legacy_schema_with_default_value(self):
        self.assertEqual(
            resolve_subfolder({"archiveSubfolder": "Claude Code"}, "conversations"),
            "Claude Code",
        )

    def test_legacy_schema_with_customised_value_is_honoured(self):
        # 最容易靜默給錯答案的情況：舊設定自訂過，升級後不可悄悄改寫到預設資料夾。
        self.assertEqual(
            resolve_subfolder({"archiveSubfolder": "對話紀錄"}, "conversations"),
            "對話紀錄",
        )

    def test_new_schema_wins_over_legacy(self):
        config = {
            "archiveSubfolder": "舊資料夾",
            "pipelines": {"conversations": {"subfolder": "新資料夾"}},
        }
        self.assertEqual(resolve_subfolder(config, "conversations"), "新資料夾")

    def test_legacy_key_does_not_leak_into_other_pipelines(self):
        config = {"archiveSubfolder": "對話紀錄"}
        self.assertEqual(resolve_subfolder(config, "githubStars"), "GitHub Stars")

    def test_empty_config_falls_back_to_defaults(self):
        self.assertEqual(resolve_subfolder({}, "conversations"), "Claude Code")
        self.assertEqual(resolve_subfolder({}, "githubStars"), "GitHub Stars")

    def test_pipeline_absent_from_config_falls_back_to_default(self):
        config = {"pipelines": {"conversations": {"subfolder": "對話紀錄"}}}
        self.assertEqual(resolve_subfolder(config, "githubStars"), "GitHub Stars")

    def test_unknown_pipeline_raises(self):
        with self.assertRaises(KeyError):
            resolve_subfolder({}, "bookmarks")


class ProjectName(unittest.TestCase):
    def test_repo_root_wins_over_cwd(self):
        # worktree 的 cwd 在 repo 底下很深的地方，專案名仍該是 repo 的名字
        self.assertEqual(
            project_name("/home/me/proj/.claude/worktrees/feat-x", "/home/me/proj"),
            "proj",
        )

    def test_subdirectory_maps_to_the_same_project(self):
        self.assertEqual(project_name("/home/me/proj/src/deep", "/home/me/proj"), "proj")

    def test_falls_back_to_cwd_outside_a_repo(self):
        self.assertEqual(project_name("/home/me/notes"), "notes")

    def test_trailing_slash_is_ignored(self):
        self.assertEqual(project_name("/home/me/proj/", None), "proj")

    def test_filesystem_root_has_a_name(self):
        self.assertEqual(project_name("/"), "root")


class ArchivedTurnsForSession(unittest.TestCase):
    SESSION = "8b1fbf5c-36fc-4330-9e41-66c03b31d12b"

    def archive(self, session_id, turns, source="claude-code"):
        return (
            f"---\nsource: {source}\nsession_id: {session_id}\n"
            f"archived_turns: {turns}\n---\n\n# Session\n"
        )

    def test_matching_session_returns_turn_count(self):
        content = self.archive(self.SESSION, 142)
        self.assertEqual(archived_turns_for_session(content, self.SESSION), 142)

    def test_other_session_returns_none(self):
        content = self.archive("some-other-session", 10)
        self.assertIsNone(archived_turns_for_session(content, self.SESSION))

    def test_user_file_returns_none_even_with_matching_session_id(self):
        # 沒有來源標記就是使用者的檔案，不該被當成封存接續下去（ADR-0002）
        content = f"---\nsession_id: {self.SESSION}\narchived_turns: 99\n---\n\n# 我的筆記\n"
        self.assertIsNone(archived_turns_for_session(content, self.SESSION))

    def test_other_pipelines_output_returns_none(self):
        content = self.archive(self.SESSION, 5, source="github-stars")
        self.assertIsNone(archived_turns_for_session(content, self.SESSION))

    def test_missing_turn_count_reads_as_zero(self):
        content = f"---\nsource: claude-code\nsession_id: {self.SESSION}\n---\n\n# S\n"
        self.assertEqual(archived_turns_for_session(content, self.SESSION), 0)

    def test_non_numeric_turn_count_returns_none(self):
        content = self.archive(self.SESSION, "壞掉的值")
        self.assertIsNone(archived_turns_for_session(content, self.SESSION))


class IsPipelineOutput(unittest.TestCase):
    def test_own_marker_matches(self):
        self.assertTrue(is_pipeline_output(MACHINE, "githubStars"))

    def test_other_pipelines_marker_does_not_match(self):
        self.assertFalse(is_pipeline_output(MACHINE, "conversations"))

    def test_frontmatter_without_source_is_a_user_file(self):
        content = "---\nrepo: foo/bar\ntags: [github-star]\n---\n\n# bar\n"
        self.assertFalse(is_pipeline_output(content, "githubStars"))

    def test_no_frontmatter_is_a_user_file(self):
        self.assertFalse(is_pipeline_output("# 我自己寫的筆記\n\n內容。\n", "githubStars"))

    def test_malformed_frontmatter_is_a_user_file(self):
        self.assertFalse(is_pipeline_output("---\nsource: github-stars\n# 沒收尾\n", "githubStars"))

    def test_unknown_pipeline_raises(self):
        with self.assertRaises(KeyError):
            is_pipeline_output(MACHINE, "bookmarks")


if __name__ == "__main__":
    unittest.main()
