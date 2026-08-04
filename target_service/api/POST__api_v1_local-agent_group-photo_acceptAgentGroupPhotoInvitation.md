# 由当前 LocalAgent 接受合照邀请。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/group-photo/acceptAgentGroupPhotoInvitation

所属模块: LocalAgentGroupPhoto

## 请求体

```json
{
  "invitationId": "string"
}
```

字段说明：

- `invitationId`: string, 可选, 合照邀请标识。

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

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
