# 查询当前登录用户的 LocalAgent 状态。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/status

所属模块: LocalAgents

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
