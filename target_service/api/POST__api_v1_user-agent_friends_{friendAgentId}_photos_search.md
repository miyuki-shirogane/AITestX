# 分页查询当前 AI 搭档与指定好友的共同照片。

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/friends/{friendAgentId}/photos/search

所属模块: AgentFriends

## 请求参数

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| friendAgentId | path | string | 是 |  |

## 请求体

```json
{
  "pageIndex": 0,
  "pageSize": 0
}
```

字段说明：

- `pageIndex`: int, 可选
- `pageSize`: int, 可选

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

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
