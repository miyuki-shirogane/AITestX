# 验证邮件验证码

POST https://solgrid-friend-api.rivtower.cc/api/v1/email/verify

所属模块: Email

## 请求体

```json
{
  "email": "string",
  "verifyCode": "string",
  "codeType": "string"
}
```

字段说明：

- `email`: string, 必填, 邮箱地址
- `verifyCode`: string, 必填, 邮箱验证码
- `codeType`: object, 可选, 验证类型

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

**400**: Bad Request
