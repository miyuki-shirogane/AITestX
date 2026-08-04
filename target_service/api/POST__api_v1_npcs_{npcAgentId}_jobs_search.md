# 分页查询指定 NPC 当前发布的岗位信息。

POST https://solgrid-friend-api.rivtower.cc/api/v1/npcs/{npcAgentId}/jobs/search

所属模块: Npcs

## 请求参数

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| npcAgentId | path | string | 是 | 发布岗位的 NPC ID。 |

## 请求体

```json
{
  "pageIndex": 0,
  "pageSize": 0
}
```

字段说明：

- `pageIndex`: int, 可选, 页码，从 1 开始。
- `pageSize`: int, 可选, 每页返回的岗位数量。

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
