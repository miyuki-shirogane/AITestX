# 由当前 LocalAgent 退出所在 Location 群聊。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/leaveLocationGroupChat

所属模块: LocalAgentChat

## 请求体

```json
{
  "clientActionId": "string"
}
```

字段说明：

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
