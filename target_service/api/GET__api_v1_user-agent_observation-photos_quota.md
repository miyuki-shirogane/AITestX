# 获取用户今日观察照片拍摄额度。

GET https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/observation-photos/quota

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
