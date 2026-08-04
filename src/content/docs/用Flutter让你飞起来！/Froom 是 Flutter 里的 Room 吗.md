---
title: "Froom 是 Flutter 里的 Room 吗"
description: "Flutter 里也想要 Room"
lastUpdated: 2026-06-12
tags:
  - "flutter"
  - "dart"
  - "sqlite"
---

> 爱来自 wlz 学长：[wilinz/froom](https://github.com/wilinz/froom)

# Froom 是 Flutter 里的 Room 吗

如果之前写过安卓原生，那大概都见过 **Room**。

它的作用很简单：把 SQLite 包一层，让我们不用天天对着一吨字符串和游标发呆。虽然本质上还是数据库，但至少写起来像是在操作对象了。

那到了 Flutter 这边，有没有类似的东西呢？

有的兄弟，有的，它叫 **Froom**。目前由 21 级 APP lz 学长维护

## 先说它是干嘛的

Froom 是一个给 Flutter 用的 SQLite 抽象库，前身叫做 Floor，灵感来源于安卓原生的 Room。

它会帮我们把 Dart 对象和数据库表之间的关系连起来，同时又不把 SQL 藏得太深。也就是说，你还是要会一点 SQL，但是不用自己手写一堆打开数据库、解析结果、塞回对象的东西。

也就是把原始的 SQL 操作封装了一遍

名字里多出来的那个 `F` 大概就是 Flutter 的 `F` 吧，挺 F 的

## 和 Room 完全一致的三件套

Room 里最核心的是三个东西：

- `Entity`：一张表
- `Dao`：操作这张表的方法
- `Database`：整个数据库入口

Froom 也是如此。

只不过 Froom 写的是 Dart。尽管语言不一样，但 Froom 心依然是 Room 心。

### Entity

Room 里一般会这样写：

```kotlin
@Entity
data class User(
    @PrimaryKey val id: Int,
    val name: String
)
```

Froom 里就变成这样：

```dart
import 'package:froom/froom.dart';

@entity
class User {
  @primaryKey
  final int id;
  final String name;

  User(this.id, this.name);
}
```

可以看到差别其实不大，都是给类加个标记，然后告诉它哪个字段是主键。

只不过 Room 的注解是大写开头，Froom 这边是 Dart 风格的小写注解，看起来稍微有点不一样。

### DAO

DAO 就是 **Data Access Object（数据访问对象）**，说人话就是“负责查数据库的对象”。

Room 里一般这样写：

```kotlin
@Dao
interface UserDao {
    @Query("SELECT * FROM user")
    fun getAll(): List<User>

    @Insert
    fun insert(user: User)
}
```

Froom 里就差不多这样：

```dart
@dao
abstract class UserDao {
  @Query('SELECT * FROM User')
  Future<List<User>> findAllUsers();

  @Query('SELECT * FROM User WHERE id = :id')
  Stream<User?> findUserById(int id);

  @insert
  Future<void> insertUser(User user);
}
```

这里比较有 Flutter 味道的是返回值。

普通查询可以返回 `Future`，表示之后给你结果；如果想监听变化，可以返回 `Stream`，数据变了也还能继续收到。

这就和 Flutter 的异步对接上了，不然写本地数据库还要自己搞通知，也太麻烦了。

## Database

Room 里要写一个继承 `RoomDatabase` 的抽象类：

```kotlin
@Database(entities = [User::class], version = 1)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
}
```

Froom 里也是抽象类，只不过继承的是 `FroomDatabase`：

```dart
import 'dart:async';
import 'package:froom/froom.dart';
import 'package:sqflite/sqflite.dart' as sqflite;

part 'database.g.dart';

@Database(version: 1, entities: [User])
abstract class AppDatabase extends FroomDatabase {
  UserDao get userDao;
}
```

那个 `part 'database.g.dart';` 一看就知道要动用代码生成了。

也就是说，这玩意和 Room 一样，不是写完就完事了，还要再生成一波（只不过 Room 可以在启动的时候自动生成）。

## 依赖和生成

想用 Froom 的话要装三个东西：

```yaml
dependencies:
  froom: ^6.0.0

dev_dependencies:
  froom_generator: ^6.0.0
  build_runner: ^2.15.0
```

写完对应代码后跑一下：

```bash
flutter packages pub run build_runner build
```

然后就会生成对应的 `database.g.dart`。

真的是太简单了！除了生成是有点麻烦，Flutter 就这点不太好。

## 用起来

生成之后，这样就能拿到数据库：

```dart
final database = await $FroomAppDatabase
    .databaseBuilder('app_database.db')
    .build();

final userDao = database.userDao;

await userDao.insertUser(User(1, 'Yiyue'));
final users = await userDao.findAllUsers();
```

这个 `$FroomAppDatabase` 就是生成出来的类，名字会根据 `AppDatabase` 的名字变。

如果之前用过 Room，那这里就完全一致了：先来个数据库，再得到 DAO，然后通过 DAO 去增删查改。

## 你用不用吧

如果要用数据库的话，那用 Froom 还是会比摁造 SQL 轻松些的

特别是本来就熟悉 Room 的话，Froom 上手会很快，因为它们的思路完全一致的：

先写表，再写 DAO，再写数据库，最后代码生成一键清除。

## 注解大全

既然 Froom 是 Room 的精神续作，那肯定也少不了一堆注解。

不过这些东西看起来很多，实际上就是在告诉生成器：这个类是什么、这个字段怎么存、这个方法要干什么。

生成器：你不说清楚我怎么知道啊。

### 表相关

`@entity`或者`@Entity(...)`用来把一个类标记成数据库表。

如果只是普通表，用小写的`@entity`就够了：

```dart
@entity
class User {
  @primaryKey
  final int id;
  final String name;

  User(this.id, this.name);
}
```

如果想改表名、加索引、外键、联合主键，那就要用大写的`@Entity(...)`：

```dart
@Entity(
  tableName: 'users',
  primaryKeys: ['id', 'name'],
  indices: [Index(value: ['name'])],
)
class User {
  final int id;
  final String name;

  User(this.id, this.name);
}
```

常用参数大概是这些：

- `tableName`：自定义表名
- `primaryKeys`：联合主键
- `indices`：索引
- `foreignKeys`：外键
- `withoutRowid`：SQLite 的 `WITHOUT ROWID` 表，这个一般用不到

`@primaryKey`或者`@PrimaryKey(...)`用来标记主键。

如果主键想自动生成，就这样：

```dart
@PrimaryKey(autoGenerate: true)
final int id;
```

这点和 Room 也很像，只不过文档里说主键字段要是 `int`。

`@ColumnInfo(...)`用来改列名：

```dart
@ColumnInfo(name: 'user_name')
final String name;
```

如果 Dart 里的字段名和数据库里的列名不想一样，就靠它了。

`@ignore`用来忽略字段：

```dart
@ignore
String? tempText;
```

`getter`、`setter` 和 `static` 字段默认就会被忽略，所以不是所有东西都要自己标。

`ForeignKey(...)`和`Index(...)`严格来说不是直接贴在字段上的注解，更像是塞进`@Entity(...)`里的配置。

外键大概这样：

```dart
@Entity(
  foreignKeys: [
    ForeignKey(
      childColumns: ['owner_id'],
      parentColumns: ['id'],
      entity: User,
    ),
  ],
)
class Dog {
  @primaryKey
  final int id;

  @ColumnInfo(name: 'owner_id')
  final int ownerId;

  Dog(this.id, this.ownerId);
}
```

也就是说，`childColumns`是这张表自己的列，`parentColumns`是被引用表里的列。

索引则是这样：

```dart
@Entity(
  indices: [
    Index(value: ['name'], unique: true),
  ],
)
class User {
  @primaryKey
  final int id;
  final String name;

  User(this.id, this.name);
}
```

索引可以让查询快一点，但也不是越多越好，不然数据库写入的时候也要维护一大坨索引，最后就反过来拖后腿了。

### DAO 相关

`@dao`用来标记 DAO 类。

```dart
@dao
abstract class UserDao {
  // 这里放查询和增删改
}
```

`@Query(...)`用来写 SQL 查询：

```dart
@Query('SELECT * FROM User WHERE id = :id')
Future<User?> findUserById(int id);
```

这里的`:id`会和方法参数`id`对应起来。

如果查不到单个对象，返回值就要写成可空，比如`Future<User?>`，不然就有点自欺欺人了。

`@insert`和`@Insert(...)`用来插入：

```dart
@insert
Future<void> insertUser(User user);

@Insert(onConflict: OnConflictStrategy.replace)
Future<int> insertAndReturnId(User user);
```

小写的`@insert`就是默认插入，大写的`@Insert(...)`可以设置冲突策略。

返回值也不只能是`void`，还可以是插入后的主键，比如`int`或者`List<int>`。

`@update`和`@Update(...)`用来更新：

```dart
@update
Future<void> updateUser(User user);

@Update(onConflict: OnConflictStrategy.replace)
Future<int> updateAndCount(User user);
```

如果返回`int`，就是改了多少行。

`@delete`用来删除：

```dart
@delete
Future<int> deleteUser(User user);
```

返回`int`的话就是删了多少行。

`@transaction`用来把几个操作包成一个事务：

```dart
@transaction
Future<void> replaceUsers(List<User> users) async {
  await deleteAllUsers();
  await insertUsers(users);
}
```

这个方法需要写成`async`，返回值也要是`Future`。

事务就是一荣俱荣一损俱损的“要么全做完，要么都别做”，不然删完旧数据、插入新数据失败，那就很遗憾了。

### 数据库相关

`@Database(...)`用来标记数据库类：

```dart
@Database(version: 1, entities: [User])
abstract class AppDatabase extends FroomDatabase {
  UserDao get userDao;
}
```

常用参数就是：

- `version`：数据库版本
- `entities`：有哪些表
- `views`：有哪些数据库视图

如果之后表结构变了，就要改`version`，然后写迁移：

```dart
final migration1to2 = Migration(1, 2, (database) async {
  await database.execute('ALTER TABLE users ADD COLUMN nickname TEXT');
});

final database = await $FroomAppDatabase
    .databaseBuilder('app_database.db')
    .addMigrations([migration1to2])
    .build();
```

迁移本身不是注解，但它经常和`@Database(version: ...)`一起出现，所以也放上来了。

### 视图和类型转换

`@DatabaseView(...)`用来定义数据库视图。

视图可以理解成一个提前写好的`SELECT`，像虚拟表一样查询，但是不能插入、更新、删除。

```dart
@DatabaseView(
  'SELECT distinct(name) AS name FROM users',
  viewName: 'user_names',
)
class UserName {
  final String name;

  UserName(this.name);
}
```

定义完之后还要放进数据库：

```dart
@Database(version: 1, entities: [User], views: [UserName])
abstract class AppDatabase extends FroomDatabase {
  UserDao get userDao;
}
```

如果只是想查一些拼出来的数据，视图会很方便。

`TypeConverter`和`@TypeConverters(...)`用来处理 SQLite 不认识的类型。

比如 SQLite 不知道 Dart 的`DateTime`是什么，那就把它变成`int`存进去：

```dart
class DateTimeConverter extends TypeConverter<DateTime, int> {
  @override
  DateTime decode(int databaseValue) {
    return DateTime.fromMillisecondsSinceEpoch(databaseValue);
  }

  @override
  int encode(DateTime value) {
    return value.millisecondsSinceEpoch;
  }
}

@TypeConverters([DateTimeConverter])
@Database(version: 1, entities: [Order])
abstract class OrderDatabase extends FroomDatabase {
  OrderDao get orderDao;
}
```

这个功能还是实验性的，所以能不用复杂类型就先别用吧。

### FTS

`@fts3`、`@fts4`或者大写的`@Fts3(...)`、`@Fts4(...)`是全文搜索用的。

普通 CRUD 基本碰不到它们，如果之后要做搜索，尤其是对一大堆文本做搜索，才需要看这一块。

它们可以设置 tokenizer，比如：

```dart
@Fts4(tokenizer: FtsTokenizer.unicode61)
@entity
class Article {
  final String title;
  final String content;

  Article(this.title, this.content);
}
```

这玩意已经有点太贴近 SQLite 了，但是还是放上来，因为有这玩意

## 最后整理一下

一般应该也只能用到这些：

- 表：`@entity`、`@primaryKey`、`@ColumnInfo`、`@ignore`
- DAO：`@dao`、`@Query`、`@insert`、`@update`、`@delete`、`@transaction`
- 数据库：`@Database`
- 比较高手：`@Entity(...)`、`Index`、`ForeignKey`、`@DatabaseView`、`@TypeConverters`
- 特殊场景：`@fts3`、`@fts4`

看起来很多，但实际写项目的时候，一开始可能只会用到前两行。

剩下的东西应该也用不到了吧
