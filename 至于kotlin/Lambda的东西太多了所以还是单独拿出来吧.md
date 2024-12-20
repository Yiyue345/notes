---
tags:
  - kotlin
---
### 有关Lambda（匿名函数

Lambda 表达式的写法是`{ 参数 -> 表达式 }`，用来在需要函数当参数或者返回值的时候传递代码块，而且不用特地标明返回值的类型~~GPT你说得好抽象~~

##### 基本而言用法是

```kotlin
val sum = { x: Int, y: Int -> x + y }
println(sum(3, 4)) // 输出 7
```

在这里的`sum`属于一个 Lambda 表达式，可以求和

> 让我们把这些元素组合起来！

##### 和那些集合相关的API组合起来就能得到许多匪夷所思的写法

```kotlin
val numbers = listOf(1, 2, 3, 4, 5)
val evens = numbers.filter { it % 2 == 0 }
println(evens) // 输出 [2, 4]
```

好吧，这里至少能看出来`{ it % 2 == 0 }`是`filter`的参数

##### 那下面这一串是啥……

```kotlin
fun operateOnNumbers(a: Int, b: Int, operation: (Int, Int) -> Int): Int {
    return operation(a, b)
}
val result = operateOnNumbers(3, 4) { x, y -> x * y }
println(result) // 输出 12
```

看得出来，这个函数有三个参数`a, b, operation`，`operation`是个接收两个参数返回一个Int的函数（Lambda 表达式）

下面的`result`则是接受了三个参数的这个函数的返回值（是的那一串`{ x, y -> x * y }`是一个参数，在这个情况下决定了a和b的运算方式）

##### 既然能作为参数，那为什么不可以作为返回值呢

```kotlin
fun getMultiplier(factor: Int): (Int) -> Int {
    return { number -> number * factor }
}
val double = getMultiplier(2)
println(double(5)) // 输出 10
```

在这个函数里边接收一个参数`factor`，返回一个接收一个`Int`返回一个`Int`的Lambda 表达式

`double`被赋值之后就是`getMultiplier`的返回值，即 `{ number -> number * 2 }`，于是便能再接收一个`Int`类型的参数

##### Lambda还能直接访问接收者的属性和方法

最经典的就是在合成`ContentValues`的时候

```kotlin
val values = ContentValues().apply {
    put("type", "learning")
    put("date", "此处省略表达式")
    put("duration", "同上")
    put("words", learnWordsEachTime)
} 
db.insert("LearningRecords", null, values)
```

这里的`put`就是方法啊

##### Lambda还可以显式指定返回值类型

不然有时会不知道返回值是什么



Lambda 表达式亦可以和`let`，`apply`等等一众高阶函数组合使用以使到最好的简化代码~~（迷惑他人~~的作用