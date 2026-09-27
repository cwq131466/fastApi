from tortoise import fields

from app.schemas.menus import MenuType

from .base import BaseModel, TimestampMixin
from .enums import MethodType


class User(BaseModel, TimestampMixin):
    username = fields.CharField(max_length=20, unique=True, description="用户名称", index=True)
    alias = fields.CharField(max_length=30, null=True, description="姓名", index=True)
    email = fields.CharField(max_length=255, unique=True, description="邮箱", index=True)
    phone = fields.CharField(max_length=20, null=True, description="电话", index=True)
    password = fields.CharField(max_length=128, null=True, description="密码")
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    is_superuser = fields.BooleanField(default=False, description="是否为超级管理员", index=True)
    last_login = fields.DatetimeField(null=True, description="最后登录时间", index=True)
    roles = fields.ManyToManyField("models.Role", related_name="user_roles")
    dept_id = fields.IntField(null=True, description="部门ID", index=True)
    oauth_access_token = fields.CharField(max_length=512, null=True, description="OAuth access token", index=True)
    avatar = fields.CharField(max_length=500, null=True, description="头像URL", index=True)

    class Meta:
        table = "user"


class Role(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, unique=True, description="角色名称", index=True)
    desc = fields.CharField(max_length=500, null=True, description="角色描述")
    menus = fields.ManyToManyField("models.Menu", related_name="role_menus")
    apis = fields.ManyToManyField("models.Api", related_name="role_apis")

    class Meta:
        table = "role"


class Api(BaseModel, TimestampMixin):
    path = fields.CharField(max_length=100, description="API路径", index=True)
    method = fields.CharEnumField(MethodType, description="请求方法", index=True)
    summary = fields.CharField(max_length=500, description="请求简介", index=True)
    tags = fields.CharField(max_length=100, description="API标签", index=True)

    class Meta:
        table = "api"


class  Menu(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, description="菜单名称", index=True)
    remark = fields.JSONField(null=True, description="保留字段")
    menu_type = fields.CharEnumField(MenuType, null=True, description="菜单类型")
    icon = fields.CharField(max_length=100, null=True, description="菜单图标")
    path = fields.CharField(max_length=100, description="菜单路径", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    parent_id = fields.IntField(default=0, description="父菜单ID", index=True)
    is_hidden = fields.BooleanField(default=False, description="是否隐藏")
    component = fields.CharField(max_length=100, description="组件")
    keepalive = fields.BooleanField(default=True, description="存活")
    redirect = fields.CharField(max_length=100, null=True, description="重定向")

    class Meta:
        table = "menu"


class Dept(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, unique=True, description="部门名称", index=True)
    desc = fields.CharField(max_length=500, null=True, description="备注")
    is_deleted = fields.BooleanField(default=False, description="软删除标记", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    parent_id = fields.IntField(default=0, max_length=10, description="父部门ID", index=True)

    class Meta:
        table = "dept"


class DeptClosure(BaseModel, TimestampMixin):
    ancestor = fields.IntField(description="父代", index=True)
    descendant = fields.IntField(description="子代", index=True)
    level = fields.IntField(default=0, description="深度", index=True)


class AuditLog(BaseModel, TimestampMixin):
    user_id = fields.IntField(description="用户ID", index=True)
    username = fields.CharField(max_length=64, default="", description="用户名称", index=True)
    module = fields.CharField(max_length=64, default="", description="功能模块", index=True)
    summary = fields.CharField(max_length=128, default="", description="请求描述", index=True)
    method = fields.CharField(max_length=10, default="", description="请求方法", index=True)
    path = fields.CharField(max_length=255, default="", description="请求路径", index=True)
    status = fields.IntField(default=-1, description="状态码", index=True)
    response_time = fields.IntField(default=0, description="响应时间(单位ms)", index=True)
    request_args = fields.JSONField(null=True, description="请求参数")
    response_body = fields.JSONField(null=True, description="返回数据")


class ScriptCategory(BaseModel, TimestampMixin):
    """脚本分类 - 支持树形结构"""
    name = fields.CharField(max_length=50, description="分类名称", index=True)
    parent_id = fields.IntField(default=0, description="父分类ID", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:
        table = "script_category"
        table_description = "运维脚本分类表"


class Script(BaseModel, TimestampMixin):
    """运维脚本"""
    title = fields.CharField(max_length=100, description="脚本标题", index=True)
    requirements = fields.JSONField(null=True, description="安装要求列表")
    steps = fields.JSONField(description="安装步骤（键值对）")
    features = fields.TextField(null=True, description="主要功能描述")
    reference_links = fields.JSONField(null=True, description="参考资料链接")
    order = fields.IntField(default=0, description="排序", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)
    
    # 权限字段
    created_by = fields.IntField(null=True, description="创建者ID（贡献者）", index=True)
    viewer_roles = fields.JSONField(default=list, description="可查看的角色ID列表（空表示所有角色可见）")

    # 关联查询 - Tortoise ORM 会自动创建 category_id 字段
    category = fields.ForeignKeyField(
        "models.ScriptCategory",
        related_name="scripts",
        on_delete=fields.CASCADE
    )

    class Meta:
        table = "script"
        table_description = "运维脚本表"


class UploadedFile(BaseModel, TimestampMixin):
    """上传的文件元数据"""
    filename = fields.CharField(max_length=255, description="文件名", index=True)
    original_filename = fields.CharField(max_length=255, description="原始文件名")
    display_name = fields.CharField(max_length=255, null=True, description="显示名称/关联文件名")
    file_path = fields.CharField(max_length=500, description="文件相对路径", index=True, unique=True)
    file_size = fields.BigIntField(default=0, description="文件大小（字节）")
    file_type = fields.CharField(max_length=50, null=True, description="文件类型/扩展名")
    mime_type = fields.CharField(max_length=100, null=True, description="MIME类型")
    
    # 关联的脚本（可选）
    script = fields.ForeignKeyField(
        "models.Script",
        related_name="files",
        on_delete=fields.SET_NULL,
        null=True,
        description="关联的脚本"
    )
    
    uploaded_by = fields.IntField(null=True, description="上传者ID")
    is_active = fields.BooleanField(default=True, description="是否有效", index=True)

    class Meta:
        table = "uploaded_file"
        table_description = "上传文件元数据表"


class ScriptRunLog(BaseModel, TimestampMixin):
    """脚本执行日志"""
    time = fields.DatetimeField(description="执行时间", index=True)
    level = fields.CharField(max_length=20, description="日志级别", index=True)
    info = fields.TextField(description="日志信息")
    cmd = fields.TextField(null=True, description="执行的命令/脚本")
    ip = fields.CharField(max_length=45, description="IP地址", index=True)
    os = fields.CharField(max_length=100, null=True, description="操作系统")
    kernel = fields.CharField(max_length=100, null=True, description="内核版本")
    mac = fields.CharField(max_length=17, null=True, description="MAC地址", index=True)
    username = fields.CharField(max_length=64, null=True, description="用户名", index=True)

    class Meta:
        table = "script_run_logs"
        table_description = "脚本执行日志表"
