# ✈ 悠享假期 — 旅行社ERP订单财务管理系统

> **Travel Agency Order & Financial Management ERP System**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)](https://www.sqlite.org/)
[![Bootstrap](https://img.shields.io/badge/UI-Native_CSS-orange.svg)]()

一个面向旅行社的**订单管理与财务核算系统**，支持多租户架构，涵盖订单全生命周期管理、客户关系管理、应收应付账款追踪、多维统计报表等核心业务功能。

---

## 📸 系统预览

| 模块 | 功能截图 |
|------|----------|
| 登录页 | CAPTCHA验证码 + 多租户隔离 |
| 系统首页 | 营收统计卡片 + 收支趋势图 + 实时订单流 |
| 订单管理 | 分页列表 + 多条件筛选 + 批量操作 |
| 订单详情 | 应收/已收/欠款一目了然 |
| 客户管理 | 1164+客户档案 + 订单关联 |
| 财务流水 | 收支分类统计 + 净利润核算 |
| 查欠款 | 客户欠款排名 + 催款依据 |
| 统计报表 | 订单状态分布 + 热门目的地 + 销售业绩排行 |

---

## 🎯 功能模块

### 业务管理
- **订单管理** — 新增 / 编辑 / 删除 / 查看，支持按订单号、客户、目的地、状态、付款状态多条件筛选
- **客户管理** — 客户档案维护，与订单自动关联，支持姓名/电话搜索

### 财务管理
- **财务流水** — 收支记录，分类统计，净利润实时计算
- **查欠款** — 客户欠款明细，逾期追踪
- **统计报表** — 订单状态分布、付款状态占比、热门目的地TOP10、月度收支趋势、销售业绩排名

### 资源管理
- **供应商管理** — 地接社/票务供应商信息维护
- **旅游产品库** — 线路产品管理与天数统计
- **员工管理** — 员工档案与登录记录
- **游客黑名单** — 风险游客管控

### 系统管理
- **用户管理** — 管理员/员工角色，密码重置
- **多租户** — 一套系统支持多个旅行社独立使用（`?ym=` 参数）
- **CAPTCHA验证** — 登录图形验证码

---

## 🏗 技术架构

```
├── app.py                 # Flask 应用主程序 (路由 + 业务逻辑)
├── data/
│   └── system.db          # SQLite 数据库 (自动创建)
├── templates/
│   ├── login.html         # 登录页面 (CAPTCHA)
│   ├── _sidebar.html      # 侧边栏导航组件
│   ├── dashboard.html     # 系统首页 / 仪表盘
│   ├── orders.html        # 订单列表
│   ├── order_form.html    # 订单表单
│   ├── order_view.html    # 订单详情
│   ├── customers.html     # 客户列表
│   ├── customer_form.html # 客户表单
│   ├── finances.html      # 财务流水
│   ├── debts.html         # 查欠款
│   ├── reports.html       # 统计报表
│   ├── suppliers.html     # 供应商管理
│   ├── products.html      # 旅游产品库
│   ├── employees.html     # 员工管理
│   ├── blacklist.html     # 游客黑名单
│   └── users.html         # 用户管理
└── static/
    ├── css/               # 样式文件
    └── js/                # JavaScript
```

**技术栈**：`Python` + `Flask` + `SQLite` + `原生CSS/JS`（无框架依赖）

**设计特点**：
- 服务端渲染 (SSR)，首屏加载快，SEO友好
- Session-based 认证，安全性高
- 数据库外键约束 + 唯一索引，数据完整性保障
- 多租户架构，数据完全隔离
- 响应式设计，PC/平板均可使用

---

## 🚀 快速开始

### 环境要求
- Python 3.10+
- pip

### 安装运行

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/travel-erp.git
cd travel-erp

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动系统
python app.py
```

浏览器打开 `http://localhost:5000`，使用默认账号登录：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin888 |
| 员工 | staff | 123456 |

---

## 📊 数据库设计

核心表结构（7张表，外键约束 + 索引优化）：

- `tenants` — 租户/公司信息
- `users` — 系统用户（角色：admin / staff）
- `orders` — 订单（关联客户，应收/已收/欠款）
- `customers` — 客户档案
- `finances` — 财务流水（收入/支出/应收）
- `suppliers` — 供应商
- `products` — 旅游产品
- `employees` — 员工

---

## 🔐 安全特性

- 密码 MD5 加密存储
- Session 会话管理 + 超时保护
- CAPTCHA 图形验证码防暴力破解
- SQL 参数化查询防注入
- 多租户数据隔离

---

## 📝 开发说明

本项目模拟真实旅行社业务场景，涵盖：
- 订单生命周期管理（待处理→已确认→进行中→已完成→已取消）
- 财务核算（应收/应付/已收/已付/利润计算）
- 客户关系管理（客户档案 + 订单历史）
- 业务报表（多维统计 + 数据可视化）

适合作为 **Python Flask 全栈项目**、**ERP系统参考**、**毕业设计** 或 **实习作品**。

---

## 📄 License

MIT License — 仅供学习参考，请勿直接用于商业用途。

---

*Built with ❤️ by [YYY_leh] — 2026
