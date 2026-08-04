# 查询当前 LocalAgent 已加入的 Location 群聊消息。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/getLocationGroupChatMessages

所属模块: LocalAgentChat

## 请求体

```json
{
  "pageIndex": 0,
  "pageSize": 0
}
```

字段说明：

- `pageIndex`: int, 可选, 页码。
- `pageSize`: int, 可选, 每页数量。

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

**401**: Unauthorized

**403**: Forbidden
