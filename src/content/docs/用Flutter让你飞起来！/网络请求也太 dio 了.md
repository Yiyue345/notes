---
title: "网络请求也太 dio 了"
description: "网络请求就靠它"
lastUpdated: 2026-05-28
tags:
  - "flutter"
  - "dart"
---

> 我不做人了！
# 网络请求也太 Dio 了

`Dio`是一个 Dart/Flutter 里常用的网络请求库，简单来说就是拿来发 HTTP 请求的。

如果只发一两个请求，用自带的`http`包当然也不是不行，但是东西一多就会出现 headers、token、超时、拦截器、上传下载这些东西。

这时候再手搓就有点折磨了，所以 Dio 就帮我们封装好了

## 先装依赖

这个都会吧我就不写了

## 创建一个 Dio

最简单可以直接这样：

```dart
final dio = Dio();
```

但是实际项目里一般会给它一点默认配置，比如后端地址和超时时间：

```dart
final dio = Dio(
  BaseOptions(
    baseUrl: 'https://api.example.com',
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 5),
  ),
);
```

这样之后请求`/user`，实际上就是请求`https://api.example.com/user`，就很省事

## GET

`GET`一般用来拿数据。

```dart
final response = await dio.get(
  '/users',
  queryParameters: {
    'page': 1,
    'size': 20,
  },
);

print(response.data);
```

`queryParameters`其实就是 URL 后面那些`?page=1&size=20`，只不过 Dio 帮拼好了。

好耶，这样就不用自己去加问号和`&`了

## POST

`POST`一般用来提交数据，比如登录：

```dart
final response = await dio.post(
  '/login',
  data: {
    'username': 'yiyue',
    'password': '114514',
  },
);

print(response.data);
```

这里的`data`就是请求体。后端如果想要 JSON 的话，那这样写一般没啥问题。

## 加请求头

有些接口要 token，这时可以在某一次请求里加：

```dart
final response = await dio.get(
  '/profile',
  options: Options(
    headers: {
      'Authorization': 'Bearer $token',
    },
  ),
);
```

如果每个请求都要 token，那每次都写一遍就太麻烦了，可以放到拦截器里。

## 拦截器

就是可以在请求发出去前、响应回来后、出错时做点什么。

看一眼代码就懂了

```dart
dio.interceptors.add(
  InterceptorsWrapper(
    onRequest: (options, handler) {
      options.headers['Authorization'] = 'Bearer $token';
      return handler.next(options);
    },
    onResponse: (response, handler) {
      return handler.next(response);
    },
    onError: (error, handler) {
      return handler.next(error);
    },
  ),
);
```

最常见的用途就是统一加 token、打印日志、处理登录过期。

不过不要把全部业务逻辑都塞这里，不然拦截器就会变得超级臃肿，之后想改就要面对一大坨了。

## 错误处理

Dio 请求失败时一般会抛`DioException`，所以经常要加个`try`：

```dart
try {
  final response = await dio.get('/profile');
  print(response.data);
} on DioException catch (e) {
  print(e.response?.statusCode);
  print(e.message);
}
```

`e.response`里面可能有后端返回的错误信息，`e.message`一般是 Dio 自己总结出来的东西。

网络请求的不确定因素太多了，所以错误还是要`catch`一下的，不然就只能去翻日志找问题了

## 表单和文件

如果要上传文件，可以用`FormData`：

```dart
final formData = FormData.fromMap({
  'name': 'avatar',
  'file': await MultipartFile.fromFile('path/to/avatar.png'),
});

await dio.post('/upload', data: formData);
```

这个不像 GET、POST 用得那么多，但如果要上传头像、附件之类的就得用了。

## 下载

Dio 也能下载文件：

```dart
await dio.download(
  'https://example.com/file.zip',
  'save/path/file.zip',
  onReceiveProgress: (received, total) {
    if (total != -1) {
      print('${(received / total * 100).toStringAsFixed(0)}%');
    }
  },
);
```

`onReceiveProgress`可以拿到下载进度，然后就可以塞个花里胡哨的进度条了。

## 取消请求

有时候页面都无了，请求还在路上冲刺，这就不太好

于是我们可以用`CancelToken`让它停下来：

```dart
final cancelToken = CancelToken();

dio.get('/search', cancelToken: cancelToken);

cancelToken.cancel('页面关闭了，不用查了');
```

比如搜索框里连着搜索很多次，就可以取消上一次请求，不然旧结果可能倒反天罡把新结果覆盖了，这就很难受了

## 大概就这些

Dio 的基本用法就是：

- 用`Dio(BaseOptions(...))`放默认配置
- 用`get`拿数据
- 用`post`交数据
- 用`Options`或者拦截器加 headers
- 用`DioException`处理错误
- 特殊情况再用上传、下载、取消请求

再复杂一点就是封装一个`ApiClient`，把这些东西都包起来，不要在每个页面里到处写网络请求。

不过那就是项目结构的问题了，之后再说吧(￣▽￣)"
