from __future__ import annotations

from typing import Any


RULES: list[dict[str, Any]] = [
    {
        "key": "electronic_special_gas",
        "keywords": ["电子特气", "特种气体", "六氟化钨", "三氟化氮", "中船特气"],
        "industries": ["电子特种气体", "半导体材料", "化工新材料"],
        "concepts": ["半导体", "国产替代", "军工电子"],
        "symbols": [],
        "reason": "电子特种气体的产能、价格、订单和盈利变化会影响半导体材料及军工电子产业链预期。",
    },
    {
        "key": "photovoltaic",
        "keywords": ["光伏", "硅料", "多晶硅", "硅片", "组件", "TOPCon", "HJT", "BC电池"],
        "industries": ["光伏设备", "硅料", "硅片", "光伏组件", "电站"],
        "concepts": ["光伏", "新能源", "绿色电力"],
        "symbols": [],
        "reason": "硅料价格、装机需求、出口政策和技术路线会影响光伏产业链盈利预期。",
    },
    {
        "key": "battery",
        "keywords": ["动力电池", "锂电", "固态电池"],
        "industries": ["动力电池"],
        "concepts": ["锂电池"],
        "symbols": [],
        "reason": "电池材料价格、技术路线和车企需求会影响动力电池产业链订单与利润率。",
    },
    {
        "key": "energy_storage",
        "keywords": ["储能", "逆变器", "PCS"],
        "industries": ["储能系统", "逆变器"],
        "concepts": ["储能"],
        "symbols": [],
        "reason": "储能招标、并网规则、逆变器准入和电芯成本会影响储能系统订单与盈利预期。",
    },
    {
        "key": "foreign_grid_equipment_restriction",
        "keywords": [
            "美国电网", "大容量电力系统", "外国电力设备", "电网安全",
            "并网逆变器", "进口逆变器", "储能系统设备", "国家紧急状态",
            "bulk-power system", "grid-connected inverter", "battery energy storage system",
            "foreign-produced power inverter", "foreign equipment from us energy grid",
        ],
        "industries": ["光伏设备", "逆变器", "储能系统", "电网设备"],
        "concepts": ["光伏", "储能", "出口限制", "供应链安全"],
        "symbols": [],
        "reason": "美国电网设备准入、采购和安全审查可能影响逆变器及储能系统的海外订单、认证成本与供应链安排；具体影响以实施细则和公司披露为准。",
    },
    {
        "key": "ai_semiconductor",
        "keywords": ["人工智能", "AI", "算力", "芯片", "半导体", "存储芯片", "出口管制", "科技股", "费城半导体"],
        "industries": ["半导体", "算力基础设施", "电子", "通信设备"],
        "concepts": ["人工智能", "国产替代", "芯片", "算力"],
        "symbols": [],
        "reason": "算力需求、芯片周期和出口限制会改变半导体及电子产业链景气预期。",
    },
    {
        "key": "dram_memory_chain",
        "keywords": ["长鑫科技", "长鑫存储", "DRAM", "动态随机存取存储器", "存储器", "存储芯片", "内存芯片"],
        "industries": ["存储芯片", "半导体设备", "半导体材料", "集成电路"],
        "concepts": ["国产存储", "半导体", "国产替代", "DRAM"],
        "symbols": [],
        "reason": "DRAM 产能、价格、资本开支和上市融资会影响存储芯片、半导体设备及材料产业链预期。",
    },
    {
        "key": "large_ipo_liquidity",
        "keywords": ["IPO", "首次公开发行", "发行上市", "申购", "募集资金", "募资", "战略配售"],
        "industries": ["资本市场"],
        "concepts": ["IPO资金分流", "新股供给"],
        "symbols": [],
        "reason": "大额新股发行可能在申购、缴款和上市窗口占用市场资金，但影响强度必须以真实发行规模和时间为依据。",
        "market_wide": True,
    },
    {
        "key": "global_technology_risk",
        "keywords": ["纳斯达克", "科技股抛售", "芯片股抛售", "半导体股下跌", "AI交易", "人工智能泡沫"],
        "industries": ["高估值成长", "科技成长", "半导体"],
        "concepts": ["全球科技风险", "风险偏好", "估值折现"],
        "symbols": [],
        "reason": "海外科技与半导体风险偏好变化会通过估值、外资和情绪传导至A股成长板块。",
        "market_wide": True,
    },
    {
        "key": "robot_low_altitude",
        "keywords": ["机器人", "人形机器人", "低空经济", "无人机", "飞行汽车", "航空航天"],
        "industries": ["机器人", "自动化设备", "航空装备", "低空经济"],
        "concepts": ["机器人", "低空经济", "高端制造"],
        "symbols": [],
        "reason": "订单、政策试点和关键零部件进展会影响机器人与低空经济主题强度。",
    },
    {
        "key": "liquor_consumption",
        "keywords": ["白酒", "食品饮料", "消费", "免税", "零售", "以旧换新"],
        "industries": ["白酒", "食品饮料", "零售"],
        "concepts": ["大消费", "消费复苏"],
        "symbols": [],
        "reason": "终端动销、库存、价格带和消费政策会影响食品饮料及零售预期。",
    },
    {
        "key": "finance",
        "keywords": ["银行", "券商", "保险", "资本市场", "两融", "降准", "净息差"],
        "industries": ["银行", "证券", "保险"],
        "concepts": ["大金融", "中特估"],
        "symbols": [],
        "reason": "利率、资本市场活跃度和信用环境会影响银行、券商和保险。",
    },
    {
        "key": "resources_energy",
        "keywords": ["原油", "油价", "OPEC", "天然气", "煤炭", "焦煤", "焦炭"],
        "industries": ["石油石化", "煤炭", "化工", "航空物流"],
        "concepts": ["能源价格", "周期资源"],
        "symbols": [],
        "reason": "能源价格影响资源企业收入，也影响化工、航空和物流成本。",
    },
    {
        "key": "metals_gold",
        "keywords": ["黄金", "金价", "贵金属", "铜价", "铝价", "稀土", "有色金属"],
        "industries": ["黄金", "有色金属", "稀土"],
        "concepts": ["避险资产", "贵金属", "周期资源"],
        "symbols": [],
        "reason": "商品价格和美元流动性会直接影响有色金属企业盈利预期。",
    },
    {
        "key": "agriculture",
        "keywords": ["生猪", "猪价", "粮食", "种业", "饲料", "大豆", "玉米", "农业"],
        "industries": ["养殖业", "饲料", "种植业", "农产品加工"],
        "concepts": ["农业", "猪周期", "粮食安全"],
        "symbols": [],
        "reason": "农产品价格、养殖周期和天气变化会影响饲料、养殖及种植产业链。",
    },
    {
        "key": "medicine",
        "keywords": ["创新药", "医疗器械", "医药", "集采", "医保", "CXO"],
        "industries": ["医药生物", "医疗器械", "医疗服务"],
        "concepts": ["创新药", "医疗健康"],
        "symbols": [],
        "reason": "研发进展、集采规则和医保政策会改变医药产业链估值与盈利预期。",
    },
    {
        "key": "defense",
        "keywords": ["军工", "国防", "军贸", "导弹", "卫星", "航空发动机"],
        "industries": ["国防军工", "航空装备", "卫星产业"],
        "concepts": ["军工", "商业航天"],
        "symbols": [],
        "reason": "订单、国防预算和地缘事件会影响军工产业链景气及风险偏好。",
    },
    {
        "key": "property_infrastructure",
        "keywords": ["房地产", "地产", "基建", "建材", "水泥", "城中村", "专项债"],
        "industries": ["房地产", "建筑材料", "基础建设"],
        "concepts": ["稳增长", "地产链"],
        "symbols": [],
        "reason": "销售、融资、土地和财政政策会影响地产及基建产业链现金流预期。",
    },
    {
        "key": "home_appliance_consumer",
        "keywords": ["家电", "空调", "冰箱", "洗衣机", "厨电", "白色家电", "家电以旧换新"],
        "industries": ["家用电器", "白色家电", "消费电子"],
        "concepts": ["耐用消费", "以旧换新", "出口消费"],
        "symbols": [],
        "reason": "终端需求、原材料成本、地产后周期和以旧换新政策会影响家电行业收入与利润率。",
    },
    {
        "key": "automotive_chain",
        "keywords": ["汽车", "乘用车", "商用车", "汽车零部件", "智能驾驶", "车企", "汽车销量"],
        "industries": ["汽车整车", "汽车零部件", "智能驾驶"],
        "concepts": ["汽车产业链", "出海", "智能汽车"],
        "symbols": [],
        "reason": "销量、价格竞争、出口政策和零部件供需会影响汽车产业链景气。",
    },
    {
        "key": "industrial_machinery",
        "keywords": ["工程机械", "工业母机", "机床", "工业自动化", "专用设备", "通用设备", "机械设备"],
        "industries": ["机械设备", "工业自动化", "高端制造"],
        "concepts": ["设备更新", "制造业投资"],
        "symbols": [],
        "reason": "制造业投资、设备更新、出口订单和原材料价格会影响机械设备企业。",
    },
    {
        "key": "software_cloud_cyber",
        "keywords": ["软件", "云计算", "网络安全", "数据要素", "信创", "大模型", "操作系统", "数据库"],
        "industries": ["软件开发", "云计算", "网络安全"],
        "concepts": ["数字经济", "信创", "人工智能"],
        "symbols": [],
        "reason": "政企IT支出、云与AI需求、数据合规和国产化进度会影响软件与网络安全产业链。",
    },
    {
        "key": "communications_network",
        "keywords": ["通信", "运营商", "光模块", "光通信", "5G", "6G", "基站", "卫星通信"],
        "industries": ["通信设备", "通信服务", "光通信"],
        "concepts": ["5G/6G", "算力网络", "卫星互联网"],
        "symbols": [],
        "reason": "运营商资本开支、网络升级和算力互联需求会影响通信设备与服务。",
    },
    {
        "key": "shipping_logistics",
        "keywords": ["航运", "港口", "集运", "集装箱", "运价", "物流", "快递", "航空运输", "红海航线"],
        "industries": ["航运港口", "物流", "航空运输"],
        "concepts": ["全球贸易", "运价周期", "供应链"],
        "symbols": [],
        "reason": "贸易量、运价、航线扰动、油价和港口效率会影响航运与物流盈利。",
    },
    {
        "key": "power_grid_utilities",
        "keywords": ["电网", "特高压", "输配电", "变压器", "电力设备", "火电", "水电", "核电", "绿电"],
        "industries": ["电网设备", "电力", "公用事业"],
        "concepts": ["新型电力系统", "特高压", "绿色电力"],
        "symbols": [],
        "reason": "电网投资、电价机制、利用小时和燃料成本会影响电力设备与公用事业。",
    },
    {
        "key": "chemicals_new_materials",
        "keywords": ["化工", "化学制品", "化学原料", "新材料", "氟化工", "农药", "化肥", "MDI"],
        "industries": ["基础化工", "化工新材料"],
        "concepts": ["周期化工", "国产替代"],
        "symbols": [],
        "reason": "产品价差、能源成本、供给约束和下游需求会影响化工企业盈利。",
    },
    {
        "key": "electronics_components",
        "keywords": ["消费电子", "电子元件", "PCB", "连接器", "被动元件", "面板", "苹果产业链"],
        "industries": ["消费电子", "电子元件", "光学光电子"],
        "concepts": ["电子产业链", "智能终端"],
        "symbols": [],
        "reason": "终端销量、库存周期、产品升级和客户资本开支会影响电子元件产业链。",
    },
    {
        "key": "media_gaming",
        "keywords": ["游戏", "版号", "影视", "广告", "传媒", "短剧", "出版"],
        "industries": ["游戏", "影视院线", "传媒"],
        "concepts": ["内容消费", "文化传媒"],
        "symbols": [],
        "reason": "内容供给、监管许可、用户付费和广告景气会影响传媒游戏行业。",
    },
    {
        "key": "tourism_hotel",
        "keywords": ["旅游", "酒店", "景区", "免税", "出入境", "客流", "餐饮"],
        "industries": ["旅游及景区", "酒店餐饮", "免税零售"],
        "concepts": ["服务消费", "出行链"],
        "symbols": [],
        "reason": "客流、房价、航班和消费政策会影响旅游酒店及免税零售。",
    },
    {
        "key": "environmental_services",
        "keywords": ["环保", "水务", "固废", "垃圾焚烧", "污水处理", "碳交易", "节能"],
        "industries": ["环保", "水务", "固废处理"],
        "concepts": ["绿色发展", "碳中和"],
        "symbols": [],
        "reason": "环保标准、项目回款、地方财政和碳政策会影响环保公用事业。",
    },
    {
        "key": "textile_apparel",
        "keywords": ["纺织", "服装", "棉花", "化纤", "鞋服", "品牌服饰"],
        "industries": ["纺织制造", "服装家纺"],
        "concepts": ["可选消费", "出口链"],
        "symbols": [],
        "reason": "棉价、汇率、出口订单和终端库存会影响纺织服装产业链。",
    },
    {
        "key": "retail_ecommerce",
        "keywords": ["零售", "电商", "商超", "百货", "跨境电商", "社会消费品零售"],
        "industries": ["商业零售", "互联网电商"],
        "concepts": ["消费复苏", "平台经济"],
        "symbols": [],
        "reason": "居民消费、平台政策、流量成本和库存周转会影响零售与电商。",
    },
    {
        "key": "global_liquidity",
        "keywords": ["美联储", "非农", "CPI", "PCE", "降息", "加息", "美债", "美元"],
        "industries": ["高估值成长", "科技成长", "贵金属"],
        "concepts": ["利率敏感", "全球流动性"],
        "symbols": [],
        "reason": "美国就业和通胀数据会改变利率路径，通过估值折现、汇率和风险偏好影响A股。",
        "market_wide": True,
    },
]


# 公司画像分类与事件识别分开：这里仅在行情源/公告画像已明确给出
# 行业或主营文字后做归类，绝不凭股票代码随机猜题材。
PROFILE_SECTOR_RULES: list[dict[str, Any]] = [
    {"key": "semiconductor", "keywords": ["半导体", "集成电路", "芯片", "封测", "半导体设备", "电子特气"], "industries": ["半导体"], "concepts": ["芯片", "国产替代"], "chain": ["芯片设计/制造/设备材料"]},
    {"key": "electronics", "keywords": ["消费电子", "电子元件", "光学光电子", "PCB", "元器件"], "industries": ["电子"], "concepts": ["智能终端"], "chain": ["电子元件与终端"]},
    {"key": "software", "keywords": ["软件", "信息技术", "云计算", "网络安全", "数据服务", "计算机应用"], "industries": ["软件与信息服务"], "concepts": ["数字经济", "信创"], "chain": ["软件/云/数据"]},
    {"key": "communications", "keywords": ["通信设备", "通信服务", "电信运营", "光通信", "5G", "6G"], "industries": ["通信"], "concepts": ["5G/6G", "算力网络"], "chain": ["通信网络与设备"]},
    {"key": "photovoltaic", "keywords": ["光伏", "太阳能", "硅料", "硅片", "逆变器"], "industries": ["光伏设备"], "concepts": ["光伏", "新能源"], "chain": ["光伏产业链"]},
    {"key": "battery", "keywords": ["动力电池", "锂电", "固态电池"], "industries": ["动力电池"], "concepts": ["锂电池"], "chain": ["动力电池产业链"]},
    {"key": "energy_storage", "keywords": ["储能", "逆变器", "PCS"], "industries": ["储能系统"], "concepts": ["储能"], "chain": ["储能系统与逆变器"]},
    {"key": "power_grid", "keywords": ["电力设备", "电网设备", "输配电", "特高压", "变压器", "公用事业", "电力"], "industries": ["电力与电网设备"], "concepts": ["新型电力系统"], "chain": ["发电/输配电/用电"]},
    {"key": "automotive", "keywords": ["汽车整车", "汽车零部件", "乘用车", "商用车", "汽车服务"], "industries": ["汽车"], "concepts": ["汽车产业链", "智能汽车"], "chain": ["整车与零部件"]},
    {"key": "home_appliance", "keywords": ["家用电器", "白色家电", "黑色家电", "厨卫电器", "小家电", "家电"], "industries": ["家用电器"], "concepts": ["耐用消费", "以旧换新"], "chain": ["家电制造与消费"]},
    {"key": "machinery", "keywords": ["机械设备", "工程机械", "通用设备", "专用设备", "工业母机", "自动化设备"], "industries": ["机械设备"], "concepts": ["高端制造", "设备更新"], "chain": ["制造设备"]},
    {"key": "defense", "keywords": ["国防军工", "军工", "航空装备", "航天装备", "船舶制造"], "industries": ["国防军工"], "concepts": ["军工", "商业航天"], "chain": ["军工装备"]},
    {"key": "medicine", "keywords": ["医药生物", "化学制药", "中药", "医疗器械", "医疗服务", "创新药", "生物制品"], "industries": ["医药医疗"], "concepts": ["创新药", "医疗健康"], "chain": ["医药研发/制造/服务"]},
    {"key": "bank", "keywords": ["银行", "商业银行"], "industries": ["银行"], "concepts": ["大金融"], "chain": ["银行信贷与财富管理"]},
    {"key": "broker", "keywords": ["证券", "券商", "资本市场服务"], "industries": ["证券"], "concepts": ["大金融", "资本市场"], "chain": ["经纪/投行/资管"]},
    {"key": "insurance", "keywords": ["保险", "保险服务"], "industries": ["保险"], "concepts": ["大金融"], "chain": ["保险与资产管理"]},
    {"key": "property_construction", "keywords": ["房地产", "建筑装饰", "基础建设", "房屋建设", "工程建设"], "industries": ["地产与建筑"], "concepts": ["稳增长", "地产链"], "chain": ["地产/建筑/基建"]},
    {"key": "building_materials", "keywords": ["建筑材料", "水泥", "玻璃玻纤", "装修建材", "非金属材料"], "industries": ["建筑材料"], "concepts": ["地产链", "基建"], "chain": ["建材"]},
    {"key": "chemicals", "keywords": ["基础化工", "化学原料", "化学制品", "农化制品", "塑料", "橡胶"], "industries": ["基础化工"], "concepts": ["周期化工"], "chain": ["化工原料与制品"]},
    {"key": "metals_mining", "keywords": ["有色金属", "工业金属", "贵金属", "小金属", "金属新材料", "矿业", "采矿"], "industries": ["有色金属与矿业"], "concepts": ["周期资源", "贵金属"], "chain": ["采矿/冶炼/加工"]},
    {"key": "coal_oil_gas", "keywords": ["煤炭", "石油石化", "油气开采", "天然气"], "industries": ["能源资源"], "concepts": ["能源价格", "周期资源"], "chain": ["煤炭/油气"]},
    {"key": "agriculture", "keywords": ["农林牧渔", "养殖业", "饲料", "种植业", "种业", "生猪", "农产品加工"], "industries": ["农业与养殖"], "concepts": ["农业", "猪周期", "粮食安全"], "chain": ["种植/饲料/养殖"]},
    {"key": "food_beverage", "keywords": ["食品饮料", "白酒", "食品加工", "饮料乳品", "调味发酵品"], "industries": ["食品饮料"], "concepts": ["大消费"], "chain": ["食品饮料消费"]},
    {"key": "retail_consumer", "keywords": ["商贸零售", "商业零售", "互联网电商", "免税", "专业连锁"], "industries": ["零售与电商"], "concepts": ["消费复苏", "平台经济"], "chain": ["零售渠道"]},
    {"key": "textile", "keywords": ["纺织服饰", "纺织制造", "服装家纺", "品牌服饰"], "industries": ["纺织服饰"], "concepts": ["出口链", "可选消费"], "chain": ["纺织与服装"]},
    {"key": "transport", "keywords": ["航运港口", "物流", "铁路公路", "航空机场", "航空运输", "快递"], "industries": ["交通运输"], "concepts": ["全球贸易", "运价周期"], "chain": ["航运/港口/物流/航空"]},
    {"key": "media", "keywords": ["传媒", "游戏", "影视院线", "出版", "广告营销"], "industries": ["传媒与游戏"], "concepts": ["内容消费"], "chain": ["内容生产与分发"]},
    {"key": "tourism", "keywords": ["社会服务", "旅游及景区", "酒店餐饮", "教育", "专业服务"], "industries": ["社会服务"], "concepts": ["服务消费"], "chain": ["旅游/酒店/专业服务"]},
    {"key": "environment", "keywords": ["环保", "水务", "环境治理", "固废治理"], "industries": ["环保公用"], "concepts": ["绿色发展", "碳中和"], "chain": ["环保与水务"]},
]


SECTOR_FAMILY_LABELS_CN: dict[str, str] = {
    "semiconductor": "半导体",
    "electronics": "电子元件与终端",
    "software": "软件与信息服务",
    "communications": "通信",
    "photovoltaic": "光伏",
    "battery": "动力电池",
    "energy_storage": "储能系统",
    "power_grid": "电力与电网",
    "automotive": "汽车",
    "home_appliance": "家用电器",
    "machinery": "机械设备",
    "defense": "国防军工",
    "medicine": "医药医疗",
    "bank": "银行",
    "broker": "证券",
    "insurance": "保险",
    "property_construction": "地产与建筑",
    "building_materials": "建筑材料",
    "chemicals": "基础化工",
    "metals_mining": "有色金属与矿业",
    "coal_oil_gas": "煤炭与油气",
    "agriculture": "农业与养殖",
    "food_beverage": "食品饮料",
    "retail_consumer": "零售与电商",
    "textile": "纺织服饰",
    "transport": "交通运输",
    "media": "传媒与游戏",
    "tourism": "旅游与社会服务",
    "environment": "环保公用",
}


SYMBOL_PROFILE_HINTS: dict[str, dict[str, list[str]]] = {
    "688146": {"industries": ["电子特种气体", "半导体材料", "化工新材料"], "concepts": ["半导体", "国产替代", "军工电子"], "chain": ["电子特气", "半导体制造材料"]},
    "300274": {"industries": ["光伏设备", "逆变器", "储能系统"], "concepts": ["光伏", "储能", "新能源"], "chain": ["逆变器", "储能系统"]},
    "300750": {"industries": ["动力电池", "储能系统", "新能源汽车"], "concepts": ["锂电池", "储能", "新能源车"], "chain": ["电池", "储能"]},
    "601012": {"industries": ["光伏设备", "硅片", "光伏组件"], "concepts": ["光伏", "新能源"], "chain": ["硅片", "组件"]},
    "600438": {"industries": ["硅料", "光伏", "饲料"], "concepts": ["光伏", "硅料", "农业"], "chain": ["硅料", "电池片", "饲料"]},
    "002594": {"industries": ["新能源汽车", "动力电池", "汽车电子"], "concepts": ["新能源车", "锂电池", "储能"], "chain": ["整车", "动力电池"]},
    "600519": {"industries": ["白酒", "食品饮料"], "concepts": ["大消费", "高端白酒"], "chain": ["白酒"]},
    "000001": {"industries": ["银行"], "concepts": ["大金融", "中特估"], "chain": ["商业银行"]},
    "300059": {"industries": ["证券", "金融信息服务"], "concepts": ["券商", "金融科技"], "chain": ["证券经纪", "基金销售"]},
    "159915": {"industries": ["创业板指数"], "concepts": ["ETF", "成长风格"], "chain": ["指数基金"]},
    "510300": {"industries": ["沪深300指数"], "concepts": ["ETF", "核心资产"], "chain": ["指数基金"]},
    "512100": {"industries": ["中证1000指数"], "concepts": ["ETF", "小盘风格"], "chain": ["指数基金"]},
}


COMPANY_PROFILE_HINTS: dict[str, dict[str, Any]] = {
    "中船特气": {
        "symbol": "688146",
        "name": "中船特气",
        "industries": ["电子特种气体", "半导体材料", "化工新材料"],
        "concepts": ["半导体", "国产替代", "军工电子"],
    },
    "宁德时代": {"symbol": "300750", "name": "宁德时代", "industries": ["动力电池", "储能系统"], "concepts": ["锂电池", "新能源车"]},
    "阳光电源": {"symbol": "300274", "name": "阳光电源", "industries": ["光伏设备", "逆变器", "储能系统"], "concepts": ["光伏", "储能"]},
    "Sungrow": {"symbol": "300274", "name": "阳光电源", "industries": ["光伏设备", "逆变器", "储能系统"], "concepts": ["光伏", "储能"]},
    "通威股份": {"symbol": "600438", "name": "通威股份", "industries": ["硅料", "光伏", "饲料"], "concepts": ["光伏", "农业"]},
    "贵州茅台": {"symbol": "600519", "name": "贵州茅台", "industries": ["白酒", "食品饮料"], "concepts": ["大消费"]},
    "平安银行": {"symbol": "000001", "name": "平安银行", "industries": ["银行"], "concepts": ["大金融"]},
}


def _as_words(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


class GlobalIndustryMapper:
    def coverage_catalog(self) -> dict[str, Any]:
        families = [str(rule.get("key") or "") for rule in PROFILE_SECTOR_RULES if rule.get("key")]
        industries = sorted({value for rule in PROFILE_SECTOR_RULES for value in rule.get("industries", [])})
        return {
            "sector_family_count": len(families),
            "event_rule_count": len(RULES),
            "sector_families": families,
            "sector_family_labels_cn": {key: SECTOR_FAMILY_LABELS_CN.get(key, key) for key in families},
            "industry_groups": industries,
            "scope_cn": "覆盖申万常见一级行业及新能源、半导体、AI、全球流动性等跨行业产业链",
            "truth_rule_cn": "只依据行情源行业、公司公告/画像或内置已核验画像分类；证据不足时返回未覆盖，不凭代码或新闻标题猜题材。",
        }

    def identify_issuers(self, text: str) -> list[dict[str, Any]]:
        """Identify explicit listed-company mentions without guessing from broad terms."""
        body = str(text or "")
        found: list[dict[str, Any]] = []
        for alias, profile in COMPANY_PROFILE_HINTS.items():
            symbol = str(profile.get("symbol") or "")
            if alias not in body and (not symbol or symbol not in body):
                continue
            found.append(dict(profile))
        return found

    def company_exposure(self, symbol: str, profile: dict[str, Any] | None = None, name: str = "") -> dict[str, Any]:
        profile = profile or {}
        base = dict(SYMBOL_PROFILE_HINTS.get(str(symbol), {}))
        primary_words: list[str] = []
        for key in ("industry", "market_industry", "main_business", "business_scope"):
            primary_words.extend(_as_words(profile.get(key)))
        product_words: list[str] = []
        for key in ("business_tags", "main_products", "business_segments", "tags"):
            product_words.extend(_as_words(profile.get(key)))
        # Upstream/downstream describe transmission paths, not the issuer's own
        # sector. They remain visible below but must never promote a supplier or
        # customer industry into a scoreable primary exposure.
        structured_words = primary_words + product_words
        structured_text = " ".join(structured_words).lower()
        industries = set(base.get("industries") or [])
        concepts = set(base.get("concepts") or [])
        chain = set(base.get("chain") or [])
        matched_sector_families: list[str] = []
        for rule in PROFILE_SECTOR_RULES:
            if any(keyword.lower() in structured_text for keyword in rule["keywords"]):
                industries.update(rule["industries"])
                concepts.update(rule["concepts"])
                chain.update(rule["chain"])
                matched_sector_families.append(rule["key"])
        has_structured_profile = bool(structured_words)
        confidence = "high" if has_structured_profile and matched_sector_families else "medium" if base else "low"
        basis = (
            "行情源行业+公司画像"
            if profile.get("market_industry") and has_structured_profile
            else "公司公告/结构化画像"
            if has_structured_profile
            else "内置已核验画像"
            if base
            else "画像缺失"
        )
        missing_reasons = [str(value) for value in (profile.get("missing_reasons") or []) if str(value).strip()]
        if confidence == "low" and not missing_reasons:
            missing_reasons = ["缺少可追溯行业或主营画像，当前不把宽泛名称匹配用于个股评分"]
        return {
            "symbol": symbol,
            "name": name or profile.get("name") or symbol,
            "main_business": profile.get("summary") or profile.get("main_business") or "公司公开画像不足，暂不扩展推断题材。",
            "industries": sorted(industries),
            "concepts": sorted(concepts),
            "chain_position": sorted(chain),
            "upstream": _as_words(profile.get("upstream")),
            "downstream": _as_words(profile.get("downstream")),
            "matched_rules": [],
            "matched_sector_families": list(dict.fromkeys(matched_sector_families)),
            "matched_sector_family_labels_cn": [
                SECTOR_FAMILY_LABELS_CN.get(key, key)
                for key in dict.fromkeys(matched_sector_families)
            ],
            "classification_confidence": confidence,
            "classification_basis_cn": basis,
            "profile_quality_status": profile.get("quality_status") or ("available" if has_structured_profile or base else "missing"),
            "profile_sources": list(dict.fromkeys(_as_words(profile.get("sources")))),
            "missing_reasons": missing_reasons,
            "coverage_catalog": self.coverage_catalog(),
            "classification_note": "全行业规则基于行情源行业、公司主营、产业链和结构化画像；名称或新闻关键词不能单独升级为可交易题材。",
        }

    def map_items(self, items: list[dict[str, Any]], symbol: str, name: str = "", profile: dict[str, Any] | None = None) -> dict[str, Any]:
        exposure = self.company_exposure(symbol, profile=profile, name=name)
        mapped = [self.map_item(item, symbol, exposure) for item in items or []]
        return {
            "company_exposure": exposure,
            "industry_mapped_items": mapped,
            "mapped_industries": sorted({value for item in mapped for value in item.get("mapped_industries", [])}),
            "mapped_concepts": sorted({value for item in mapped for value in item.get("mapped_concepts", [])}),
            "mapped_symbols": sorted({value for item in mapped for value in item.get("mapped_symbols", [])}),
            "related_count": len([item for item in mapped if item.get("included_in_score") or item.get("score_included")]),
            "direct_related_count": len([item for item in mapped if item.get("is_related_to_symbol")]),
            "early_warning_count": len([
                item for item in mapped
                if item.get("is_related_to_symbol") and item.get("confirmation_level") == "early_warning"
            ]),
        }

    def map_item(self, item: dict[str, Any], symbol: str, exposure: dict[str, Any]) -> dict[str, Any]:
        event_industries = {str(value) for value in (item.get("affected_industries_cn") or []) if str(value).strip()}
        text = " ".join(str(item.get(key) or "") for key in ("title", "summary", "content", "category")).lower()
        hit_rules = [rule for rule in RULES if any(keyword.lower() in text for keyword in rule["keywords"])]
        symbol_rules = [rule for rule in hit_rules if not bool(rule.get("market_wide"))]
        industries = sorted({value for rule in hit_rules for value in rule["industries"]} | event_industries)
        concepts = sorted({value for rule in hit_rules for value in rule["concepts"]})
        # Industry rules describe transmission paths, never a privileged stock
        # list. Direct-company relevance must come from the event payload or an
        # explicit company/code mention in the evidence text.
        structured_symbols: set[str] = set()
        for key in ("affected_symbols", "symbols"):
            structured_symbols.update(_as_words(item.get(key)))
        for key in ("issuer_symbol", "company_symbol", "security_code"):
            structured_symbols.update(_as_words(item.get(key)))
        structured_symbols.update(
            str(issuer.get("symbol") or "")
            for issuer in self.identify_issuers(text)
            if str(issuer.get("symbol") or "").strip()
        )
        symbols = sorted(structured_symbols)
        exposure_words = set(exposure.get("industries", []) + exposure.get("concepts", []) + exposure.get("chain_position", []))
        symbol_industries = {value for rule in symbol_rules for value in rule["industries"]} | event_industries
        symbol_concepts = {value for rule in symbol_rules for value in rule["concepts"]}
        event_words = symbol_industries | symbol_concepts
        overlap = exposure_words.intersection(event_words)
        for exposure_word in exposure_words:
            left = str(exposure_word).strip().lower()
            if len(left) < 2:
                continue
            for event_word in event_words:
                right = str(event_word).strip().lower()
                if len(right) >= 2 and (left in right or right in left):
                    overlap.add(str(event_word))
        explicit_name = str(exposure.get("name") or "").strip().lower()
        direct = symbol in symbols or symbol.lower() in text or (explicit_name and explicit_name != symbol.lower() and explicit_name in text)
        market_wide = any(bool(rule.get("market_wide")) for rule in hit_rules)
        rule_keys = [str(rule.get("key") or "") for rule in hit_rules]
        event_confirmed = (
            item.get("confirmation_level") in {"official_confirmed", "multi_source_confirmed"}
            and item.get("event_stage") not in {"rumor", "draft"}
        )
        event_specific = bool(item.get("event_type") and item.get("event_type") != "general_information")
        relevance = 18 if not hit_rules and not event_specific else 32 + len(hit_rules) * 10 + len(overlap) * 12 + (20 if direct else 0) + (5 if market_wide else 0) + (8 if event_confirmed else 0)
        relevance = max(0, min(100, relevance))
        positive_words = ["利好", "支持", "增长", "降息", "补贴", "中标", "需求上升", "回暖"]
        negative_words = [
            "利空", "下跌", "制裁", "风险", "收紧", "限制", "禁令", "国家紧急状态",
            "亏损", "下滑", "加息", "冲突", "ban", "restrict", "sanction", "prohibit",
            "national emergency", "security risk",
        ]
        event_direction = str(item.get("event_direction") or "")
        direction = (
            event_direction
            if event_direction in {"positive", "negative"}
            else "positive" if any(word in text for word in positive_words)
            else "negative" if any(word in text for word in negative_words)
            else "neutral"
        )
        reasons = [rule["reason"] for rule in hit_rules[:2]]
        if overlap:
            reasons.append(f"与当前标的产业暴露重合：{'、'.join(sorted(overlap))}。")
        elif market_wide:
            reasons.append("这是市场级宏观变量，只进入大盘环境分，不直接作为个股利多或利空。")
        elif not hit_rules:
            reasons.append("未命中当前标的行业、概念或产业链，不纳入个股评分。")
        elif not direct:
            reasons.append("事件虽命中其他行业，但与当前标的可追溯业务暴露不重合，不纳入个股评分。")
        # Market-wide liquidity/risk events belong to the market-regime score.
        # They enter an individual information score only when the text names
        # the company/security or also matches a non-market industry rule.
        event_scope = str(item.get("decision_scope") or "")
        profile_usable = str(exposure.get("classification_confidence") or "low") in {"high", "medium"}
        if event_specific:
            # A named foreign issuer or a single regulatory/product case is not
            # evidence against every A-share company in the same broad sector.
            # Industry overlap is scoreable only for an explicitly broad
            # industry event; issuer/case events require a direct company hit.
            included = bool(relevance >= 55 and (direct or (profile_usable and event_scope == "industry" and overlap)))
        else:
            included = bool(relevance >= 55 and (direct or (profile_usable and overlap)))
        score_included = bool(included and (not event_specific or event_confirmed))
        raw_sentiment = item.get("sentiment_score")
        try:
            mapped_sentiment = float(raw_sentiment) if raw_sentiment is not None else 50.0
        except (TypeError, ValueError):
            mapped_sentiment = 50.0
        if included and direction == "negative":
            mapped_sentiment = min(
                mapped_sentiment,
                22.0 if item.get("event_severity") == "high" and event_confirmed else 32.0 if event_confirmed else 40.0,
            )
        source_trade_gate = str(item.get("trade_gate") or "observe")
        mapped_trade_gate = (
            "block_new_position"
            if included and direction == "negative" and source_trade_gate == "candidate_block"
            else "manual_confirmation"
            if included and direction == "negative"
            else "observe"
        )
        item_id = item.get("id") or item.get("url") or item.get("title") or f"global-{symbol}-{abs(hash(text)) % 1_000_000}"
        return {
            **item,
            "global_item_id": str(item_id),
            "is_related_to_symbol": included,
            "mapped_industries": industries,
            "mapped_concepts": concepts,
            "mapped_symbols": symbols,
            "mapped_chain": sorted(overlap),
            "relevance_score": relevance,
            "impact_direction": direction,
            "base_sentiment_score": raw_sentiment,
            "sentiment_score": round(mapped_sentiment, 2),
            "mapping_adjustment_note": (
                f"{item.get('confirmation_level_cn') or '公开信息'}已映射到当前标的业务暴露；"
                f"事件阶段={item.get('event_stage_cn') or '待确认'}，交易用途={self._trade_gate_cn(mapped_trade_gate)}。"
                if included and event_specific
                else ""
            ),
            "impact_reason": " ".join(reasons),
            "included_in_score": score_included,
            "score_included": score_included,
            "market_wide": market_wide,
            "matched_rule_keys": rule_keys,
            "impact_scope_cn": "市场环境" if market_wide and not included else "个股产业链" if included else "背景信息",
            "transmission_chain": self._transmission_chain(rule_keys, bool(overlap or direct), market_wide, event_industries, item),
            "mapped_trade_gate": mapped_trade_gate,
            "mapped_trade_gate_cn": self._trade_gate_cn(mapped_trade_gate),
            "decision_scope": event_scope,
            "decision_scope_cn": item.get("decision_scope_cn"),
            "score_reliability": float(item.get("evidence_reliability") or 0.35),
        }

    @staticmethod
    def _transmission_chain(
        rule_keys: list[str],
        symbol_related: bool,
        market_wide: bool,
        event_industries: set[str] | None = None,
        item: dict[str, Any] | None = None,
    ) -> list[str]:
        chain: list[str] = []
        item = item or {}
        if "global_technology_risk" in rule_keys or "ai_semiconductor" in rule_keys:
            chain.extend(["海外科技/半导体风险偏好", "成长估值与外资情绪", "A股科技板块"])
        if "global_liquidity" in rule_keys:
            chain.extend(["海外利率与美元流动性", "估值折现/汇率", "A股市场环境"])
        if "large_ipo_liquidity" in rule_keys:
            chain.extend(["IPO申购与缴款", "短期资金占用", "A股流动性"])
        if "dram_memory_chain" in rule_keys and symbol_related:
            chain.extend(["DRAM供需与资本开支", "设备/材料/存储产业链", "公司业务暴露"])
        if "foreign_grid_equipment_restriction" in rule_keys and symbol_related:
            chain.extend(["美国电网设备准入/采购限制", "逆变器与储能系统海外订单及认证成本", "公司海外业务预期"])
        if symbol_related and event_industries and not chain:
            action = str(item.get("event_type_cn") or "政策/事件变化")
            chain.extend([
                action,
                f"{'、'.join(sorted(event_industries)[:3])}的准入、需求或成本",
                "公司相关业务与订单预期",
            ])
        if market_wide and not symbol_related and not chain:
            chain.append("市场级变量")
        return list(dict.fromkeys(chain))

    @staticmethod
    def _trade_gate_cn(value: str) -> str:
        return {
            "block_new_position": "阻断自动新增仓位",
            "manual_confirmation": "仅预警并要求人工核验",
            "observe": "仅观察，不触发交易",
        }.get(value, "仅观察，不触发交易")
