# ロードマップ

更新日: 2026-08-18

## 現在地

リポジトリ分離直後です。第2層のauthoring APIと制作example、第3層skillの骨格はありますが、このリポジトリ内でend-to-endの完成判定と構成がまだ統一されていません。

## M1: reference production

代表制作物を1つ選び、Python sourceと入力から次を一続きで再現します。

- graphic IRと`.ai`の生成
- 第一層validation、semantic検査、preview
- 必要なnative materialization
- Illustrator実機での構造・編集性確認
- 人間によるvisual acceptance

この制作で見つかった不足だけを、第2層の実装またはfixture付きの第1層要求へ振り分けます。

## M2: デザインモデルの拡張

reference productionで必要になった順に、document context / theme、入力validation、layout / overflow、component identity、image fitting、複数artboard等を追加します。先回りした機能網羅は行いません。

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
