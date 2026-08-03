# POST /api/v1/user-agent/wallet/changes/search

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/wallet/changes/search

所属模块: UserAgents

## 请求体

```json
{
  "pageIndex": 0,
  "pageSize": 0,
  "direction": 0,
  "startTime": "string",
  "endTime": "string"
}
```

字段说明：

- `pageIndex`: int, 可选
- `pageSize`: int, 可选
- `direction`: int, 可选
- `startTime`: string, 可选
- `endTime`: string, 可选

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
