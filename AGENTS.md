# Repository instructions

- 応答は日本語で行う。
- このリポジトリは第2層（デザインモデル）と第3層（エージェントworkflow / skill）を所有する。
- `.ai`のparser、writer、低水準IR、検証処理は`py-ai-illustrator`へ実装し、このリポジトリへ複製しない。
- 第1層の追加機能が必要な場合は、実ファイルfixture、必要operation、保持条件、検証条件を明示して`py-ai-illustrator`へ要求する。
- ドキュメント量はコンテキストを浪費しない最小限に保つ。既存文書と説明を重複させず、新規文書を作る前に既存の正本へ統合する。
- READMEは入口、`docs/design-model.md`は設計境界、`docs/roadmap.md`は未完了作業だけを扱う。APIの詳細はコード、example、testを正とする。
- pre-1.0では不要な互換wrapperを残さず、抽象の変更時はtest、example、必要最小限の文書を同時に更新する。
- design modelは`transforms.py`（affine）、`composition.py`（component/layer）、`typography.py`（text block）、`geometry.py`（primitive）、`text_layout.py`（計測/wrap）、`tables.py`（table）を独立責務として保つ。通常のPython sourceは500行前後または独立責務3つで分割を判断し、800行超は分割または理由付き例外、1,000行超は禁止する。
- 制約は製品要件、第1層IR/backendの現在の能力限界、安全性保証のいずれかへ紐付ける。能力限界を恒久的な製品制約として表現しない。
