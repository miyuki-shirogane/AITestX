# 获取一个未绑定邀请码；库存为空时补充邀请码池。

POST https://solgrid-friend-api.rivtower.cc/api/v1/invitation-codes/generate

所属模块: InvitationCodes

## 请求体

```json
{
  "count": 0
}
```

字段说明：

- `count`: int, 可选, 邀请码池为空时的补充数量，单次最多 100 个。

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": []
}
```

**400**: Bad Request
