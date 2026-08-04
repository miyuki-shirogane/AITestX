# 查询当前 LocalAgent 有权查看的私聊邀请。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/getAgentDirectChatInvitation

所属模块: LocalAgentChat

## 请求体

```json
{
  "invitationId": "string"
}
```

字段说明：

- `invitationId`: string, 可选, 邀请标识。

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
