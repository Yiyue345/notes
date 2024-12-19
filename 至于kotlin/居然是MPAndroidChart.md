这是一个比较方便的创建图表的库（因为没用过别的

## 如何搓一张图
### 开局

```kotlin
implementation("com.github.PhilJay:MPAndroidChart:v3.1.0")
```
### 造图
`BarChart`是柱状图，`LineChart`是折线图

每个图都要有一个**数据集**，`BarChart`要`BarDataSet`，`LineChart`要`LineDataSet`，数据集还要变成数据……一些属性要在图表中设置，还有一些要在**数据集**中设置

#### 搓数据集
首先要有一个**条目(entry)**的列表，之后再变成`DataSet`

比如
```kotlin
val entries = ArrayList<BarEntry>()
val timeEntries = ArrayList<Entry>()
```
然后就可以往里面`add`想要的`Entry`对象了，无论是`BarEntry`还是`Entry`，格式都是`Entry(Float, Float)`

塞完数据就可以像下面这样变成数据集然后变成数据了
```kotlin
val dataSet = BarDataSet(entries, "")  // 那个字符串很显然是介绍
val data = BarData(dataSet)
```
然后就能让图表的`data` = `data`了

>[!NOTE]
>
>即使**已经**给图表设置了数据集，修改数据集的属性**也是可以影响图表显示效果的**

#### 搓图
数据集已经设置好了，其实没什么可以搓的了

只需要调用图的`invalidate()`方法刷新即可

#### 搓ValueFormatter
这玩意中文应该叫啥，数值整形器吗（

很容易发现这默认的数据显示格式十分丑陋，自带小数点

这对强迫症来说肯定是无法忍受的，所以他们贴心地准备了个`ValueFormatter`，顾名思义就是把数据格式化的东西

这便是一个把小数点去掉变成整数的`ValueFormatter`
```kotlin
val valueFormatter = object : ValueFormatter() { // 小数变成整数  
    override fun getFormattedValue(value: Float): String? {  
        return String.format("%.0f", value)  
    }  
}
```

只要返回的是字符串便好，但为什么不能直接放字符串进去呢

### 各种属性

超多属性供您微操，打造属于自己的图表！

#### 数据集的

```kotlin
dataSet.valueFormatter = valueFormatter  // 数据集的值按什么格式来显示
dataSet.setDrawValues(true)  // 在柱子顶部显示它的的值
dataSet.valueTextSize = 10f // 柱子顶部字体大小
```

#### 图表的

```kotlin
barChart.setScaleEnabled(false) // 缩放  
barChart.barData.barWidth = 0.5f // 宽度  
barChart.legend.isEnabled = false // 图例  
barChart.description.isEnabled = false // 介绍  

barChart.xAxis.setDrawGridLines(false) // 网格线  
barChart.xAxis.setDrawAxisLine(false)  
barChart.axisLeft.isEnabled = false // 左边的Y轴  
barChart.axisRight.isEnabled = false // 右边的Y轴

barChart.xAxis.valueFormatter = valueFormatter  // 图表底部值的显示格式
barChart.xAxis.position = XAxis.XAxisPosition.BOTTOM  // X轴显示在底部
barChart.xAxis.setDrawLabels(true) // 柱子底下的标签  
barChart.xAxis.granularity = 1f // 柱子间距  
barChart.axisLeft.axisMinimum = 0f // Y轴的最小值

barChart.setTouchEnabled(false) // 触摸

barChart.animateY(1000) // 一秒钟的Y轴动画
```


还有更多！但是我觉得这么多也差不多够用了