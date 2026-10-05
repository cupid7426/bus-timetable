# 赤羽駅行きバス時刻表
赤羽北三丁目・志村四小の6つの乗り場(うち5つが赤羽駅行き)から、希望時刻の前後に出るバスを表示します。
- `python scripts/fetch.py` で `docs/data.json` を更新(毎日04:00 JSTにGitHub Actionsが自動実行)
- `docs/` をGitHub Pagesで公開(Settings → Pages → main /docs)
- 乗り場の追加・変更は `config.json`
