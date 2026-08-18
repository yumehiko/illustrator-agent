# 開発原則

1. 利用者の制作・改訂作業からcomponentとworkflowを設計する。
2. Python component、template、入力データを再生成可能なsource of truthにする。
3. 既存`.ai`は元ファイルをsource of truthにして、曖昧な対象選択では停止する。
4. 見た目だけでなく、階層、identity、編集可能性、再生成可能性を成果物として扱う。
5. flatten、outline、font置換等の損失を黙って行わない。
6. skillは薄いadapterとし、第1層のparser / writer / validatorを再実装しない。
7. 同じ明示的な入力、font、profileから同じIRを生成する。

このリポジトリはpre-1.0のためpublic APIの後方互換をまだ保証しません。抽象を変更するときは、テスト、example、文書を同じ変更で更新し、不要な互換wrapperを残しません。
