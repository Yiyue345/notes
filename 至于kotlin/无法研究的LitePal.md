### 顶上放个标题就是好看

由于被明日方舟牵制，我不得不在宿舍开始对LitePal的研究

令人哈哈大笑的是添加依赖失败了

所以接下来只能抄文档了

可恶啊怎么理智还没有清完



失败，太失败了

解析不了了只能摁造SQL了



### LitePal

> 你别说，这放个标题还挺像样的

#### 初始化

~~我才发现GPT输出的好像就是md格式~~

##### 配置xml

在`main\assets`目录下新建一个叫`litepal.xml`的文件（又要手打xml了吗

在这个xml里面填入数据库的名字、版本和数据库模型

如下所示

```xml
<?xml version="1.0" encoding="utf-8"?>
<litepal>
    <dbname value="YourDatabaseName" />
    <version value="1" />
     <!--映射模型-->
    <list>
        <mapping class="com.example.yourapp.model.YourModelClass" />
        <!--添加实体类，此处必须映射完整路径-->
    </list>
</litepal>
```

数据库模型必须继承自`LitePalSupport`