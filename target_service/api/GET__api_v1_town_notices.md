# 分页查询当前仍然有效、可供页面展示的小镇公告。

GET https://solgrid-friend-api.rivtower.cc/api/v1/town/notices

所属模块: Npcs

## 请求参数

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| pageIndex | query | int | 是 | 页码，从 1 开始。 |
| pageSize | query | int | 是 | 每页返回的公告数量。 |

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
