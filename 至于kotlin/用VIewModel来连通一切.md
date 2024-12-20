---
tags:
  - kotlin
  - Android
---
### ViewModel，你简直就是救世主

但是为什么不能让Fragment直接访问Activity的值呢，就因为这样太丑陋了吗？

（好像还真是

#### 啥是ViewModel

这玩意就是Activity和Fragment之间的桥梁，而且即使Acitivity重新创建（旋转）了也不为所动，因此可以拿来保存两者共有的数据

#### 怎么用

创建一个ViewModel只要继承一个就好啦

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

等下……我记得好像还有个ViewModelFactory吧，那是啥来着？