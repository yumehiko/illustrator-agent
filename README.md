# illustrator-agent

編集可能なAdobe Illustrator成果物を、意味と再生成規則を持つPythonデザインオブジェクトから制作するリポジトリです。

現在は第2層（デザインモデル）の確立を優先します。Python componentと入力データから決定的にIRを生成し、兄弟リポジトリ`py-ai-illustrator`のdirect native compilerでIllustrator 2026の編集可能な`.ai`へ変換します。第3層のagent workflow / skillは、第2層が安定してから整備します。

```text
Python component + input data
  -> graphic IR
  -> pure validation
  -> Illustrator 2026 direct native compile
  -> reopen semantics/editability + PDF preview
```

`.ai`のparser、writer、低水準IR、検証処理はこのリポジトリへ複製しません。第1層の不足は、具体的な制作fixtureと検証条件を添えて`py-ai-illustrator`へ要求します。

## セットアップ

```bash
uv sync --extra dev --locked
uv run --locked pytest
uv run --locked ruff check .
```

`[project.dependencies]`は公開package metadata上のversion要件、uv専用の`[tool.uv.sources]`は検証済み`py-ai-illustrator` commitの取得元、`uv.lock`はその解決済みcommitと推移依存を固定します。versionはpre-1.0中に同じ値を取り得るため、単独では互換性の正本にしません。現時点の`--no-sources`は未公開packageだけをversionから取得しようとするため、fresh checkoutの経路には使いません。production gateはインストール元、commit、versionを照合し、不明または不一致なら停止します。

第1層を同時開発するときだけ、同じ親ディレクトリの兄弟checkoutを固定commitへ合わせてからeditable installへ差し替えます。`uv run`の自動syncはlocked sourceへ戻すため、この間は`--no-sync`を付けます。checkoutに未commitの変更がある状態ではproduction gateは通りません。

```bash
git -C ../py-ai-illustrator checkout 322b97d2ababc2feb4dd64b6a453885596e74da6
uv pip install --python .venv/bin/python --editable ../py-ai-illustrator
uv run --no-sync pytest
```

検証commitを更新するときは、公開API互換性testを通したうえで`[tool.uv.sources]`の`rev`と`layer1_compatibility.py`の`LAYER1_COMMIT`を同時に更新し、`uv lock`を実行します。

設計と完成条件は[design model](docs/design-model.md)、未完了作業は[roadmap](docs/roadmap.md)を参照してください。

## Examples

`examples/`は次のproduction gateと最小recipeだけを保持します。production gateはnative AI、IR、PDF preview、検証reportを再生成し、direct compile後の意味と編集性まで検証します。

| 分類 | example | 固有の検証対象 |
| --- | --- | --- |
| production gate | `quarterly_kpi_report` | theme、再利用component、chart、point text |
| production gate | `japanese_schedule` | table、日本語font-aware計測、改行、overflow |
| production gate | `product_catalog` | linked image、area text、複数artboard |
| production gate | `campaign_variants` | JSON駆動variant、stable identity、artboard対応 |
| 最小recipe | `generate_product_swatch` | linked image用の決定的PNG fixture生成 |

```bash
uv run python -m examples.quarterly_kpi_report
uv run python -m examples.japanese_schedule
uv run python -m examples.product_catalog
uv run python -m examples.campaign_variants
```

日本語制作物はfont-aware measurement evidenceを明示入力として要求し、近似計測だけではoverflowを合格させません。`product_catalog`はcommit済みPNGを変更せずに読みます。fixtureを再生成して比較する最小recipeも出力先を`build/`に限定し、既存fileは上書きしません。

```bash
uv run python -m examples.generate_product_swatch
```

全exampleの既定出力は`build/`以下です。productionを同じ場所へ再生成する場合だけ`--force`を付けます。人間のpreview承認後は`--accept-visual-by "<name>"`を付けると検証reportへ記録できます。Illustrator不要のIR生成・determinism・契約検証は通常の`pytest`、実機gateは`RUN_ILLUSTRATOR_TESTS=1 uv run pytest tests/illustrator`で分離して実行します。

## ライセンス

[MIT License](LICENSE)です。
