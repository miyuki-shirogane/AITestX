# 用户主动观察当前AI搭档并异步生成照片。

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/observation-photos

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
