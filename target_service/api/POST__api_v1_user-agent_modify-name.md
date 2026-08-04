# 修改用户AI搭档昵称

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/modify-name

所属模块: UserAgents

## 请求体

```json
{
  "nickname": "string",
  "userCallName": "string"
}
```

字段说明：

- `nickname`: string, 必填, AI搭档昵称
- `userCallName`: string, 必填, AI搭档如何称呼用户

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
