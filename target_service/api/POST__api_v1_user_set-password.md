# 新注册号码设置密码

POST https://solgrid-friend-api.rivtower.cc/api/v1/user/set-password

所属模块: Users

## 请求体

```json
{
  "password": "string"
}
```

字段说明：

- `password`: string, 必填, 密码

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
