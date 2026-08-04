---
title: "Getx 让 Flutter 更简单"
description: "好用爱用"
lastUpdated: 2026-03-27
tags:
  - "flutter"
---

> Flutter made easy
> 这可不是我说的啊，他们的 readme 就是这么写的

虽然他们的文档已经写得很好了，但我还是想专门写点东西
# Getx 是个啥

这是一个很方便使用的包，让状态管理、依赖注入和路由管理都变得简单多了，而且拿它写 MVVM 体感上和安卓原生是差不多的

当然它最主要的用途还是管理状态（数据），毕竟你也不想拖着`InheritedWidget`写一大堆模板代码吧

> 当然管理状态还有像 [provider](https://pub.dev/packages/provider) 之类的包，可以都去了解一下，然后看看哪种更合适你（或者是你的项目）

# 状态管理

状态管理说着高级，实际上主要还是在不同的 Widget 之间共享变量

## 简单的基本用法

现在如果有两个页面 `PageA`和`PageB`，它们同时可以修改一个变量`count`并显示，那我们怎么才能让修改在两个页面间同步呢

聪明的你肯定想到在它们的父组件里面加个`InheritedWidget`，但是吧每次都要创建这么一个类加上一堆长长的方法名，也太麻烦了

此时 Getx 的 `controller`就派上用场了，顾名思义它是一个控制器，像`ViewModel`一样生命周期独立于视图（当然在合适的时机也会自动释放啦）。于是需要共享的变量就可以放在里面

```dart
class CountController extend GetxController {
    int count = 0;
}
```

然后在要使用这个变量之前初始化一下这个 `controller`（这部分涉及 Getx 的[依赖管理](#依赖管理)）

```dart
Get.put(CountController()); // 初始化一个 CountController，并将它加入 Getx 的依赖管理器中
```
然后在需要使用这个变量的时候获取这个`controller`的实例
```dart
class PageA extend StatelessWidget {
    @override
    Widget build(BuildContext context) {
    
        final controller = Get.find<CountController>(); // 在依赖管理器中找到一个 CountController 对象
        print(controller.count);
        
        ...
    }
}
```
就这么简单

但还有更方便的，因为我们要把这个`count`显示出来，所以在它变化时要更新 UI 就得用`setState`。可是如果我想写响应式呢？当然可以！只需要给这个变量做一点小标记，再在 UI 中略微修改就可以做到了

把`count`改成下面这样

```dart
class CountController extend GetxController {
    var count = 0.obs;
}
```

把界面改成这样

```dart
class PageA extend StatelessWidget {
    @override
    Widget build(BuildContext context) {
    
        final controller = Get.find<CountController>(); // 在依赖管理器中找到一个 CountController 对象
        
        return Obx(() => Text(controller.count.value.toString()));
    }
}
```

这个`Text`的内容就会随着`count`的值改变而改变，妈妈从此再也不用担心我忘记`setState`了！

## 不复杂的进阶用法

### .obs 是啥

给上面的`count`加上`.obs`之后，这个变量就是“**可观察的**”了，也就是 **Observable**

除了直接加`.obs`，还可以用`Rx<Type>`来创建

```dart
var count = Rx<Int>(0); // 初始值是不必须的
```

还有一些很常用的类有对应的能快速创建对象的方法

```dart
final name = RxString('');
final isLogged = RxBool(false);
final count = RxInt(0);
final balance = RxDouble(0.0);
final items = RxList<String>([]);
final myMap = RxMap<String, int>({});
```

还没写完呢
# 依赖管理

解释什么是依赖注入是一件复杂的事，你只需要知道 Getx 提供了一个很好用的依赖管理器：只要你之前把你需要用的对象给放进去，那你就能**随时随地**，不需要传递什么上下文，在代码的任何一个位置获取到这个对象的实例

当然最多的还是放 Getx 的 Controller：

```Dart
Controller controller = Get.put(Controller());
```

如果你需要在别的地方用到它，只需要这样：

```Dart
final controller = Get.find();
```

真是太简单了！

## 但是很多时候事情没那么简单

就是说，如果我放了不止一个对象，Getx 又怎么知道我要的是哪个呢？这倒不是难事，因为`Get.put()`和`Get.find()`都是能指定类型的，就像这样：

```Dart
Get.put<MyController>(MyController()); // 这里边的指定不是必须的
Get.put<YourController>(YourController());

final someController = Get.find<MyController>();
```

这样就能稳稳地获取到正确的类型了

然后又出现了新的问题：如果我有好多个`MyController`，又该怎么找到想要的那个呢？

这也很简单，因为`Get.put()`和`Get.find()`还可以指定一个 tag：

```Dart
Get.put<MyController>(MyController(), tag: 'My first Controller');
Get.put<MyController>(MyController(), tag: 'My second Controller');

final someController = Get.find<MyController>(tag: 'My first Controller'); // 当然是获取第一个 Controller 啦
```

只要保证 tag 的字符串是唯一的，就能保证一定能获取对应的对象了

下面是官方文档对`Get.put()`的参数介绍：

```Dart
Get.put<S>(
  // 必备：你想得到保存的类，比如控制器或其他东西。
  // 注："S "意味着它可以是任何类型的类。
  S dependency

  // 可选：当你想要多个相同类型的类时，可以用这个方法。
  // 因为你通常使用Get.find<Controller>()来获取一个类。
  // 你需要使用标签来告诉你需要哪个实例。
  // 必须是唯一的字符串
  String tag,

  // 可选：默认情况下，get会在实例不再使用后进行销毁
  // （例如：一个已经销毁的视图的Controller)
  // 但你可能需要这个实例在整个应用生命周期中保留在那里，就像一个sharedPreferences的实例或其他东西。
  //所以你设置这个选项
  // 默认值为false
  bool permanent = false,

  // 可选：允许你在测试中使用一个抽象类后，用另一个抽象类代替它，然后再进行测试。
  // 默认为false
  bool overrideAbstract = false,

  // 可选：允许你使用函数而不是依赖（dependency）本身来创建依赖。
  // 这个不常用
  InstanceBuilderCallback<S> builder,
)
```

还有一些别的用法这里就不讲了，因为平常用得比较少，想学的话可以自己去研究 (￣﹃￣)

# 路由管理

[官方文档](https://github.com/jonataslaw/getx/blob/master/documentation/zh_CN/route_management.md)是这么讲的

~~其实是我懒得写了，反正这些用法五分钟就学得会~~

# 其他的好东西

## 切换语言

可以像下面这样快速切换应用的语言：

```Dart
var locale = Locale('en', 'US');
Get.updateLocale(locale);
```

## 获取上下文

可以用`Get.context`随时获取当前上下文，有一说一这个功能确实有点夸张，但是很多时候能少写一个参数欸

