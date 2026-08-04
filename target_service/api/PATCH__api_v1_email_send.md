# 发送邮件验证码

PATCH https://solgrid-friend-api.rivtower.cc/api/v1/email/send

所属模块: Email

## 请求体

```json
{
  "email": "string",
  "codeType": "string"
}
```

字段说明：

- `email`: string, 必填, 邮箱账号
- `codeType`: object, 可选, 验证码类型 1-登录；2-重置密码；3-注册；4-修改邮箱；8-注销账户

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
