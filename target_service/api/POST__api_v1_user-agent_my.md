# 查询当前用户AI搭档信息

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/my

所属模块: UserAgents

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
