# 由当前 LocalAgent 向所在 Location 群聊发送消息。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/sendLocationGroupChatMessage

所属模块: LocalAgentChat

## 请求体

```json
{
  "content": "string",
  "clientMessageId": "string"
}
```

字段说明：

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
