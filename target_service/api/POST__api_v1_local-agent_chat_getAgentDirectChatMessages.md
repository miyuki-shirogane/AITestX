# 查询当前 LocalAgent 可读的私聊消息。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/getAgentDirectChatMessages

所属模块: LocalAgentChat

## 请求体

```json
{
  "chatThreadId": "string",
  "pageIndex": 0,
  "pageSize": 0
}
```

字段说明：

- `chatThreadId`: string, 可选, 私聊线程标识。
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
