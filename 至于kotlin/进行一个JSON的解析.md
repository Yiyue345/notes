### 怎么又是JSON？

> 好吧，我只是想起当年做MC整合包时手打JSON的日子了

**JSON**（JavaScript Object Notation）即JavaScript对象表示法，这玩意体积小又好看所以用得很多，于是在哪里都能看见这玩意（随便一搜就在电脑上搜出了39231个JSON文件

由于这东西用途太广了，于是解析这玩意的方法也不少

#### 用GSON解析

对`{"name":"Tom","age":20}` 这样一段JSON数据，用GSON解析成一个对象很简单

```kotlin
val gson = Gson()
val person = gson.fromJson(jsonData, Person::class.java)
```

而对于像`[{"name":"Tom","age":20}, {"name":"Jack","age":25}, {"name":"Lily","age":22}]` 这样一个数组，则需要

```kotlin
val typeOf = object : TypeToken<List<Person>>() {}.type 
val people = gson.fromJson<List<Person>>(jsonData, typeOf) 
```

这样将其解析为一个列表

不过GSON主要是写给Java的，用在kt上多少会有点问题

于是就要请出下一位选手登场

#### 用Moshi解析~~（もしもし~~

相比GSON，Moshi对kt的支持更好，还有个专门给kt用的扩展，就叫Moshi-kotlin

用Moshi解析`{"name":"Tom","age":20}`只需这样

```kotlin
val moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
val jsonAdapter = moshi.adapter(Person::class.java)
val person = jsonAdapter.fromJson(jsonData)
```

而数组也只要这样

```kotlin
val moshi = Moshi.Builder().build()
val type = Types.newParameterizedType(List::class.java, Person::class.java)
val jsonAdapter = moshi.adapter<List<Person>>(type)
val people: List<Person>? = jsonAdapter.fromJson(jsonData)
```

就得到people这样一个列表了



#### 有关反射序列化

以下是GPT原话：

> 在 Kotlin 中，**反射序列化**是指使用反射机制（reflection）将对象动态转换为 JSON 字符串，或从 JSON 字符串动态转换为对象的过程。反射让程序在运行时可以检查、创建或操作对象的属性和方法，而无需知道它们的具体类型。
>
> ### 为什么需要 Moshi 适配 Kotlin 的反射序列化？
>
> Moshi 默认使用 Java 的反射来处理对象的序列化和反序列化，但 Kotlin 的数据类（`data class`）有一些独特的特性，如不可为空的属性、默认参数等。这些特性在 Java 中并不常见，所以 Moshi 默认情况下并不能很好地支持 Kotlin 数据类的反射序列化。
>
> 为了解决这个问题，Moshi 提供了 `KotlinJsonAdapterFactory`，它是一个专门为 Kotlin 设计的适配器工厂，可以使 Moshi 兼容 Kotlin 的数据类。如果要完全避免反射的使用，还可以通过 `moshi-kotlin-codegen` 插件直接生成序列化代码。
>
> ### 使用反射序列化和 Moshi Kotlin 支持的好处
>
> 使用 `KotlinJsonAdapterFactory` 或 `moshi-kotlin-codegen` 可以让 Moshi 更加准确地处理 Kotlin 数据类，使其在序列化和反序列化时符合 Kotlin 的数据类规范，避免因类型不匹配或字段缺失导致的错误。这也让开发者在解析 JSON 时不再需要手动处理 Kotlin 特有的属性特性。

总之好就完了(￣﹃￣)