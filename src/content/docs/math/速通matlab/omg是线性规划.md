---
title: "omg是线性规划"
description: "这玩意接收七个参数，返回两个东西："
lastUpdated: 2026-05-12
---

# 新的东西

## `linprog`

这玩意接收七个参数，返回两个东西：

```MATLAB
[x, fval] = linprog(f, A, b, Aeq, beq, lb, ub);
```

它求的是 $\displaystyle \min f^T x$，其中 $f$ 是目标函数的系数，大概长这样

$$
f = [a_1,a_2,\cdots];
$$

也就是代表函数：

$$
f = a_1 x_1+a_2x_2+\cdots
$$

$x$ 代表最优解，就是要求的东西

同时它还要满足以下条件

$$
\begin{aligned} 
Ax &\leq b \\
A_{eq}x &= b_{eq} \\
lb \leq x &\leq ub
\end{aligned} 
$$

三个式子分别代表不等式约束、等式约束和变量上下界，如果不需要其中某个约束，填入`[]`就行了

返回的`x`和`fval`分别是最优解和最优函数匹配值

比如说如果要求

$$
\min Z = 2x_1+3x_2
$$

还有约束

$$
\begin{aligned} 
x_1 + x_2 &\geq 10 \\
x_1,x_2&\geq0
\end{aligned} 
$$

很容易发现`f = [2; 3]`，但是不等式约束的符号和函数要求不一样，于是就要两边乘 $-1$ 得到

$$
-x_1-x_2 \leq -10
$$
所以`A = [-1, -1]; b = -10;`

然后由于 $x_1,x_2\geq0$ ，于是下界`lb=zeros(2,1);`，这行代表生成一个 2 行 1 列的矩阵，里面都是 0

然后就可以这样求解了

```MATLAB
[x, fval] = linprog(f, A, b, [], [], lb, []);
```

## `intlinprog`

这个和上面那个大差不差，只是多接收了个参数，用来决定哪几个 $x$ 必须是整数

```MATLAB
[x, fval] = intlinprog(f, intcon, A, b, Aeq, beq, lb, ub);
```

`intcon`接收一个像`1:4`这样的区间，代表第 1 到 4 个 $x$ 都要是整数