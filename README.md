# illustrator-agent

エージェントと一緒に、編集可能なAdobe Illustrator成果物を制作・改訂するための第2層・第3層リポジトリです。

低水準の`.ai`変換・編集・検証は兄弟リポジトリ`py-ai-illustrator`へ委譲します。このリポジトリは、デザインの意味と再生成規則を持つPython component、およびそれを安全に扱う`edit-illustrator` skillを所有します。

```text
依頼・素材
  -> edit-illustrator skill / workflow
  -> Python component / template / input data
  -> py-ai-illustrator IR・writer・validator
  -> editable .ai + diagnostics + preview
```

## 現在地

- `RenderedComponent` / `LayerBuilder`
- Table、point / area text、基本図形、group、Artboard
- rigid transformとtext rotation
- linked imageを含む実制作example
- `edit-illustrator` skillの初期workflow

第1層にない機能をskill内で推測実装しません。具体的な制作要求から不足が見つかった場合は、fixtureと検証条件を添えて`py-ai-illustrator`へ最小profileを追加します。

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

## Python example

```python
from illustrator_agent import Color, Document, LayerBuilder, TextBlock, TextStyle
from py_ai_illustrator.legacy import dump_ai7

builder = LayerBuilder(id="poster", name="Poster")
builder.add(TextBlock(
    id="title",
    text="Editable title",
    width=320,
    style=TextStyle(font_size=32, fill=Color(0.1, 0.2, 0.5)),
).render(x=40, top=240))

document = Document(width=400, height=300, layers=[builder.build()])
dump_ai7(document, "poster.ai")
```

より大きな制作例は`examples/`、設計境界は[architecture](docs/architecture.md)、今後の作業は[roadmap](docs/roadmap.md)を参照してください。

## Skill

Codex skillの本体は[skills/edit-illustrator/SKILL.md](skills/edit-illustrator/SKILL.md)です。新しいセッションでは、このskillと現在の制作要求を基準に第3層workflowを育てます。

## ライセンス

[MIT License](LICENSE)です。
