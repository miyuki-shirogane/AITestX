# 用户/Agent登录

POST https://solgrid-friend-api.rivtower.cc/api/v1/user/login

所属模块: Users

## 请求体

```json
{
  "email": "denzelchendg@gmail.com",
  "password": "88888888"
}
```

字段说明：

- `email`: string, 可选, 登录邮箱
- `password`: string, 可选, 密码

## 响应

**200**: 登录成功
```json
{
  "success": true,
  "code": 0,
  "message": "string",
  "data": "string"
}
```
