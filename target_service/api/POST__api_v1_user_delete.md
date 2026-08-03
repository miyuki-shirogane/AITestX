# 注销账户

POST https://solgrid-friend-api.rivtower.cc/api/v1/user/delete

所属模块: Users

## 请求体

```json
{
  "email": "string",
  "code": "string"
}
```

字段说明：

- `email`: string, 必填, Email
- `code`: string, 必填, 验证码

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
