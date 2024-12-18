如今已经没有什么kotlin-android-extensions了啊

要方便也只能是`binding`了（吧

#### 在Activity中用binding

在`Activity`中用`binding`要在class里边来个定义

```kotlin
private lateinit var binding: FirstLayoutBinding
```

然后在onCreate里面进行一个值的赋

```kotlin
binding = FirstLayoutBinding.inflate(layoutInflater)
setContentView(binding.root)
```

恭喜你，现在可以像

```kotlin
binding.cannotDoAnymore
```

这样调用一个控件了！

#### 至于在Fragment中……

大差不差啦，比如开始可以这样写

```kotlin
private var _binding: HomepageFragmentBinding? = null
private val binding get() = _binding!!
```

这里用!!是为了防止之后要用一堆?.  不太好看说实话

然后在`onCreateView`之中这样写

```kotlin
override fun onCreateView(
inflater: LayoutInflater,
    container: ViewGroup?,
    savedInstanceState: Bundle?
): View? {
    _binding = HomepageFragmentBinding.inflate(inflater, container, false)
    return binding.root
}
```

大功告成！之后你就能在Fragment中摆脱一大堆`findViewById`了吗？

还有一步，就是在`onDestroyView`中把这个`binding`再干掉！

如下

```kotlin
override fun onDestroyView() {
    super.onDestroyView()
    _binding = null
}
```

为什么呢？GPT言道：需要在 `onDestroyView` 中显式地清理Binding对象，以避免内存泄漏

好吧其实我现在不是很看得懂这玩意



哎呀不管那么多有的没的了，感谢GPT神医就完了

##### 下一集：回来吧findViewById

