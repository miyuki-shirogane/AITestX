# 用户注册

POST https://solgrid-friend-api.rivtower.cc/api/v1/user/register

所属模块: Users

## 请求体

```json
{
  "email": "string",
  "verificationId": "string",
  "password": "string",
  "confirmPassword": "string",
  "invitationCode": "string"
}
```

字段说明：

- `email`: string, 必填, 邮箱
- `verificationId`: string, 必填, 验证 Id
- `password`: string, 必填, 密码
- `confirmPassword`: string, 必填, 确认密码
- `invitationCode`: string, 必填, 邀请码

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
