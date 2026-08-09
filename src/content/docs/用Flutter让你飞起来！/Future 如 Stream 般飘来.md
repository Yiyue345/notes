---
title: Future 如 Stream 般飘来
description: 我眼中的未来又是何种色彩？
lastUpdated: 2026-08-09
tags:
  - dart
---
这是两个写 Dart 异步时必然要用到的类，必须要明白的是，Dart 一般都是单线程的，除非自己开 Isolate

# Future

`Future`是一个类，可以用来做一些比较耗时的操作但不阻塞主线程，等到需要用其返回值时再用

> `Promise`: ?
## 怎么用

### 通过构造函数

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

`async`（异步）这个单词可以加在函数体外边，自动把返回值包装成`Future`对象，同时~~开一个线程~~让它稍后执行，比如这样


```dart
Future<String> fetchUsername() async {  
  Future.delayed(Duration(seconds: 2));  
  return 'Alice';  
}
```

其实本质上就是把这个任务放到队列中去，等更重要的任务执行完再执行它

这可真是太方便了，可我们如果要用到返回值的时候该怎么办呢？

### 等等你的函数！

`await`可以一直等一个有`Future`的函数，唯一的问题是，你无法选中主线程，所以你只能让所在的有`async`的函数等一等，直到那个函数执行完返回你所需要的值

```dart
Future<void> fetchData() async { // 只能让async等一等
	print("开始获取数据..."); 
	String username = await fetchUsername(); // 等等fetchUsername()吧！
	print("用户名：$username"); // 好耶得到这个值了
}
```

也就是通过保存这个函数的状态来“暂停”了这个函数的后续代码，直到`await`的函数结束（似是 Kotlin 来

### 异步也不得不防

和写多线程一样，写异步也很容易遇到各种妙妙异常，这时就得请出`try-catch`了。但是这玩意应该谁都会用吧，不写了哈哈

# Stream

`Stream`也是一个类，也可以用来做一些比较耗时的操作但不阻塞主线程，等到需要用其返回值时再用，不同之处是它可以返回多个值，合适需要持续获取数据的时候用

## 怎么用

### 从构造函数声明

用到这个的时候应该都会看用什么构造函数了吧（

去看看那一堆工厂构造函数就知道怎么得到一个`Stream`了

### async*

和`async`不同的是，`async*`可以让你得到一个`Stream`对象，就像下面这样

```dart
Stream<int> countStream() async* {
  for (int i = 1; i <= 5; i++) {
    await Future.delayed(const Duration(seconds: 1));
    yield i;
  }
}
```

发现了吗，和`Future`不同的是，`Stream`返回一个值需要用`yield`

其实除了一般的`yeild`，还有一个`yeild*`，用来返回一个`Stream`：

```dart
Stream<int> firstStream() async* {
  yield 1;
  yield 2;
}

Stream<int> secondStream() async* {
  yield 0;
  yield* firstStream();
  yield 3;
}
```

然后能得到：

```
0
1
2
3
```

然后我们遇到了和上面类似的问题：怎么拿到它的返回值呢？

此时你可能想到了`await`，但是先别急！我们可以直接用`listen`来监听：

```dart
countStream().listen( 
  (value) { 
    print('收到数据：$value'); 
  }, 
  onError: (error) { 
    print('发生错误：$error'); 
  }, 
  onDone: () { 
    print('Stream 已结束'); 
  }, 
);
```

也就是加了几个监听器，来直接监听它

### 也等等你的流！

我们当然不能总是只用监听器的，不过也不能直接用`await`，而是用`await for`，它能像`for-in`一样持续遍历`Stream`的返回值，比如

```dart
Future<void> main() async {
  await for (final value in countStream()) {
    print('收到：$value');
  }

  print('Stream 已结束');
}
```

这样就可以不断地**收到**了╰(￣ω￣ｏ)

### 还有些别的事

一般的`Stream`是不能被监听多次的，不然可能会报错，如果想要监听多次，就要用广播`Stream`：

```dart
final controller = StreamController<int>.broadcast();

controller.stream.listen((value) {
  print('页面 A：$value');
});

controller.stream.listen((value) {
  print('页面 B：$value');
});

controller.add(10);
```

之后就会输出

```text
页面 A：10 页面 B：10
```

类似不少集合，`Stream`也有`.map()`和`.where()`这些方法

顺带一提，`Future`和`Stream`在一定程度上是可以相互转化的，不过嘛……感觉用起来也比较一般