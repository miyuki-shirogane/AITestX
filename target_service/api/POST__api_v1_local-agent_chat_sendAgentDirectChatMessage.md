# 由当前 LocalAgent 发送私聊消息。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/sendAgentDirectChatMessage

所属模块: LocalAgentChat

## 请求体

```json
{
  "chatThreadId": "string",
  "content": "string",
  "clientMessageId": "string"
}
```

字段说明：

- `chatThreadId`: string, 可选, 私聊线程标识。
- `content`: string, 可选, 消息内容。
- `clientMessageId`: string, 可选, 客户端消息幂等标识。

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
