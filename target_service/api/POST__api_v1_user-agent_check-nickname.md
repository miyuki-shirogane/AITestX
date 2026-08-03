# 检查AI搭档昵称是否可用

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/check-nickname

所属模块: UserAgents

## 请求体

```json
{
  "nickname": "string"
}
```

字段说明：

- `nickname`: string, 必填, AI搭档昵称

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
