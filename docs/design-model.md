# 第2層: デザインモデル

## ゴール

人間またはCodexが、意味と再生成規則を持つPythonデザインオブジェクトを書き、決定的に編集可能な`.ai`へ変換し、Illustrator上で意図した見た目・構造・編集性を確認できる状態にします。

第2層はcomponent、template、variant、layout、theme、入力validation、stable identityを所有し、第一層のgraphic IRへrenderします。`.ai`のparser、writer、低水準IR、検証は`py-ai-illustrator`へ委譲します。依存方向は`illustrator-agent -> py-ai-illustrator`だけです。新規制作の正式経路は`Document IR -> compile_native_ai -> PDF-compatible native AI -> reopen検証`であり、legacy AIを中間生成物、oracle、production gateにしません。

`DocumentContext`はcanvas、内部表現がpointであること、title、metadata、`DesignTheme`を明示します。`unit == "pt"`は利用者の入力単位を制限する製品要件ではなく、IRへ渡す座標の宣言です。themeは色と文字styleをnamed roleで解決し、componentが要求するroleの欠落を既定値で補わず拒否します。

## Source of truth

新規生成ではPython source、template、入力データをsource of truthとします。既存`.ai`の局所編集では元ファイルをsource of truthとして第一層のsource-preserving patchを使い、一般の`.ai`から高水準componentを推測復元しません。

## Render契約

1. componentは入力を検証してからIRを生成する。
2. 暗黙の時刻、環境、global stateへ依存しない。
3. font、座標系、色、単位、layout policyを明示する。
4. render後は第一層のcompatibility / semantic / visual validationを通す。
5. flatten、outline、font置換等の損失を黙って行わない。
6. textを含む非rigid transform等、意味が未定義な操作は拒否する。

制約は製品要件、第1層IR/backendの現在の能力限界、determinism・editability・fail-closed等の安全性保証へ分類します。組版判断はtext、PostScript font名、size、trackingと計測method/sourceを一体のevidenceとして扱います。決定的な近似はprovisional wrapに限り、font-awareではない結果を`verified-fit`へ昇格させません。fail-closed productionは外部のfont-aware measurement evidenceとの完全一致を要求し、不足、条件違い、overflowを拒否します。font計測やIllustrator DOM処理自体は第1層の責務であり、この層は記録済み結果の契約とlayout policyだけを所有します。

text/imageの非rigid transform拒否は現行IR/backendの能力限界で、恒久的な製品制約ではありません。

pure gateは`Document`生成、JSON往復、determinism、production contractと記録済みlayout evidenceをIllustratorなしで検証します。native compile、指定fontの利用可否、保存・再open後のsemantic/editability、PDF preview、visual acceptanceはIllustrator実機gateとして分離します。

## 完成条件

代表制作物ごとに次を確認します。

1. Python上で役割、variant、layout規則が明示されている。
2. previewとIllustrator実機表示が意図に合う。
3. text、path、group、layer、imageが必要な粒度で編集できる。
4. 同じ明示的な入力、font、asset、profileから同等のIRと`.ai`を再生成できる。

## 第1層への要求

不足機能は、実ファイルfixture、必要operation、未対応情報の保持条件、semantic / visual / native editabilityの検証条件を揃えて`py-ai-illustrator`へ要求します。第二層で低水準処理を迂回実装しません。

## 第3層との境界

第3層は自然言語と素材から、この層のPythonモデルまたは検証可能な入力データを作る薄いworkflowです。第2層の完成条件が安定するまで本格実装を延期し、第三層専用のデザイン表現は増やしません。
