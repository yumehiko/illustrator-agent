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

このリポジトリと`py-ai-illustrator`を同じ親ディレクトリに置きます。

```text
repository/
├── illustrator-agent/
└── py-ai-illustrator/
```

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

利用例は`examples/`、設計と完成条件は[design model](docs/design-model.md)、未完了作業は[roadmap](docs/roadmap.md)を参照してください。

## Reference production

`quarterly_kpi_report`を、明示的なJSON入力からnative AI、IR、PDF preview、検証reportまで再生成します。通常入口はIllustrator実機を必須とし、direct compileが保存・再open後の意味と編集性を検証します。

```bash
uv run python -m examples.quarterly_kpi_report
```

成果物は`build/m1/`へ出力します。同じ場所へ再生成する場合だけ`--force`を付けます。人間のpreview承認後は`--accept-visual-by "<name>"`を付けると検証reportへ記録できます。Illustrator不要のIR生成・determinism・契約検証は通常の`pytest`、実機gateは`RUN_ILLUSTRATOR_TESTS=1 uv run pytest tests/illustrator`で分離して実行します。

## ライセンス

[MIT License](LICENSE)です。
