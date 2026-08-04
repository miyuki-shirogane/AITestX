# 查询当前用户信息

POST https://solgrid-friend-api.rivtower.cc/api/v1/user/info

所属模块: Users

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

**401**: Unauthorized

**403**: Forbidden
