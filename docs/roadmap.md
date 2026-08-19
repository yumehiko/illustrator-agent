# ロードマップ

更新日: 2026-08-19

## 現在地

M1 reference productionは完了しました。M2では`quarterly_kpi_report`を明示的な`DocumentContext`とimmutableなnamed-role `DesignTheme`へ移行し、生成AIのbyte同一性を確認しました。

## M2: デザインモデルの拡張

次はM1に残るad-hocな入力validationを第2層の再利用可能な契約へ移します。その後、reference productionで必要になった順にlayout / overflow、component identity、image fitting、複数artboard等を追加します。先回りした機能網羅は行いません。

## M3: 一般性の確認

日本語文字組み、データ駆動variant、image / area text / 複数artboardを代表する異なる制作物で同じ完成条件を通します。

## M4: 第3層

第2層のAPIと判断基準が安定した後、制作手順を`edit-illustrator` skillへまとめます。

## リポジトリ整理

M1と並行して必要なものから行います。

- public APIとmodule構成の整理
- exampleの役割分類、重複削減、生成物の保存方針
- component unit testとend-to-end testの分離
- 生成・検証コマンドの統一とCI範囲の決定
- 第3層skill骨格の凍結または縮小
