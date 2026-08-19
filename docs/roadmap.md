# ロードマップ

更新日: 2026-08-19

## 現在地

M1 reference productionと新規制作のnative-first移行は完了しました。`quarterly_kpi_report`は明示的な`DocumentContext`とimmutableなnamed-role `DesignTheme`からdirect native compileします。

## M2: デザインモデルの拡張

次はreference productionに残るad-hocな入力validationを第2層の再利用可能な契約へ移します。その後、必要になった順にfont-aware layout / overflow、component identity、image fitting、複数artboard等を追加します。先回りした機能網羅は行いません。

## M3: 一般性の確認

日本語文字組み、データ駆動variant、image / area text / 複数artboardを代表する異なる制作物で同じ完成条件を通します。

## M4: 第3層

第2層のAPIと判断基準が安定した後、制作手順を`edit-illustrator` skillへまとめます。

## リポジトリ整理

- exampleの重複削減と生成物の保存方針
- CIで実行するIllustrator実機gateの運用決定
- 第3層skill骨格の凍結または縮小
