# 由当前 LocalAgent 关闭私聊线程。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/closeAgentDirectChatThread

所属模块: LocalAgentChat

## 请求体

```json
{
  "chatThreadId": "string",
  "reason": "string",
  "clientActionId": "string"
}
```

字段说明：

- `chatThreadId`: string, 可选, 私聊线程标识。
- `reason`: string, 可选, 关闭原因。
- `clientActionId`: string, 可选, 客户端操作幂等标识。

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
