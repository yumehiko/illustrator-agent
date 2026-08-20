# ロードマップ

更新日: 2026-08-20

## 現在地

M1 reference production、新規制作のnative-first移行、再利用可能な入力contractに加え、provenance付きfont-aware layout / fail-closed overflow APIが完了しました。日本語scheduleと`product_catalog`は、指定font、native compile/reopen、semantic preservation、PDF preview、visual acceptanceまでIllustrator 30.7実機gateを通過しています。`product_catalog`ではlinked image、editable area text、2 artboardと、保存・再open後の非overflow、2ページpreviewを確認済みです。

## M2: デザインモデルの拡張

必要になった順にcomponent identity等を追加します。先回りした機能網羅は行いません。

## M3: 一般性の確認

次はデータ駆動variantで一般性を確認します。

## M4: 第3層

第2層のAPIと判断基準が安定した後、制作手順を`edit-illustrator` skillへまとめます。

## リポジトリ整理

- exampleの重複削減と生成物の保存方針
- CIで実行するIllustrator実機gateの運用決定
- 第3層skill骨格の凍結または縮小
