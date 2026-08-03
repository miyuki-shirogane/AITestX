# 创建视觉素材 临时开放C端，后续改成Admin权限

POST https://solgrid-friend-api.rivtower.cc/api/v1/visual-assets/create

所属模块: VisualAssets

## 请求体

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
