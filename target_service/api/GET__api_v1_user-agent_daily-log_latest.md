# 查询当前登录用户的 UserAgent 最新每日日志。

GET https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/daily-log/latest

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
