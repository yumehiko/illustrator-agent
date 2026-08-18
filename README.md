# illustrator-agent

編集可能なAdobe Illustrator成果物を、意味と再生成規則を持つPythonデザインオブジェクトから制作するリポジトリです。

現在は第2層（デザインモデル）の確立を優先します。Python componentと入力データから決定的にIRを生成し、兄弟リポジトリ`py-ai-illustrator`で`.ai`への変換・検証・preview・Illustrator実機確認を行います。第3層のagent workflow / skillは、第2層が安定してから整備します。

```text
Python component + input data
  -> graphic IR
  -> py-ai-illustrator
  -> editable .ai + diagnostics + preview
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

## ライセンス

[MIT License](LICENSE)です。
