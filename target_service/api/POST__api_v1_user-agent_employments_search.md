# 分页查询当前登录用户的 UserAgent 与 NPC 建立的雇佣关系。

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/employments/search

所属模块: Npcs

## 请求体

```json
{
  "pageIndex": 0,
  "pageSize": 0
}
```

字段说明：

- `pageIndex`: int, 可选, 页码，从 1 开始。
- `pageSize`: int, 可选, 每页返回的雇佣关系数量。

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
