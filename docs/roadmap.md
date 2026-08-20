# ロードマップ

更新日: 2026-08-20

## 現在地

M1 reference production、新規制作のnative-first移行、再利用可能な入力contractは完了しました。provenance付きfont-aware layout / fail-closed overflow APIと日本語scheduleのpure gateは実装済みです。

## M2: デザインモデルの拡張

次は必要になった順にcomponent identity、image fitting、複数artboard等を追加します。先回りした機能網羅は行いません。

## M3: 一般性の確認

日本語scheduleは、指定fontの利用可否、native compile/reopen、PDF preview、visual acceptanceのIllustrator実機gateが未完了です。完了後、データ駆動variant、image / area text / 複数artboardを代表する異なる制作物で同じ完成条件を通します。

## M4: 第3層

第2層のAPIと判断基準が安定した後、制作手順を`edit-illustrator` skillへまとめます。

## リポジトリ整理

- exampleの重複削減と生成物の保存方針
- CIで実行するIllustrator実機gateの運用決定
- 第3層skill骨格の凍結または縮小
