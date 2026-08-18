# アーキテクチャ

このリポジトリは第2層と第3層を所有します。

```text
第3層: edit-illustrator skill / agent workflow
  inspect brief and assets -> plan -> generate or patch -> verify -> report
                              |
                              v
第2層: design model
  component / template / layout / theme / semantic identity
                              |
                              v
外部依存: py-ai-illustrator
  low-level IR / .ai reader-writer / typed patch / validation / preview
```

依存方向は`illustrator-agent -> py-ai-illustrator`だけです。parser、writer、低水準IR、semantic / visual validationをskillへ複製しません。

## 編集経路

- 新規制作・量産: Python component、template、入力データをsource of truthにしてIRへ決定的にrenderする。
- 既存`.ai`の局所改訂: 元`.ai`をsource of truthにし、第1層のinspect / typed patch / validationを使う。
- Illustratorで手修正した生成物: graphic semanticsとdesign semanticsの保持を分けて報告する。

一般の`.ai`から「価格表」「CTA」等の高水準の意味を根拠なく復元しません。元Python source、stable ID、metadata、sidecar manifest等を対応根拠にします。

## 第1層への要求

不足機能はこのリポジトリの制作要求から発見します。第1層へ渡す要求には、対象`.ai` fixture、必要operation、未対応情報の保持条件、semantic / visual / native editabilityの合格条件を含めます。
