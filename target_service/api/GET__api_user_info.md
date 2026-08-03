# 获取用户信息

GET http://localhost:8080/api/user/info

所属模块: 用户

## 请求参数

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| token | header | string | 是 | 认证token |

## 响应

**200**: 成功
```json
{
  "code": 0,
  "data": "string"
}
```
