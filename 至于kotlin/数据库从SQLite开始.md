### 论SQLite的操作

###### ROOM是谁，我在哪，我的大脑呢

操作基本靠exeSQL（就是直接用SQL

SQL是不分大小写的

有时工具不一定靠谱，真正重要的是靠自己的判断

#### 省流

------

|        | 通过API                                                      | 通过SQL                                  |
| ------ | ------------------------------------------------------------ | ---------------------------------------- |
| 增表   |                                                              | `create table 表名 (一堆值的名及[类型])` |
| 增数据 | `db.insert(表名, null, 值)`                                  | `insert into 表名 (键) values(值)`       |
| 删表   |                                                              | `drop table [条件] 表名`                 |
| 删数据 | `db.delete("表名, 条件", 条件的值)`                          | `delete from 表名 where 条件`            |
| 改     | `db.update(表名, 要修改的列, 条件),  arrayOf(值)`            | `update 表名 set 列名 = ? where 条件`    |
| 查     | `db.query(表名, 列名, 条件, 条件中的具体值, 要分组的列, 分组的筛选条件, 搜索结果的排序方式)` | `select 列名 from 表名 where 条件 ……`    |



#### 首先

操作数据库那就得先有一个，原始的办法是弄个SQLiteOpenHelper，比如下面这样

```kotlin
class NoteDatabaseHelper(val context: Context, name: String, version: Int) :
SQLiteOpenHelper(context, name, null, version)
```

这样在别的文件中，可以通过两行代码来用这个Helper

```kotlin
val dbHelper = NoteDatabaseHelper(context, "数据库名", 版本)
val db = dbHelper.writableDatabase
```

这个`db`就是可以操作的数据库了

#### 增(insert)

创建一个新表可以像下面这样：

```sqlite
create table Note (
        id integer primary key autoincrement,
        title text,
        content text,
        editTime)
```

也就是`create table 表名 (一堆值的名及类型(可选))`

如果想要默认值，可以在类型后面加上`NOT NULL DEFAULT 默认值`

往表里面插入新的数据如下

```kotlin
val value = ContentValues().apply {
    put("title", binding.titleBox.text.toString())
    put("content", binding.editBox.text.toString())
    put("editTime", System.currentTimeMillis())
}
db.insert("Note", null, value)
```

在kt里面可以这样组装一个数据再插入，插入不过就是`db.insert(表名, null, 值)`

除此之外，插入还可以用`insertWithOnConflict`，用来处理可能出现的冲突，只要在最后多加一个参数，比如

```kotlin
db.insertWithOnConflict("word", null, values, SQLiteDatabase.CONFLICT_IGNORE) // 忽略相同id
```

这样就是当主键冲突时忽略然后继续插入

直接用SQL那就是`insert into 表名 (键) values(值)`后面再填值，例如

```kotlin
db.execSQL("insert into Book (name, author, pages, price) values(?, ?, ?, ?)", 
    arrayOf("The Da Vinci Code", "Dan Brown", "454", "16.96") 
) 
```

看得出来一个?对应一个值

#### 删(delete)

就是`db.delete("表名, 条件", 条件的值)`，比如

```kotlin
db.delete("Book", "pages > ? ", arrayOf("500"))
```

用SQL则是`delete from 表名 where 条件`，后面跟上一串条件，如

```kotlin
db.execSQL("delete from Book where pages > ?", arrayOf("500")) 
```

删表则是`drop table [条件] 表名` ，像是

```sql
drop table Note
```

#### 改(update)

修改数据用的是`update`，像`db.update("Book", values, "name = ?", arrayOf("The Da Vinci Code"))` 

即`db.update(表名, 要修改的列, 条件),  arrayOf(值)`，其中要修改的列和条件和值都可以不止一个

用SQL就变成了

```sql
update 表名 set 列名 = ? where 条件
```

后面一样用`arrayOf`填入值即可

#### 查(select/query)

查可麻烦了，有一大堆参数

`db.query(表名, 列名, 条件, 条件中的具体值, 要分组的列, 分组的筛选条件, 搜索结果的排序方式)`

如果换成用参数名表示就是

`db.query(table, columns, selections, selectionArgs, groupBy, having, orderBy)`

使用`having`时必须也要有`groupBy`否则会狠狠报错

一般情况下都是用不到那么多个参数的，所以不要的地方用`null`填满就好了，比如

```kotlin
val cursor = db.query("Book", null, null, null, null, null, null)
```

用SQL上面这句可以简化成

```kotlin
val cursor = db.rawQuery("select * from Book", null) 
```

要一行一行查询数据可以这样

```kotlin
if (cursor.moveToFirst()) {
    do {
    val name = cursor.getString(cursor.getColumnIndex("name"))
    val author = cursor.getString(cursor.getColumnIndex("author"))
    val pages = cursor.getInt(cursor.getColumnIndex("pages"))
    val price = cursor.getDouble(cursor.getColumnIndex("price"))
    } while (cursor.moveToNext())
}
cursor.close() // 最后别忘了关掉
```

不过用`getColumnIndexOrThrow`比用`getColumnIndex`要更安全，不然有可能直接得到-1崩掉

在查询数据时一定要先用`moveToFirst()`转到第一个符合条件的数据，不然会狠狠地报错！

#### 有关更多SQL语句

`id BETWEEN A AND B`可以查询所有符合A≤id≤B的行

`DESC`代表倒序查找

#### 事务(transaction)

事务让一组操作只有全部执行完才会生效，有一个操作失败了就要全部打回

通过`db.beginTransaction()`就可以开启一个事务了

`db.setTransactionSuccessful()`说明事务完成，而`db.endTransaction()`代表事务结束

显然如果事务不完成那即使结束了前面对数据库的操作会全部木大

可以像下面这样用事务

```kotlin
db.beginTransaction()
try{
	...
    db.setTransactionSuccessful()
} catch (...) {
	...
} finally {
    db.endTransaction()
}
```



好耶！这样SQLite的基础操作就学完了，接下来的步骤是……学别的数据库框架，然后就不用这些语法了？！

不过那些框架都是基于SQLite写的，至少能知道面对的是个啥罢

下一集：[LitePal](无法研究的LitePal.md)我来辣！

下下一集：解析失败重回SQLite
