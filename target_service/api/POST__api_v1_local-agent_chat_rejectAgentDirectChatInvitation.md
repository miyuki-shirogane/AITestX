# 由当前 LocalAgent 拒绝私聊邀请。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/rejectAgentDirectChatInvitation

所属模块: LocalAgentChat

## 请求体

```json
{
  "invitationId": "string",
  "reason": "string"
}
```

字段说明：

- `invitationId`: string, 可选, 邀请标识。
- `reason`: string, 可选, 拒绝原因。

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": true
}
```

**401**: Unauthorized

**403**: Forbidden
