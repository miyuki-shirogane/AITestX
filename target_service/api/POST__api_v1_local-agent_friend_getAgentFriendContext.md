# 获取当前 LocalAgent 的好友上下文。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/friend/getAgentFriendContext

所属模块: LocalAgentFriend

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
