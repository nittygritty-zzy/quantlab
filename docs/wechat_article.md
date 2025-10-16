# 🚀 开源了！一款专业级量化交易研究平台 QuantLab

## 为什么要做这个项目？

你是否遇到过这些痛点：

📊 **数据分散**：股票数据在一个平台，期权数据在另一个平台，基本面数据又在第三方...

💰 **成本高昂**：Bloomberg Terminal 每年 $24,000+，专业分析工具动辄上万...

🔧 **工具割裂**：投资组合管理用 Excel，回测用 Python 脚本，实时分析靠手动...

⏰ **效率低下**：每天手动查询数据、计算指标、更新报表...

**今天，这些问题都有解决方案了！**

## 🎯 QuantLab 是什么？

QuantLab 是一个**完全开源**的量化交易研究平台，集成了：

### 核心功能

✅ **投资组合管理** - 专业级组合管理 CLI
✅ **多源数据整合** - Polygon、yfinance、Alpha Vantage
✅ **期权深度分析** - 完整的 Greeks 计算和策略分析
✅ **量化回测引擎** - 集成 Microsoft Qlib 框架
✅ **高性能存储** - DuckDB 实现秒级查询
✅ **完整测试覆盖** - 154 个测试用例保证质量

**GitHub 开源地址**：`https://github.com/nittygritty-zzy/quantlab`

---

## 💼 十大实战场景

### 场景一：构建科技股投资组合

想构建一个 FAANG+ 科技股组合？只需几行命令：

```bash
# 初始化 QuantLab
quantlab init

# 创建科技股组合
quantlab portfolio create tech_giants \
    --name "FAANG+ Portfolio" \
    --description "大型科技公司"

# 添加持仓（自动分配权重）
quantlab portfolio add tech_giants AAPL GOOGL MSFT --weight 0.20
quantlab portfolio add tech_giants META AMZN --weight 0.15
quantlab portfolio add tech_giants NVDA --weight 0.10

# 查看组合
quantlab portfolio show tech_giants
```

**输出效果**：
```
📊 Portfolio: FAANG+ Portfolio
📈 Positions: 6
├─ AAPL    │ Weight: 20.00%
├─ GOOGL   │ Weight: 20.00%
├─ MSFT    │ Weight: 20.00%
├─ META    │ Weight: 15.00%
├─ AMZN    │ Weight: 15.00%
└─ NVDA    │ Weight: 10.00%
Total Weight: 100.00%
```

---

### 场景二：追踪实际持仓

记录真实交易数据，包括成本价和份额：

```bash
# 更新持仓（含成本价和份额）
quantlab portfolio update tech_giants AAPL \
    --shares 50 \
    --cost-basis 178.25 \
    --notes "Q4 回调时买入"

quantlab portfolio update tech_giants GOOGL \
    --shares 30 \
    --cost-basis 142.50 \
    --notes "财报后入场"

# 查看更新后的组合
quantlab portfolio show tech_giants
```

**效果**：自动计算总投资额、持仓价值、盈亏情况！

---

### 场景三：深度分析一只股票

在买入 ORCL（甲骨文）之前，做全方位分析：

```bash
# 综合分析（基本面 + 期权 + 情绪 + 技术面）
quantlab analyze ticker ORCL \
    --include-fundamentals \
    --include-options \
    --include-sentiment \
    --include-technicals \
    --output results/orcl_analysis.json
```

**分析报告包含**：

📈 **价格信息**
- 当前价：$145.50
- 涨跌：+2.3% ($3.25)
- 成交量：5,234,567

💰 **基本面数据**
- 市值：$401.2B
- 市盈率：28.5
- 远期市盈率：21.2
- 营收增长：7.2%
- 利润率：21.5%
- 负债率：2.84

📊 **期权活跃度**
- 看跌/看涨比率：0.78（看涨）
- 隐含波动率：22.5%
- 下次财报：2025-03-15（30 天后）

📰 **情绪分析**
- 情绪得分：0.72（积极）
- 文章数：45（7 天内）
- 热度：高

🎯 **分析师共识**
- 评级：买入(12) / 持有(8) / 卖出(2)
- 目标价：$165.00（+13.4%）

---

### 场景四：组合全面分析

分析整个投资组合的健康状况：

```bash
quantlab analyze portfolio tech_giants \
    --include-options \
    --aggregate-metrics \
    --output results/tech_giants_analysis.json
```

**输出示例**：
```
📊 分析组合：FAANG+ Portfolio（6 个持仓）

个股分析：
✓ AAPL  │ 评分: 82/100 │ 情绪: 积极 │ 分析师: 85% 买入
✓ GOOGL │ 评分: 78/100 │ 情绪: 积极 │ 分析师: 80% 买入
✓ MSFT  │ 评分: 88/100 │ 情绪: 非常积极 │ 分析师: 90% 买入
✓ META  │ 评分: 75/100 │ 情绪: 中性 │ 分析师: 75% 买入
✓ AMZN  │ 评分: 81/100 │ 情绪: 积极 │ 分析师: 82% 买入
⚠ NVDA  │ 评分: 68/100 │ 情绪: 混合 │ 分析师: 70% 买入

组合指标：
总价值：$52,450
平均市盈率：32.5
平均情绪：0.68（积极）
组合 Beta：1.15
加权分析师评级：80% 买入

⚠️ 警报：
- NVDA 显示疲软（考虑减仓）
- MSFT 表现最强（98% 分析师看好）
```

---

### 场景五：历史数据查询

研究历史价格模式用于回测：

```bash
# 查询多只股票的历史数据
quantlab data query AAPL GOOGL MSFT \
    --start 2024-01-01 \
    --end 2025-01-15 \
    --type stocks_daily \
    --limit 100

# 检查数据覆盖范围
quantlab data check
```

**数据覆盖**：
```
📁 Parquet 数据可用性
✓ stocks_daily    │ 13,187 只股票 │ 2024-09-01 至 2025-10-15（442 天）
✓ stocks_minute   │ 8,523 只股票  │ 最近 90 天
✓ options_daily   │ 3,245 只股票  │ 2024-09-01 至 2025-10-15
✗ options_minute  │ 不可用
```

---

### 场景六：期权策略研究

研究 AAPL 的备兑看涨期权（Covered Call）机会：

```bash
quantlab analyze ticker AAPL \
    --include-options \
    --no-fundamentals \
    --no-sentiment \
    --output results/aapl_options.json
```

**期权分析**：
```
🔍 期权分析：AAPL
当前价格：$181.75

近期到期（30 天）：
看涨期权（备兑看涨候选）：
行权价 │ 权利金 │ IV    │ Delta │ 盈亏平衡 │ 收益率
$185   │ $3.85  │ 21.2% │ 0.45  │ $185.00  │ 2.1%
$190   │ $2.15  │ 19.8% │ 0.28  │ $190.00  │ 4.6%
$195   │ $0.95  │ 18.5% │ 0.15  │ $195.00  │ 7.3%

看跌期权（现金担保看跌候选）：
行权价 │ 权利金 │ IV    │ Delta │ 净成本   │ 收益率
$175   │ $2.80  │ 22.5% │ -0.35 │ $172.20  │ 1.6%
$170   │ $1.45  │ 20.1% │ -0.20 │ $168.55  │ 0.9%

波动率指标：
当前 IV：21.2%
历史波动率（30 天）：18.5%
IV 百分位：62%（偏高）

💡 建议：适合卖出权利金的条件
   IV 高于历史水平 - 考虑在 $190 行权价卖出看涨期权
```

---

### 场景七：多策略组合管理

同时管理成长、价值、股息三种策略：

```bash
# 创建不同策略的组合
quantlab portfolio create growth \
    --name "高成长股" \
    --description "市盈率 > 30 的成长股"

quantlab portfolio create value \
    --name "价值股" \
    --description "市盈率 < 15 的低估股"

quantlab portfolio create dividend \
    --name "股息收入" \
    --description "高股息率股票"

# 添加对应股票
quantlab portfolio add growth NVDA TSLA SNOW --weight 0.33
quantlab portfolio add value BAC JPM WFC --weight 0.33
quantlab portfolio add dividend T VZ SO --weight 0.33

# 查看所有组合
quantlab portfolio list
```

**输出**：
```
📊 您的投资组合

组合 ID       │ 名称        │ 持仓数 │ 总权重   │ 最后更新
─────────────┼─────────────┼────────┼──────────┼─────────
tech_giants  │ FAANG+      │ 6      │ 100.00%  │ 2025-10-15
growth       │ 高成长股    │ 3      │ 99.00%   │ 2025-10-15
value        │ 价值股      │ 3      │ 99.00%   │ 2025-10-15
dividend     │ 股息收入    │ 3      │ 99.00%   │ 2025-10-15

总组合数：4
总持仓数（去重）：15
```

---

### 场景八：每月组合审查

标准化的月度审查流程：

```bash
# 步骤 1：刷新市场数据
quantlab lookup refresh portfolio tech_giants

# 步骤 2：获取综合分析
quantlab analyze portfolio tech_giants --aggregate-metrics

# 步骤 3：检查再平衡需求
quantlab portfolio show tech_giants

# 步骤 4：寻找新机会
quantlab data tickers --type stocks_daily | grep -E "^[A-Z]{1,4}$" | head -20
quantlab analyze ticker CRM --include-fundamentals

# 步骤 5：基于分析更新持仓
quantlab portfolio update tech_giants NVDA --weight 0.05 \
    --notes "减仓 - 估值担忧"

quantlab portfolio add tech_giants CRM --weight 0.05 \
    --notes "新仓位 - 云计算增长"

# 步骤 6：导出记录
quantlab analyze portfolio tech_giants \
    --output results/monthly_review_2025_10.json
```

---

### 场景九：风险监控脚本

创建每日自动监控脚本：

```bash
# 创建监控脚本
cat > scripts/daily_monitor.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d)

echo "🔍 每日组合监控 - $DATE"
echo "=================================="

# 分析每个组合
for portfolio in tech_giants growth value dividend; do
    echo ""
    echo "📊 组合：$portfolio"
    quantlab analyze portfolio $portfolio \
        --include-options \
        --output "results/monitoring/${portfolio}_${DATE}.json" 2>&1 | \
        grep -E "(Score:|Sentiment:|Analysts:|⚠|❌)"
done

# 检查国债利率（无风险利率）
echo ""
echo "📈 当前国债利率："
quantlab lookup get treasury 10y

echo ""
echo "✅ 监控完成"
EOF

chmod +x scripts/daily_monitor.sh

# 运行监控
./scripts/daily_monitor.sh
```

---

### 场景十：量化回测研究

使用 Microsoft Qlib 框架进行专业回测：

```bash
# 运行 LightGBM 策略回测（流动性股票池）
cd qlib_repo/examples
uv run qrun ../../configs/lightgbm_liquid_universe.yaml

# 结果可视化
uv run python ../../scripts/analysis/visualize_results.py
```

**回测结果示例**：
```
📊 回测结果

配置：Liquid Universe
股票池：13,187 只（过滤后）
周期：2024-09-01 至 2025-10-15

关键指标：
IC（信息系数）：0.066
Rank IC：-0.006
夏普比率：3.94
最大回撤：-39.2%
年化收益：+45.8%

✅ IC > 0.06 表示良好的预测能力
✅ 夏普比率 > 3 表示优秀的风险调整收益
```

---

## 🏗️ 技术架构

### 核心技术栈

**后端框架**：
- Python 3.12+
- Click（CLI 框架）
- DuckDB（高性能数据库）
- Microsoft Qlib（量化回测）

**数据源**：
- Polygon.io（实时和历史数据）
- yfinance（Yahoo Finance）
- Alpha Vantage（基本面数据）

**分析工具**：
- Pandas / NumPy（数据处理）
- SciPy（科学计算）
- 自研 Greeks 计算器（期权分析）

### 项目结构

```
quantlab/
├── quantlab/              # 核心库
│   ├── cli/              # CLI 命令
│   ├── core/             # 核心逻辑
│   ├── data/             # 数据层
│   ├── analysis/         # 分析工具
│   └── backtest/         # 回测引擎
├── tests/                # 测试（154 个）
│   ├── cli/             # 单元测试（122 个）
│   └── integration/     # 集成测试（32 个）
├── configs/              # 回测配置（16+）
├── docs/                 # 文档（50+）
└── scripts/              # 实用脚本
```

---

## 📊 测试覆盖率

**全面的测试保证质量**：

✅ **154 个测试用例**
✅ **0.93 秒**完成全部测试
✅ **100% 通过率**

**测试分类**：
- **122 个单元测试**：使用 Mock 快速测试
- **32 个集成测试**：真实组件测试

**覆盖范围**：
- 19 个 CLI 命令
- 完整的组合生命周期
- 数据库持久化
- 错误处理
- 边界条件

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/nittygritty-zzy/quantlab.git
cd quantlab

# 安装依赖（使用 uv）
uv venv
source .venv/bin/activate
uv sync

# 安装 QuantLab
uv pip install -e .

# 初始化
quantlab init
```

### 配置 API 密钥

编辑 `~/.quantlab/config.yaml`：

```yaml
api_keys:
  polygon: "your_polygon_api_key"
  alphavantage: "your_alphavantage_api_key"

database:
  path: "~/.quantlab/quantlab.duckdb"

data_paths:
  parquet_root: "/path/to/your/data"
```

### 第一个命令

```bash
# 查看帮助
quantlab --help

# 创建你的第一个组合
quantlab portfolio create my_first --name "我的第一个组合"

# 添加几只股票
quantlab portfolio add my_first AAPL MSFT GOOGL

# 查看组合
quantlab portfolio show my_first
```

---

## 💡 适用人群

### 个人投资者
- 管理个人投资组合
- 分析股票和期权
- 学习量化投资

### 量化研究员
- 策略回测和优化
- 多因子研究
- Alpha 挖掘

### 金融学生
- 学习量化金融
- 实践投资策略
- 研究市场数据

### 开发者
- 构建金融应用
- 集成数据源
- 扩展功能

---

## 🎁 项目亮点

### 1. 完全开源免费
- MIT 协议
- 无隐藏费用
- 社区驱动

### 2. 专业级质量
- 154 个测试用例
- 完整文档
- 生产就绪

### 3. 易于扩展
- 模块化设计
- 清晰的 API
- 插件式架构

### 4. 多数据源整合
- Polygon.io
- yfinance
- Alpha Vantage
- 可自定义添加

### 5. 高性能
- DuckDB 秒级查询
- 优化的数据结构
- 并行处理

---

## 📈 回测性能

**已验证的策略配置**：

| 策略 | IC | Rank IC | 夏普比率 | 最大回撤 |
|------|----|---------|---------:|-------:|
| Liquid Universe | 0.066 | -0.006 | 3.94 | -39.2% |
| Fixed Dates | 0.079 | -0.008 | 4.54 | -35.3% |
| Full Universe | 0.080 | -0.004 | 2.98 | -41.7% |

**IC > 0.06** = 优秀的预测能力
**夏普比率 > 2** = 良好的风险调整收益

---

## 🛠️ 未来规划

### 近期计划（Q1 2025）
- [ ] 添加更多技术指标
- [ ] 支持加密货币数据
- [ ] Web UI 界面
- [ ] 实时行情推送

### 中期计划（Q2-Q3 2025）
- [ ] 机器学习模型集成
- [ ] 多账户管理
- [ ] 自动化交易接口
- [ ] 移动端应用

### 长期愿景
- 打造中文量化社区首选平台
- 建立策略分享生态
- 提供云端回测服务

---

## 🤝 如何参与

### 贡献代码
```bash
# Fork 仓库
# 创建特性分支
git checkout -b feature/amazing-feature

# 提交更改
git commit -m "Add amazing feature"

# 推送到分支
git push origin feature/amazing-feature

# 创建 Pull Request
```

### 报告问题
- 访问 [GitHub Issues](https://github.com/nittygritty-zzy/quantlab/issues)
- 详细描述问题
- 提供复现步骤

### 分享想法
- 在 Issues 中讨论新功能
- 分享你的使用经验
- 帮助其他用户

---

## 📚 学习资源

### 文档
- **快速开始**：`QUICKSTART.md`
- **CLI 指南**：`QUICKSTART_CLI.md`
- **项目结构**：`PROJECT_STRUCTURE.md`
- **API 文档**：`docs/`

### 教程
- 投资组合管理完整指南
- 期权策略实战案例
- 量化回测入门
- 数据源对接教程

### 示例代码
- `scripts/analysis/` - 分析脚本示例
- `tests/` - 测试用例参考
- `configs/` - 回测配置示例

---

## ⚖️ 免责声明

⚠️ **重要提示**：

本项目仅供**研究和教育目的**使用。

- ❌ 不构成投资建议
- ❌ 不保证收益
- ❌ 投资有风险，入市需谨慎

使用本软件进行实际交易的风险由用户自行承担。作者和贡献者不对任何财务损失负责。

---

## 🔗 相关链接

**项目资源**：
- 🌐 GitHub：`https://github.com/nittygritty-zzy/quantlab`
- 📖 在线文档：（即将推出）
- 💬 社区讨论：（即将推出）

**依赖项目**：
- [Microsoft Qlib](https://github.com/microsoft/qlib) - 量化投资框架
- [DuckDB](https://duckdb.org/) - 高性能分析数据库
- [Click](https://click.palletsprojects.com/) - Python CLI 框架

**数据提供商**：
- [Polygon.io](https://polygon.io/) - 实时和历史市场数据
- [Yahoo Finance](https://finance.yahoo.com/) - 免费市场数据
- [Alpha Vantage](https://www.alphavantage.co/) - 金融 API

---

## 👨‍💻 关于作者

**nittygritty-zzy**

一名热爱量化投资的开发者，希望通过开源项目降低量化交易的门槛，让更多人能够使用专业级的投资分析工具。

---

## 🎉 加入我们

如果你对量化投资感兴趣，欢迎：

⭐ **Star** 项目 - 支持开源
🍴 **Fork** 项目 - 定制开发
👀 **Watch** 项目 - 关注更新
💬 **提交 Issue** - 反馈问题
🤝 **Pull Request** - 贡献代码

---

## 📣 最后的话

在这个算法交易和机器学习主导的时代，个人投资者也应该拥有专业级的工具。

**QuantLab 的使命**：让量化投资不再是机构的专利，让每个人都能使用数据驱动的投资决策。

这不是终点，而是起点。

让我们一起，用代码改变投资的方式！

---

**立即开始你的量化投资之旅**：

```bash
git clone https://github.com/nittygritty-zzy/quantlab.git
cd quantlab
uv sync
quantlab init
```

**让数据说话，让策略经得起时间的检验！** 📈

---

## 📱 关注我们

持续更新中...

下期预告：《QuantLab 实战：从零开始构建量化选股策略》

---

*本文由 QuantLab 官方发布*
*GitHub: https://github.com/nittygritty-zzy/quantlab*
*发布日期: 2025年10月15日*

---

**#量化投资 #开源项目 #Python #金融科技 #投资组合管理 #期权交易 #算法交易 #数据分析**
