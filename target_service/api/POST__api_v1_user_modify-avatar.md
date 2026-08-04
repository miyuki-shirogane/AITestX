# 修改用户头像

POST https://solgrid-friend-api.rivtower.cc/api/v1/user/modify-avatar

所属模块: Users

## 请求体

```json
{
  "avatar": "string"
}
```

字段说明：

- `avatar`: string, 可选, 头像 URL

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

**401**: Unauthorized

**403**: Forbidden
