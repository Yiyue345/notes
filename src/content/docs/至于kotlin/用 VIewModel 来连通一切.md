---
title: "用 VIewModel 来连通一切"
description: "这可方便了"
lastUpdated: 2025-11-24
tags:
  - "安卓"
---

## ViewModel，你简直就是救世主

但是为什么不能让Fragment直接访问Activity的值呢，就因为这样太丑陋了吗？

（好像还真是

### 啥是ViewModel

这玩意就是 Activity 和 Fragment 之间的桥梁，而且即使 Acitivity 重新创建（旋转）了也不为所动，因此可以拿来保存两者共有的数据

更准确地说，它其实是逻辑与界面之间的桥梁

### 怎么用

创建一个 ViewModel 只要继承一个就好啦

```kotlin
class MyViewModel : ViewModel()
```

之后里边可以放一大堆数据，无论Activity还是（属于它的）Fragment都可看可查的的那种

经常拿来和LiveData配合打组合技

在Activity和Fragment里用ViewModel的方法都是一样的，首先创建一个private lateinit var

```kotlin
private lateinit var myViewModel: MyViewModel
```

然后进行一个赋值

```kotlin
myViewModel = ViewModelProvider(context)[MyViewModel::class.java]
```

就可以在后面加个.愉快地调用其中的变量与函数啦

### 像对象一样传参（并不

等下……我记得好像还有个`ViewModelProvider.Factory`吧，那是啥来着？

可以看作是`ViewModel`的一个构造方式吧，这样就可以像类和函数那样有预先传入的参数了~~，不用像某个人一样手动把内部变量全部赋值一遍~~

那要怎么做呢？先对`ViewModel`本身动手脚

```kotlin
class MyViewModel(number: Int) : ViewModel()
```

这样这个`ViewModel`就需要传入一个参数了

之后便要构建传参的路径，就需要那`ViewModelProvider.Factory`了

```kotlin
class MyViewModelFactory(private val number: Int) : ViewModelProvider.Factory { 
	override fun <T : ViewModel> create(modelClass: Class): T { 
		return MyViewModel(number) as T 
	} 
}
```

最后在赋值的时候在参数里面添加这个`Factory`就好了，例如

```kotlin
myViewModel = ViewModelProvider(this, MyViewModelFactory(number))[MyViewModel::class.java]
```

当当当，大功告成！

## 大人，时代变了

在用 Compose 的时代，如果我们不在 Activity 或者 Fragment 的作用域里面，显然上面那些经典的方法是用不了的

当然，新时代也是有新时代的方法的！~~（不过这些方法似乎不自带~~

首先需要加上`androidx-lifecycle-viewmodel-compose`这个包

然后我们只需要在 Composable 函数中这样

```kotlin
val viewModel: HomepageViewModel = viewModel()
```

就可以用 ViewModel 了，是不是非常简单呢