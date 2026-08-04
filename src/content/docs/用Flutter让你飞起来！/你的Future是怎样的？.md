---
title: "你的Future是怎样的？"
description: "我眼中的未来又是何种色彩？"
lastUpdated: 2025-02-22
tags:
  - "dart"
---

`Future`是一个类，可以用来做一些比较耗时的操作但不阻塞主线程，等到需要用其返回值时再用

> `Promise`: ?
## 怎么用

### 在定义里

一般都是作为某个函数的返回类型，比如

```dart
Future<String> fetchUsername() { // 不显式指定这个<String>也是可以的，毕竟比较先进的语言都有自动推断类型吧（
	// 模拟一个耗时操作，比如网络请求
	return Future.delayed(Duration(seconds: 2), () => "Alice");
}
```
显然我们要返回一个`Future`对象，但是每次都包装一个太麻烦了，有没有更简单的方法呢？

### async

有的兄弟，有的

`async`（异步）这个单词可以加在函数体外边，自动把返回值包装成`Future`对象，同时也开一个线程，比如这样

```dart
Future<String> fetchUsername() async {  
  Future.delayed(Duration(seconds: 2));  
  return 'Alice';  
}
```

这可真是太方便了，可我们如果要用到返回值的时候该怎么办呢？

### 等等你的函数！

`await`可以让当前线程等一等一个有`Future`的函数，唯一的问题是，你无法选中主线程，所以你只能让所在的有`async`的函数等一等，直到那个函数执行完返回你所需要的值

```dart
Future<void> fetchData() async { // 只能让async等一等
	print("开始获取数据..."); 
	String username = await fetchUsername(); // 等等fetchUsername()吧！
	print("用户名：$username"); 
}
```

### 列表是好文明

