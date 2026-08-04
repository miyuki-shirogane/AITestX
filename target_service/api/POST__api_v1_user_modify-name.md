# 修改用户昵称

POST https://solgrid-friend-api.rivtower.cc/api/v1/user/modify-name

所属模块: Users

## 请求体

```json
{
  "nickname": "string"
}
```

字段说明：

- `nickname`: string, 可选, 昵称

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
