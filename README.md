# skk-merged

基于 [SukkaLab/ruleset.skk.moe](https://github.com/SukkaLab/ruleset.skk.moe) 的规则集合并与 MRS 构建项目。

## 构建内容

- `data/domain/*.txt`：mihomo `domain` 行为的文本规则集。
- `data/ip/*.txt`：mihomo `ipcidr` 行为的文本规则集。
- `output/domain/*.mrs` 与 `output/ip/*.mrs`：由 mihomo 编译的 MRS 文件。
- `sources.json`：上游来源、分类合并关系和输出名称的唯一配置入口。

当前合并关系包括：`apple_cdn + apple_cn + apple_services → apple`、`microsoft_cdn + microsoft → microsoft`，以及同名规则的合并。所有 `non_ip` 来源都会归入 domain 输出。

## 本地构建

需要 Python 3.10+ 和 mihomo：

```bash
python scripts/build_rules.py
MIHOMO_BIN=/path/to/mihomo bash scripts/compile_mrs.sh
```

解析不了的规则会以 `WARNING unconvertible ...` 写入 Action 日志；构建仍会保留其余可转换规则。当前支持的 `non_ip` 类型是 `DOMAIN`、`DOMAIN-SUFFIX`、`DOMAIN-WILDCARD`，其中 `DOMAIN-KEYWORD` 等无法表达为 mihomo domain provider 的规则会被记录并跳过。

GitHub Actions 每天运行一次，也支持手动触发；上游下载、归一化、合并和 MRS 编译均在 Action 中完成。后续增加其他软件格式时，在 `scripts/` 增加新的编译适配器并复用 `data/` 即可。
