# 查询世界当前状态

POST https://solgrid-friend-api.rivtower.cc/api/v1/world/current-state

所属模块: World

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
