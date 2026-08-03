# 查询当前 LocalAgent 的 Location 状态。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/chat/getAgentLocationState

所属模块: LocalAgentChat

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
