---
description: 把我 GitHub star 的仓库拉下来，分析、分类，写入 Obsidian 库
argument-hint: [--vault <路径>] [--limit <N>|all] [--no-readme] [--refresh]
---

# 任务：GitHub Stars → Obsidian 知识库

把当前 GitHub 账号 star 过的仓库拉取、分析、按主题分类，写成 Obsidian 原生笔记。

## 参数（$ARGUMENTS）

用户可能传入以下参数，未传则用默认值：

- `--vault <路径>`：Obsidian 库根目录。**未传时，优先读取 `~/.claude/obsidian-memory/config.json` 的 `vaultPath`（与 `/obsidian-memory-init` 共用同一份设定）；该文件不存在或没有 `vaultPath` 才 fallback 到 `~/Obsidian`，并务必让用户确认真实路径。**
- `--limit <N>`：只处理前 N 个（按 star 时间倒序）。默认 `50`。设为 `all` 处理全部。
- `--no-readme`：跳过 README 抓取，只用 metadata 做粗分析（快、省 token）。**默认会抓 README 做深度分析。**
- `--refresh`：覆盖已存在的笔记。默认跳过已存在的，保护用户手改内容。

## 前置检查（先做，别跳过）

1. 运行 `gh auth status`，确认已登录。没登录就停下让用户先 `gh auth login`。
2. 解析 vault 路径：若传了 `--vault` 用该值；否则读取 `~/.claude/obsidian-memory/config.json` 的 `vaultPath`（该配置文件也可能不存在——如果不存在，提示用户可以先执行 `/obsidian-memory-init` 设定一次，或直接用 `--vault` 指定，再继续）；仍然没有就用默认值 `~/Obsidian`。
3. 确认 vault 路径存在（`ls <vault>`）。不存在就停下问用户。
4. 在 vault 下建目录：`<vault>/GitHub Stars/`。

## 步骤 1：拉取 star 列表

用 star 时间倒序拉取，附带 star 时间戳：

```bash
gh api user/starred --paginate \
  -H "Accept: application/vnd.github.star+json" \
  --jq '.[] | {starred_at, full_name: .repo.full_name, description: .repo.description, language: .repo.language, stars: .repo.stargazers_count, url: .repo.html_url, topics: .repo.topics, pushed_at: .repo.pushed_at}' \
  > "<vault>/GitHub Stars/.stars-raw.ndjson"
```

结果是 NDJSON（每行一个 JSON）。统计总数，若 `--limit` 未设为 `all`，只取前 N 行处理。

## 步骤 2：分类

读取上面的数据，逐仓库归入一个**主题分类**（不是简单按语言分）。根据 `topics`、`description`、`language` 综合判断。参考分类（可按实际情况增删）：

- 基础设施 / DevOps（k8s、Docker、CI、监控）
- 数据库 / 存储
- AI / LLM / Agent 工具
- 后端框架 / 库
- 前端 / UI
- CLI / 效率工具
- 网络 / 代理 / 安全
- 学习资料 / Awesome 清单
- 其它

每个仓库只归一个主类，但可在 tags 里加更细的标签。

## 步骤 3：为每个仓库写一篇笔记

路径 `<vault>/GitHub Stars/<owner>__<name>.md`（`/` 用 `__` 替代避免建子目录）。

**已存在且未传 `--refresh` 就跳过。**

除非传了 `--no-readme`，先抓完整 README（最多 ~12KB，足够覆盖安装/用法章节）：
```bash
gh api "repos/<full_name>/readme" --jq '.content' | base64 -d | head -c 12288
```

抓不到（部分仓库 README 不在默认位置）就退回用 description，并在笔记里标注「未获取到 README」。

**从 README 里重点提炼这几类信息**，写进笔记：
- **适用平台**：支持的操作系统（Linux / macOS / Windows）、架构（x86_64 / ARM64——我关注国产 ARM，务必留意）、运行时/语言版本要求、是否需要 GPU 等。
- **安装方式**：把 README 里给出的所有安装路径都列出来（包管理器 `apt`/`brew`/`pip`/`npm`/`cargo`/`go install`、Docker 镜像、预编译二进制、源码编译等），每种给出关键命令。
- **基本用法**：从 quickstart / usage 段落里抽一两条最小可用示例命令或配置片段。
- **依赖 / 前置条件**：需要先装什么、需要什么服务（如 Redis、Postgres）、需不需要 API key。

笔记模板（正文用中文，命令原样保留；README 原文别整段照抄，用自己的话概括）：

```markdown
---
repo: {full_name}
url: {url}
language: {language}
stars: {stars}
topics: [{topics}]
category: {分类}
platforms: [{Linux, macOS, Windows 等，据 README 判断}]
arch: [{x86_64, arm64 等，判断不出就留 unknown}]
install: [{docker, brew, pip 等命令行手段的简称列表}]
starred_at: {starred_at 的日期部分}
last_push: {pushed_at 的日期部分}
tags: [github-star, star/{分类slug}]
---

# {name}

> {description}

## 是什么
一到两句话说清这个项目解决什么问题、核心能力是什么。

## 为什么值得关注
结合我的技术栈（容器码头 / K8s / Redis / ARM 国产化 / 数据分析等），点出它对我可能的用处。没有明显关联就客观说它的典型使用场景。

## 适用平台与要求
- 操作系统：{Linux / macOS / Windows}
- 架构：{x86_64 / arm64，若 README 明确支持国产 ARM 或提供 arm64 二进制，在此标注}
- 运行时/依赖：{语言版本、外部服务、API key 等前置条件}

## 安装
把 README 里的安装方式分条列出，例如：

​```bash
# Docker
docker run ...

# 包管理器
brew install ... / pip install ... / go install ...
​```

## 基本用法
最小可用示例（命令或配置片段）：

​```bash
# 最简单跑起来的一条命令
​```

## 关键信息
- 主语言：{language} ｜ Stars：{stars}
- 最近更新：{last_push}（据此判断是否还活跃）
- 主题：{topics}

[在 GitHub 打开]({url})
```

安装/用法段落**只写 README 里确实给出的内容**，README 没提就写「README 未说明」，不要凭空编命令。

## 步骤 4：生成分类索引（MOC）

写 `<vault>/GitHub Stars/GitHub Stars.md`，按分类分组，每个仓库一行双链 + 一句话点评：

```markdown
---
tags: [moc, github-star]
updated: {今天日期}
---

# GitHub Stars 索引

共 {总数} 个，更新于 {日期}。

## 基础设施 / DevOps
- [[owner__name]] — 一句话点评
- ...

## 数据库 / 存储
- ...

（每个分类一节，空分类不列）
```

## 收尾

- 删除临时文件 `.stars-raw.ndjson`。
- 给用户一句话总结：处理了多少个、跳过多少个、分了几类、索引在哪。
- 如果因 `--limit` 只处理了一部分，提醒用户可以传 `--limit all` 或调大数字继续。
- README 深度分析每个仓库都要抓一次、分析一次，比较费时费 token。若数量大、只想要粗略清单，传 `--no-readme` 会快很多。

## 硬性规则

- 绝不覆盖用户手改过的笔记（除非 `--refresh`）。
- 一次别改太多文件就静默跑完——每处理完一个分类停一下报告进度。
- README/描述里的原文别整段照抄，用自己的话概括。
