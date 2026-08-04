---
title: "模块二：SQL编程、完整性约束与视图"
description: "AI 生成的数据库系统原理复习资料。"
---

这一部分对应开卷考核的**模块二，满分20分**。教材第3章系统讲解了SQL的数据定义、数据查询、数据更新和视图；第2章的完整性内容则决定了你的建表语句是否严谨。

考试不仅看你会不会写SQL，更看你是否能够把模块一的设计**真正建成可运行的数据库**。

---

## 1. 本模块任务拆解

| 任务 | 分值 | 要求 |
| --- | ---: | --- |
| DDL | 6 | 创建数据库与不少于3张表，覆盖三类完整性 |
| DML | 6 | 插入3条AI辅助生成数据，完成自定义更新与删除 |
| 多表查询 | 5 | 自定义5组查询，涉及2张及以上表，并覆盖指定复杂查询方式 |
| 视图 | 3 | 创建1个能简化高频复杂查询的视图 |

答题时建议把每条SQL前的“业务需求”先写出来，然后再贴代码和运行结果。这样不仅更清晰，也能体现你是在解决问题而不是堆代码。

---

## 2. SQL中的三类完整性

### 2.1 实体完整性：主键

主键唯一识别一条记录，不能重复，也不能为 `NULL`。

```sql
CustomerID INTEGER PRIMARY KEY
```

### 2.2 参照完整性：外键

外键保证相关数据真实存在。例如订单所属的客户必须先存在。

```sql
FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
```

### 2.3 用户自定义完整性：业务规则

业务规则可以由约束实现：

```sql
CustomerName VARCHAR(60) NOT NULL,
Phone VARCHAR(20) UNIQUE,
UnitPrice DECIMAL(10, 2) CHECK (UnitPrice >= 0),
Quantity INTEGER CHECK (Quantity > 0)
```

在报告中可以这样解释：

```text
主键体现实体完整性；外键体现参照完整性；非空、唯一和检查约束体现业务自定义完整性。
```

---

## 3. 可迁移的示例业务模型

由于正式业务场景在考试当天公布，下面用通用的订单结构演示SQL写法。现场需要将表名、字段名和查询要求替换成题目中的业务对象。

关系结构：

```text
Customer：客户
Product：商品
Orders：订单
OrderItem：订单明细，连接订单和商品
```

联系：

```text
Customer 1:N Orders
Orders M:N Product，通过OrderItem实现
```

---

## 4. DDL：创建数据库和数据表

### 4.1 创建数据库说明

在 MySQL 中可以直接执行：

```sql
CREATE DATABASE examdb;
USE examdb;
```

在 openGauss 中，通常先在可创建数据库的连接中执行：

```sql
CREATE DATABASE examdb;
```

随后连接到 `examdb` 再创建表。报告中应说明自己使用的是哪一种数据库环境。

### 4.2 创建数据表代码

以下表结构尽量采用 MySQL 与 openGauss 都容易调整的标准写法：

```sql
CREATE TABLE Customer (
    CustomerID INTEGER PRIMARY KEY,
    CustomerName VARCHAR(60) NOT NULL,
    Phone VARCHAR(20) NOT NULL UNIQUE,
    RegisterTime TIMESTAMP NOT NULL
);

CREATE TABLE Product (
    ProductID INTEGER PRIMARY KEY,
    ProductName VARCHAR(100) NOT NULL,
    CategoryName VARCHAR(50) NOT NULL,
    UnitPrice DECIMAL(10, 2) NOT NULL CHECK (UnitPrice >= 0),
    StockQuantity INTEGER NOT NULL CHECK (StockQuantity >= 0)
);

CREATE TABLE Orders (
    OrderID INTEGER PRIMARY KEY,
    CustomerID INTEGER NOT NULL,
    OrderTime TIMESTAMP NOT NULL,
    OrderStatus VARCHAR(20) NOT NULL
        CHECK (OrderStatus IN ('待支付', '已支付', '已取消', '已完成')),
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
);

CREATE TABLE OrderItem (
    OrderID INTEGER NOT NULL,
    ProductID INTEGER NOT NULL,
    Quantity INTEGER NOT NULL CHECK (Quantity > 0),
    DealPrice DECIMAL(10, 2) NOT NULL CHECK (DealPrice >= 0),
    PRIMARY KEY (OrderID, ProductID),
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
);
```

### 4.3 如何在报告中解释约束

| 代码位置 | 约束类型 | 解释 |
| --- | --- | --- |
| `CustomerID PRIMARY KEY` | 实体完整性 | 客户编号唯一且不能为空 |
| `Orders.CustomerID` 外键 | 参照完整性 | 每个订单必须属于已存在客户 |
| `Phone UNIQUE` | 用户自定义完整性 | 一个手机号不能重复注册 |
| `UnitPrice CHECK` | 用户自定义完整性 | 商品价格不能为负数 |
| `OrderStatus CHECK` | 用户自定义完整性 | 状态必须处于规定范围内 |
| `OrderItem` 联合主键 | 实体完整性 | 同一订单中的同一商品只保留一条明细 |

---

## 5. DML：插入、更新和删除

### 5.1 插入基础关联数据

外键表的插入有先后顺序：

```text
先插入Customer和Product，再插入Orders，最后插入OrderItem。
```

```sql
INSERT INTO Customer (CustomerID, CustomerName, Phone, RegisterTime) VALUES
(1, '张晨', '13800000001', '2026-05-01 09:00:00'),
(2, '李宁', '13800000002', '2026-05-02 10:30:00'),
(3, '王悦', '13800000003', '2026-05-03 14:10:00');

INSERT INTO Product (ProductID, ProductName, CategoryName, UnitPrice, StockQuantity) VALUES
(101, '数据库原理教材', '图书', 59.00, 20),
(102, '便携笔记本', '文具', 12.50, 80),
(103, 'SQL练习册', '图书', 28.00, 35);

INSERT INTO Orders (OrderID, CustomerID, OrderTime, OrderStatus) VALUES
(1001, 1, '2026-05-10 09:20:00', '已支付'),
(1002, 2, '2026-05-11 16:10:00', '待支付'),
(1003, 1, '2026-05-12 12:00:00', '已完成');

INSERT INTO OrderItem (OrderID, ProductID, Quantity, DealPrice) VALUES
(1001, 101, 1, 59.00),
(1001, 102, 2, 12.50),
(1002, 103, 1, 28.00),
(1003, 101, 1, 55.00);
```

考核要求中提到，可以选择一张表使用AI工具批量生成3条插入数据。报告中可以标记：

```text
Product表中的三条样例数据由AI辅助生成基础文本，本人根据字段约束检查价格和库存范围，并在数据库中实际运行验证。
```

不要只写这句话而不执行SQL。运行结果截图才是有效证据。

### 5.2 自定义更新要求与SQL

业务要求示例：

```text
将“便携笔记本”的库存增加20件。
```

```sql
UPDATE Product
SET StockQuantity = StockQuantity + 20
WHERE ProductID = 102;
```

业务要求示例：

```text
将订单1002的状态从待支付更新为已支付。
```

```sql
UPDATE Orders
SET OrderStatus = '已支付'
WHERE OrderID = 1002
  AND OrderStatus = '待支付';
```

更新后应执行查询并截图：

```sql
SELECT * FROM Product WHERE ProductID = 102;
SELECT * FROM Orders WHERE OrderID = 1002;
```

### 5.3 自定义删除要求与SQL

删除必须注意外键约束。若某订单已有明细，直接删除订单会失败，这是参照完整性在保护数据。

业务要求示例：

```text
删除尚未产生任何订单明细的无效订单。
```

```sql
DELETE FROM Orders
WHERE OrderID = 1004
  AND NOT EXISTS (
      SELECT 1
      FROM OrderItem
      WHERE OrderItem.OrderID = Orders.OrderID
  );
```

如果确实需要删除已有明细的订单，应按照业务规则先删除从表明细，再删除主表订单，并在报告中解释原因。

---

## 6. 五组多表查询设计

教材中的SQL查询部分强调，SQL可以通过连接、嵌套查询和分组统计表达实际业务问题。考核要求的查询必须涉及2张及以上表，因此不要提交仅对单表进行筛选的语句。

### 查询一：`JOIN` 与 `LIKE`

业务要求：

```text
查询购买过名称中含“数据库”的商品的客户姓名、商品名称和订单编号。
```

```sql
SELECT c.CustomerName, p.ProductName, o.OrderID
FROM Customer c
JOIN Orders o ON c.CustomerID = o.CustomerID
JOIN OrderItem oi ON o.OrderID = oi.OrderID
JOIN Product p ON oi.ProductID = p.ProductID
WHERE p.ProductName LIKE '%数据库%';
```

知识点：

```text
多表内连接；LIKE模糊匹配；字段名前使用表别名避免重名。
```

### 查询二：`IN` 子查询

业务要求：

```text
查询至少购买过“图书”分类商品的客户信息。
```

```sql
SELECT CustomerID, CustomerName, Phone
FROM Customer
WHERE CustomerID IN (
    SELECT o.CustomerID
    FROM Orders o
    JOIN OrderItem oi ON o.OrderID = oi.OrderID
    JOIN Product p ON oi.ProductID = p.ProductID
    WHERE p.CategoryName = '图书'
);
```

知识点：

```text
子查询先得到满足条件的客户编号集合，外层查询再显示客户信息。
```

### 查询三：`GROUP BY` 与聚合统计

业务要求：

```text
统计每位客户已支付或已完成订单的消费总金额。
```

```sql
SELECT c.CustomerID,
       c.CustomerName,
       SUM(oi.Quantity * oi.DealPrice) AS TotalAmount
FROM Customer c
JOIN Orders o ON c.CustomerID = o.CustomerID
JOIN OrderItem oi ON o.OrderID = oi.OrderID
WHERE o.OrderStatus IN ('已支付', '已完成')
GROUP BY c.CustomerID, c.CustomerName;
```

知识点：

```text
IN用于多个状态条件；SUM用于统计；GROUP BY按客户分组。
```

### 查询四：`GROUP BY` 与 `HAVING`

业务要求：

```text
查询累计销售数量不少于2件的商品及其销售数量。
```

```sql
SELECT p.ProductID,
       p.ProductName,
       SUM(oi.Quantity) AS SoldQuantity
FROM Product p
JOIN OrderItem oi ON p.ProductID = oi.ProductID
JOIN Orders o ON oi.OrderID = o.OrderID
WHERE o.OrderStatus <> '已取消'
GROUP BY p.ProductID, p.ProductName
HAVING SUM(oi.Quantity) >= 2;
```

区别要记住：

```text
WHERE：分组前筛选行。
HAVING：分组后筛选统计结果。
```

### 查询五：左连接检查业务缺口

业务要求：

```text
查询还没有下过订单的客户，用于后续服务提醒。
```

```sql
SELECT c.CustomerID, c.CustomerName
FROM Customer c
LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
WHERE o.OrderID IS NULL;
```

知识点：

```text
LEFT JOIN会保留左表全部客户；没有匹配订单的行，其订单编号为NULL。
```

---

## 7. 视图设计

### 7.1 为什么创建视图

视图是基于查询定义的虚表。它本身通常不重复存储全部业务数据，而是把复杂查询包装成一个易用的查询入口。

适合创建视图的场景：

```text
一个复杂统计查询需要经常执行。
普通角色只需要看到部分字段，而不能看到敏感字段。
希望统一统计口径，避免每次重写多表连接。
```

### 7.2 创建订单汇总视图

业务要求：

```text
创建一个视图，展示每笔订单的客户、状态和总金额，供管理员快速查询。
```

```sql
CREATE VIEW V_OrderSummary AS
SELECT o.OrderID,
       c.CustomerName,
       o.OrderTime,
       o.OrderStatus,
       SUM(oi.Quantity * oi.DealPrice) AS TotalAmount
FROM Orders o
JOIN Customer c ON o.CustomerID = c.CustomerID
JOIN OrderItem oi ON o.OrderID = oi.OrderID
GROUP BY o.OrderID, c.CustomerName, o.OrderTime, o.OrderStatus;
```

使用视图：

```sql
SELECT *
FROM V_OrderSummary
WHERE OrderStatus = '已支付';
```

报告说明可写为：

```text
该视图封装了订单、客户和订单明细之间的多表连接及金额汇总逻辑，能够减少高频查询中的重复代码，并为后续按订单状态进行统计提供统一数据入口。
```

---

## 8. SQL运行截图应包含什么

建议每类操作保存至少一组清楚截图：

| 截图类型 | 应显示内容 |
| --- | --- |
| 表创建 | 建表语句成功执行或表结构查询结果 |
| 插入数据 | `SELECT` 显示插入后的记录 |
| 更新、删除 | 执行前后的关键结果或影响行数 |
| 五组查询 | 中文业务要求、SQL语句、返回结果 |
| 视图 | `CREATE VIEW` 成功，以及查询视图结果 |

如果截图中出现运行错误，应写明：

```text
错误现象是什么；
原因是什么，例如外键引用的数据不存在、字段名写错或分组字段遗漏；
如何修改后成功运行。
```

---

## 9. 常见失分点

| 问题 | 后果 | 改进 |
| --- | --- | --- |
| 建了3张表但没有外键 | 未体现参照完整性 | 给业务联系添加正确外键 |
| 五条查询都是单表查询 | 不符合考核要求 | 至少连接两张表 |
| 只使用 `SELECT *` | 不能体现查询设计 | 按业务显示必要字段并加入条件 |
| `GROUP BY` 统计结果不合理 | 业务含义错误 | 用测试数据核验计算结果 |
| 视图只是单表查询 | 简化价值弱 | 封装多表连接或统计查询 |
| 只贴AI代码不运行 | 违反要求且无法证明正确 | 自己修改、调试并截图 |

---

## 10. 本模块快速背诵版

```text
DDL用于定义数据库结构，包括创建数据库、表和约束；DML用于插入、更新和删除数据；SELECT用于数据查询；VIEW用于封装常用查询。

实体完整性通过PRIMARY KEY实现，参照完整性通过FOREIGN KEY实现，用户自定义完整性通过NOT NULL、UNIQUE、CHECK等约束实现。

多表查询常用JOIN连接相关表，LIKE进行模糊匹配，IN表达集合条件，GROUP BY进行分组统计，HAVING筛选分组后的统计结果。

考试中SQL必须实际运行，并提供结果截图；AI辅助数据或代码必须经过本人设计、修改和验证。
```
