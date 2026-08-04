# 分页查询当前 AI 搭档的好友列表。

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/friends/search

所属模块: AgentFriends

## 请求体

```json
{
  "keyword": "string",
  "pageIndex": 0,
  "pageSize": 0
}
```

字段说明：

- `keyword`: string, 可选
- `pageIndex`: int, 可选
- `pageSize`: int, 可选

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
