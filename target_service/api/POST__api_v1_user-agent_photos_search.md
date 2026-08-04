# 分页查询AI搭档相册照片

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/photos/search

所属模块: UserAgents

## 请求体

```json
{
  "pageIndex": 0,
  "pageSize": 0,
  "keyword": "string",
  "sortDirection": "string"
}
```

字段说明：

- `pageIndex`: int, 可选, 当前页码，从1开始
- `pageSize`: int, 可选, 每页数量
- `keyword`: string, 可选, 照片内容关键字，匹配标题或URL
- `sortDirection`: object, 可选, 时间排序方向：0未知不排序，1正序，2倒序

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": "string"
}
```

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
