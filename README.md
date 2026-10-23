# 借书之问

以一本书为线索，讲一个值得思考的问题。

- [系统之美](site/systems/index.html)：八期原创主题阅读。
- [反脆弱](site/antifragile/index.html)：八期原创主题阅读。
- [有限与无限的游戏](site/infinite-games/index.html)：六期原创主题阅读，附思考练习与笔记。

- [格外的活法](site/extraordinary-lives/index.html)：六期完整原创讲述，依据公开访谈与理论材料，附来源、练习、笔记和 Markdown 阅读稿。

- [土星之环](site/saturn/index.html)：八期主题深读，附文学形式、历史证据与记忆辨析。
- [日本历史与经济](site/japan/index.html)：十二期深读，附历史机制、因果辨析与资料出处。
- [Agent：机器如何学会做事](site/agent/index.html)：十二期工程深读，附机制推演与动手自检。

- [哥德尔、艾舍尔、巴赫：集异璧之大成](site/geb/index.html)：八期完整原创主题深读，第 2—8 期新增约 1.4 万汉字；含原著章节索引、参考资料、案例与反例、思考练习、分期笔记、打印和 Markdown 下载。

土星之环、日本历史与经济和 Agent 三辑均同步已发布的深读版；每辑页末提供整辑静态全文入口，可打印保存。

- [滔天洪水](site/deluge/index.html)：当前完整导读与八期后续阅读规划，附资料来源、阅读进度、字号/夜读设置和本地笔记导出。

- [崩盘](site/crashed/index.html)：深化主题文章（约6500字），六节正文，补充货币基金挤兑、美元互换、爱尔兰担保与2012年欧元救援案例；附14项来源、论证证据表、资本缓冲互动示例、原著阅读索引和 [Markdown阅读稿](site/crashed/reading.md)。

- [四千周](site/four-thousand-weeks/index.html)：六期完整原创讲述，附原著线索、案例与反例、适用边界、一手资料索引、个人笔记、口播复制及整辑静态全文。

站点首页：`site/index.html`。完整文章、搜索、阅读进度、笔记与原有阅读工具均保留。笔记和进度仅存当前浏览器，不跨设备同步。

## GitHub Pages

在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。工作流 `.github/workflows/pages.yml` 会把 `site/` 发布到 Pages；首次启用后，可在 Actions 中运行 **Deploy reading site to GitHub Pages**。

预期网址：https://byteleee.github.io/QTB/

后续提交到 `main` 会自动更新站点。正文为独立原创评论，不替代原著；说明性虚构场景不应当作真实史料。


## 《集异璧之大成》内容维护

第 2—8 期正文：`site/geb/manuscripts/`；标题、原著定位与资料：`site/geb/episodes.json`。修改后运行 `python scripts/build-geb.py` 生成独立阅读页、带参考资料的下载稿与八期合辑。第一期正文保留在系列首页，旧入口和第一期笔记键保持兼容。内容验收记录见 `site/geb/content-review.md`。
