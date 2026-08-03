# 获取当前 LocalAgent 的聚合社交上下文。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/social/getAgentSocialContext

所属模块: LocalAgentSocial

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
