# V3.25 本地程序化券商桥接

## 用途与边界

`HttpBridgeBrokerAdapter` 用于连接用户本机已经安装、登录并获得授权的交易桥进程。它是 QMT/PTrade 之外的标准化本地出口，不提供券商能力，也不能绕过券商授权、风控或监管要求。

- 默认只允许 `127.0.0.1`、`localhost` 和 `::1`。
- 必须配置访问令牌。
- 桥接服务必须明确返回 `accepted: true`，系统才把委托视为已受理。
- 未配置 SDK、账号授权或本地桥时，系统保持模拟交易模式。
- 券商账号、密码、令牌和终端路径不得写入代码或提交 Git。

## 环境变量

```dotenv
BROKER_TYPE=http_bridge
BROKER_HTTP_URL=http://127.0.0.1:9901
BROKER_HTTP_TOKEN=replace-with-a-local-secret
BROKER_HTTP_ALLOW_REMOTE=false
BROKER_HTTP_TIMEOUT_SECONDS=5

FEATURE_LIVE_BROKER=true
LIVE_TRADING_ENABLED=true
ORDER_CONFIRM_REQUIRED=true
LIVE_KILL_SWITCH=false
TRADE_WHITELIST_SYMBOLS=300750,600438
MAX_LIVE_ORDER_VALUE=50000
MAX_DAILY_LIVE_ORDER_COUNT=20
MAX_DAILY_LOSS_PCT=3
```

远程地址默认被拒绝。只有用户自行完成网络隔离、双向认证和合规评估后，才应考虑设置 `BROKER_HTTP_ALLOW_REMOTE=true`。

## 本地桥接口契约

本地桥应实现以下 JSON HTTP 接口：

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/health` | 连接和授权状态 |
| POST | `/connect` | 连接本地券商终端 |
| POST | `/disconnect` | 断开连接 |
| GET | `/account` | 账户快照 |
| GET | `/cash` | 资金快照 |
| GET | `/positions` | 持仓列表 |
| GET | `/orders` | 委托列表 |
| GET | `/trades` | 成交列表 |
| POST | `/orders` | 提交委托 |
| GET | `/orders/{order_id}` | 查询委托 |
| POST | `/orders/{order_id}/cancel` | 撤单 |

请求使用 `Authorization: Bearer <BROKER_HTTP_TOKEN>`。响应中的时间、订单号、成交号和原始券商状态必须来自真实终端，不得生成占位数据。

## 下单安全链路

真实委托始终经过：

1. 使用服务器缓存中的可追溯行情，不接受浏览器伪造的行情快照；
2. 检查匹配标的的评分溯源；
3. 检查已落库且与方向、数量一致的实盘风控记录；
4. 校验行情新鲜度、重大负面信息、交易日和连续竞价时段；
5. 校验白名单、单笔金额、当日委托次数和 kill switch；
6. 进入人工确认队列；
7. 批准时重新执行全部检查，并校验券商连接、现金、可卖持仓和重复委托；
8. 经 `ExecutionRouter` 发送到本地桥，记录请求、响应、订单状态和图表标注。

任何一项失败都必须返回明确的阻断原因，不能降级为自动受理。

## 降级行为

- QMT SDK 不存在：QMT 适配器返回 `unsupported`。
- PTrade SDK 不存在：PTrade 适配器返回 `unsupported`。
- 本地桥未启动或令牌错误：HTTP 桥返回 `disconnected` 或 `failed`。
- 所有真实出口不可用：继续使用 `/realtime-paper`，不会真实下单。

研究辅助，不构成投资建议；真实交易需用户自行确认合规与风险。
