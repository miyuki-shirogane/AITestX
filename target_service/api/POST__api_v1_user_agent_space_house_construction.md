# 为当前登录用户开始一次房屋施工。

> 上游接口 `designs/search` 查询时使用 `designType=1`（House）

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/space/house-construction

所属模块: Spaces

## 请求体

```json
{
  "designId": "string",
  "presetAssetId": "string",
  "layoutJson": "{\"grid\":{\"columns\":2,\"rows\":2},\"items\":[{\"asset\":{\"source\":\"design\",\"designId\":\"019fef7e-5f14-71c5-b4ce-f2f8d55978e0\",\"resultFileId\":\"1-94a72633b30f457894f6ac80adf7e0db.png\"},\"colspan\":1,\"id\":\"house-1\",\"kind\":\"house\",\"render\":{\"mirroredX\":false},\"rowspan\":1,\"x\":0,\"y\":0}],\"version\":1}"
}
```

字段说明：

- `designId`: string, 可选, 自定义房屋设计 ID；使用预设房屋素材时为空。
- `presetAssetId`: string, 可选, 预设房屋素材 ID；使用自定义房屋设计时为空。
- `layoutJson`: string, 必填, 完整房屋布局 JSON。示例值见上方，包含 grid、items、version 等字段。

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": {
    "constructionId": "string",
    "status": 0,
    "expectedCompletedAt": "string",
    "constructionCost": 0,
    "economyBalance": 0
  }
}
```

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
