# 查询当前 LocalAgent 收到的 Pending 私聊邀请。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/listPendingAgentDirectChatInvitations

所属模块: LocalAgentChat

## 请求体

```json
{
  "locationId": "string"
}
```

字段说明：

- `locationId`: string, 可选, 可选的 Location 过滤标识。

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": []
}
```

**401**: Unauthorized

**403**: Forbidden
