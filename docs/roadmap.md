# ロードマップ

更新日: 2026-08-18

## 現在地

第2層のcomponent authoring MVPと、第3層の`edit-illustrator` skill骨格があります。リポジトリ分離後は、実際の制作依頼を通してworkflowと不足componentを追加します。

## 次の候補

1. skillの最初のend-to-end制作セッション
2. inspect / plan / generate-or-patch / validate / previewの標準workflow
3. image contain / cover / clipping crop
4. missing / modified link診断と安全な再link
5. component identityとsidecar semantic manifest
6. font / color / spacing / document contextの共有theme
7. page分割、複合layout、overflow / missing font検証

優先順位は網羅性ではなく、具体的な制作要求と再利用価値で決めます。第1層の不足はskill内で迂回せず、fixtureと検証条件を持つ要求として`py-ai-illustrator`へ返します。
