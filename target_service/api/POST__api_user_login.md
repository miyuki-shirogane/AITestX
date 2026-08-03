# 用户登录

POST http://localhost:8080/api/user/login

所属模块: 用户

## 请求体

```json
{
  "username": "admin",
  "password": "123456"
}
```

字段说明：

- `username`: string, 必填, 用户名
- `password`: string, 必填, 密码

## 响应

**200**: 登录成功
```json
{
  "code": 0,
  "data": "string"
}
```

**401**: 登录失败
```json
{
  "code": 1001,
  "msg": "用户名或密码错误"
}
```
