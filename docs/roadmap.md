# ロードマップ

更新日: 2026-08-20

## 現在地

M1 reference production、新規制作のnative-first移行、再利用可能な入力contractに加え、provenance付きfont-aware layout / fail-closed overflow APIが完了しました。日本語scheduleと`product_catalog`は、指定font、native compile/reopen、semantic preservation、PDF preview、visual acceptanceまでIllustrator 30.7実機gateを通過しています。`product_catalog`ではlinked image、editable area text、2 artboardと、保存・再open後の非overflow、2ページpreviewを確認済みです。`campaign_variants`はsemantic key由来のstable identity、3つのnamed artboard、pure gateまで実装済みですが、Illustratorでのnative compile / reopen、preview、visual acceptanceは未完了です。

## M2: デザインモデルの拡張

component identityと複数artboardはpure gateまで実装済みです。`campaign_variants`のIllustrator実機gateを通してproduction sliceを完了します。先回りした機能網羅は行いません。

## M3: 一般性の確認

`campaign_variants`のnative compile / reopen、複数artboard、preview、visual acceptanceを確認し、データ駆動variantの完成条件を通します。

## M4: 第3層

第2層のAPIと判断基準が安定した後、制作手順を`edit-illustrator` skillへまとめます。

## リポジトリ整理

- exampleの重複削減と生成物の保存方針
- CIで実行するIllustrator実機gateの運用決定
- 第3層skill骨格の凍結または縮小
