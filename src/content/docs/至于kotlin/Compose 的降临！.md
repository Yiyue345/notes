---
title: "Compose 的降临！"
description: "写爽了"
lastUpdated: 2025-11-23
tags:
  - "Kotlin"
  - "安卓"
---

# 抛弃石山，做回自己！

你是否已经厌倦了在 xml 中拖拖拽拽，最终只是搓出了相当一般界面的日子了？

你是否已经对每次创建 Activity 和 Fragment 时都要加个布局文件，每个控件都要单独声明（即使用 binding 也很麻烦）的繁琐操作感到失望？

你是否羡慕例如 Flutter 那样的声明式 UI，优雅地将布局界面写到代码中去，不用在两个文件间反复切换，浪费生命？

那 **Jetpack Compose** 就能解决你的烦恼！

> Jetpack Compose 是用于构建原生 Android 界面的新工具包。它使用更少的代码、强大的工具和直观的 Kotlin API，可以帮助您简化并加快 Android 界面开发。

## 让我们开始吧

在古老的没有 Compose 的时代，程序员都是在 Activity 里面这样处理界面的：

```kotlin
// 首先要声明一个 binding
lateinit var binding: ActivityHomepageBinding

override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)  
    // 然后再给 binding 赋值
    binding = ActivityHomepageBinding.inflate(layoutInflater)  
    // 还要绑定布局
    setContentView(binding.root)
    
    // 之后要调用 xml 中的某个控件还得加上 binding.
    // 如果不用 binding 也方便不到哪去
}
```

很容易发现，即使我们要绑定界面和 Activity，就要写上这么一大串的重复代码了（虽然可以自动生成）。如果代码量一大，这样的重复工作就会变得特别繁琐。

那 Compose 呢？

```kotlin
override fun onCreate(savedInstanceState: Bundle?) {  
    super.onCreate(savedInstanceState)  

    setContent {  
        // 各种 Composable 函数
    }    
}
```

真的是太简洁了有没有，如果要学习 Compose，主要就是学习那些 Composable 函数

## @Composable

只要给函数加上一个`@Compsable`注解，这个函数就是 Composable 的（废话

```kotlin
@Composable
fun Ciallo() {
    Text("Ciallo~")
}
```

这就是个简单的 Composable 函数，可以被放到`setContent`里面，作用是显示`Ciallo~`这段文本

那些已经准备好的各种组件也都是有`@Compsable`的

## 关于 Context

我们在做很多操作的时候都要用到 Context，即上下文，常用的 Activity 就是 Context 的派生类，也就是说 Activity 是 Context 的一种

如果我们要显示一个 Toast，那就要传入一个 Context

```kotlin
// 在 Activity 中是这样的
Toast.makeText(this, "我是文本", Toast.LENGTH_SHORT).show() 

// 在 Fragment 中是这样的
Toast.makeText(requireActivity(), "我也是文本", Toast.LENGTH_SHORT).show()
```

在 Composable 函数里面显然不能这样写，但是聪明的谷歌工程师也给出了方法，也就是下面这样

```kotlin
// 先获取当前的 Context
val context = LocalContext.current 

// 然后再用
Toast.makeText(context, "我还是文本", Toast.LENGTH_SHORT).show()
```
## remember 和 mutableStateOf


## 关于 ViewModel

可以去[这里](用%20VIewModel%20来连通一切.md#大人，时代变了)看看