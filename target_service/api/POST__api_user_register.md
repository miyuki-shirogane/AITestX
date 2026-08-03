# 用户注册

POST http://localhost:8080/api/user/register

所属模块: 用户

## 请求体

```json
{
  "username": "string",
  "password": "string",
  "email": "string"
}
```

字段说明：

- `username`: string, 必填, 用户名
- `password`: string, 必填, 密码
- `email`: string, 必填, 邮箱

## 响应

**200**: 注册成功
```json
{
  "code": 0,
  "msg": "string"
}
```
