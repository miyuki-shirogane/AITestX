# 检查用户昵称是否可用

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/check-user-call-name

所属模块: UserAgents

## 请求体

```json
{
  "userCallName": "string"
}
```

字段说明：

- `userCallName`: string, 必填, 用户昵称

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
