# EdgeOne 访问统计

当前仅启用后台采集和查询接口，不在页面展示浏览量、站点访问量、最近访问时间或热门文章排行。

## 数据与计数规则

- 同一浏览器 24 小时内仅增加一次站点总访问量；清除站点数据、无痕模式或更换浏览器会重新计数。
- 每次打开普通文章都会增加该文章的浏览量，目录首页只更新站点最近访问时间。
- 服务端不保存 IP、User-Agent、Cookie 或其他访客身份信息。
- 站点数据包括 `totalVisits` 和 `lastVisitedAt`；文章数据包括 `path`、`title`、`views` 和 `lastVisitedAt`。

## EdgeOne 部署

项目使用 `@edgeone/pages-blob`，Edge Function 首次调用时会创建名为 `notes-analytics` 的 Blob 命名空间，无需手动绑定环境变量。`edge-functions/api/analytics.js` 会自动映射为 `/api/analytics`。

计数采用“强一致读取后加一再写入”，适合个人博客；Blob SDK 没有原子自增，高并发下统计可能出现少量覆盖，因此结果应视为近似值。

## API

记录访问：

```http
POST /api/analytics
Content-Type: application/json

{
  "path": "/math/概率论/参数估计/",
  "title": "参数估计",
  "type": "article",
  "countSiteVisit": true
}
```

查询统计与热门文章：

```http
GET /api/analytics?limit=10
```

`limit` 默认为 10，范围为 1–20。排行按浏览量降序，相同浏览量按最近访问时间降序。

站点统计保存在 `analytics/site.json`；文章统计保存在 `analytics/articles/`，文件名使用文章路径的 SHA-256 摘要。排行最多扫描 256 篇文章，超过时响应中的 `meta.truncated` 为 `true`。
