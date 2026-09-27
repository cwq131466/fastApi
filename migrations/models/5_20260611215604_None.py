from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "api" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "path" VARCHAR(100) NOT NULL  /* API路径 */,
    "method" VARCHAR(6) NOT NULL  /* 请求方法 */,
    "summary" VARCHAR(500) NOT NULL  /* 请求简介 */,
    "tags" VARCHAR(100) NOT NULL  /* API标签 */
);
CREATE INDEX IF NOT EXISTS "idx_api_created_78d19f" ON "api" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_api_updated_643c8b" ON "api" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_api_path_9ed611" ON "api" ("path");
CREATE INDEX IF NOT EXISTS "idx_api_method_a46dfb" ON "api" ("method");
CREATE INDEX IF NOT EXISTS "idx_api_summary_400f73" ON "api" ("summary");
CREATE INDEX IF NOT EXISTS "idx_api_tags_04ae27" ON "api" ("tags");
CREATE TABLE IF NOT EXISTS "blog_article" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "title" VARCHAR(200) NOT NULL  /* 文章标题 */,
    "cover" VARCHAR(500)   /* 封面图片URL */,
    "summary" TEXT   /* 文章摘要 */,
    "content" TEXT NOT NULL  /* 文章内容(Markdown格式) */,
    "status" VARCHAR(20) NOT NULL  DEFAULT 'draft' /* 文章状态 */,
    "category_id" INT NOT NULL  /* 分类ID */,
    "author_id" INT NOT NULL  /* 作者ID */,
    "view_count" INT NOT NULL  DEFAULT 0 /* 阅读次数 */,
    "like_count" INT NOT NULL  DEFAULT 0 /* 点赞数 */,
    "seo_keywords" VARCHAR(200)   /* SEO关键词 */,
    "seo_description" VARCHAR(500)   /* SEO描述 */,
    "is_top" INT NOT NULL  DEFAULT 0 /* 是否置顶 */,
    "is_recommend" INT NOT NULL  DEFAULT 0 /* 是否推荐 */,
    "published_at" TIMESTAMP   /* 发布时间 */
) /* 博客文章表 */;
CREATE INDEX IF NOT EXISTS "idx_blog_articl_created_be417f" ON "blog_article" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_updated_3e0941" ON "blog_article" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_title_8186fa" ON "blog_article" ("title");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_status_bfd5c9" ON "blog_article" ("status");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_categor_f6b61f" ON "blog_article" ("category_id");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_author__70e285" ON "blog_article" ("author_id");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_view_co_dcf85d" ON "blog_article" ("view_count");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_is_top_e44bf0" ON "blog_article" ("is_top");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_is_reco_ae802a" ON "blog_article" ("is_recommend");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_publish_502990" ON "blog_article" ("published_at");
CREATE TABLE IF NOT EXISTS "blog_article_tag" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "article_id" INT NOT NULL  /* 文章ID */,
    "tag_id" INT NOT NULL  /* 标签ID */,
    CONSTRAINT "uid_blog_articl_article_3d27e8" UNIQUE ("article_id", "tag_id")
) /* 文章标签关联表 */;
CREATE INDEX IF NOT EXISTS "idx_blog_articl_created_d8f3ac" ON "blog_article_tag" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_updated_dbcad2" ON "blog_article_tag" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_article_8a8525" ON "blog_article_tag" ("article_id");
CREATE INDEX IF NOT EXISTS "idx_blog_articl_tag_id_e865cd" ON "blog_article_tag" ("tag_id");
CREATE TABLE IF NOT EXISTS "auditlog" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT NOT NULL  /* 用户ID */,
    "username" VARCHAR(64) NOT NULL  DEFAULT '' /* 用户名称 */,
    "module" VARCHAR(64) NOT NULL  DEFAULT '' /* 功能模块 */,
    "summary" VARCHAR(128) NOT NULL  DEFAULT '' /* 请求描述 */,
    "method" VARCHAR(10) NOT NULL  DEFAULT '' /* 请求方法 */,
    "path" VARCHAR(255) NOT NULL  DEFAULT '' /* 请求路径 */,
    "status" INT NOT NULL  DEFAULT -1 /* 状态码 */,
    "response_time" INT NOT NULL  DEFAULT 0 /* 响应时间(单位ms) */,
    "request_args" JSON   /* 请求参数 */,
    "response_body" JSON   /* 返回数据 */
);
CREATE INDEX IF NOT EXISTS "idx_auditlog_created_cc33d0" ON "auditlog" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_auditlog_updated_2f871f" ON "auditlog" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_auditlog_user_id_4b93fa" ON "auditlog" ("user_id");
CREATE INDEX IF NOT EXISTS "idx_auditlog_usernam_b187b3" ON "auditlog" ("username");
CREATE INDEX IF NOT EXISTS "idx_auditlog_module_04058b" ON "auditlog" ("module");
CREATE INDEX IF NOT EXISTS "idx_auditlog_summary_3e27da" ON "auditlog" ("summary");
CREATE INDEX IF NOT EXISTS "idx_auditlog_method_4270a2" ON "auditlog" ("method");
CREATE INDEX IF NOT EXISTS "idx_auditlog_path_b99502" ON "auditlog" ("path");
CREATE INDEX IF NOT EXISTS "idx_auditlog_status_2a72d2" ON "auditlog" ("status");
CREATE INDEX IF NOT EXISTS "idx_auditlog_respons_8caa87" ON "auditlog" ("response_time");
CREATE TABLE IF NOT EXISTS "blog_category" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(50) NOT NULL  /* 分类名称 */,
    "slug" VARCHAR(50) NOT NULL UNIQUE /* 分类别名 */,
    "parent_id" INT NOT NULL  DEFAULT 0 /* 父分类ID */,
    "icon" VARCHAR(100)   /* 分类图标 */,
    "description" VARCHAR(500)   /* 分类描述 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */
) /* 博客分类表 */;
CREATE INDEX IF NOT EXISTS "idx_blog_catego_created_8bd6dc" ON "blog_category" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_blog_catego_updated_ea3e44" ON "blog_category" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_blog_catego_name_23e59e" ON "blog_category" ("name");
CREATE INDEX IF NOT EXISTS "idx_blog_catego_slug_308ed6" ON "blog_category" ("slug");
CREATE INDEX IF NOT EXISTS "idx_blog_catego_parent__bf1904" ON "blog_category" ("parent_id");
CREATE INDEX IF NOT EXISTS "idx_blog_catego_order_6e65ac" ON "blog_category" ("order");
CREATE INDEX IF NOT EXISTS "idx_blog_catego_is_acti_794c5e" ON "blog_category" ("is_active");
CREATE TABLE IF NOT EXISTS "dept" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL UNIQUE /* 部门名称 */,
    "desc" VARCHAR(500)   /* 备注 */,
    "is_deleted" INT NOT NULL  DEFAULT 0 /* 软删除标记 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "parent_id" INT NOT NULL  DEFAULT 0 /* 父部门ID */
);
CREATE INDEX IF NOT EXISTS "idx_dept_created_4b11cf" ON "dept" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_dept_updated_0c0bd1" ON "dept" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_dept_name_c2b9da" ON "dept" ("name");
CREATE INDEX IF NOT EXISTS "idx_dept_is_dele_466228" ON "dept" ("is_deleted");
CREATE INDEX IF NOT EXISTS "idx_dept_order_ddabe1" ON "dept" ("order");
CREATE INDEX IF NOT EXISTS "idx_dept_parent__a71a57" ON "dept" ("parent_id");
CREATE TABLE IF NOT EXISTS "deptclosure" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "ancestor" INT NOT NULL  /* 父代 */,
    "descendant" INT NOT NULL  /* 子代 */,
    "level" INT NOT NULL  DEFAULT 0 /* 深度 */
);
CREATE INDEX IF NOT EXISTS "idx_deptclosure_created_96f6ef" ON "deptclosure" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_updated_41fc08" ON "deptclosure" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_ancesto_fbc4ce" ON "deptclosure" ("ancestor");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_descend_2ae8b1" ON "deptclosure" ("descendant");
CREATE INDEX IF NOT EXISTS "idx_deptclosure_level_ae16b2" ON "deptclosure" ("level");
CREATE TABLE IF NOT EXISTS "menu" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL  /* 菜单名称 */,
    "remark" JSON   /* 保留字段 */,
    "menu_type" VARCHAR(7)   /* 菜单类型 */,
    "icon" VARCHAR(100)   /* 菜单图标 */,
    "path" VARCHAR(100) NOT NULL  /* 菜单路径 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "parent_id" INT NOT NULL  DEFAULT 0 /* 父菜单ID */,
    "is_hidden" INT NOT NULL  DEFAULT 0 /* 是否隐藏 */,
    "component" VARCHAR(100) NOT NULL  /* 组件 */,
    "keepalive" INT NOT NULL  DEFAULT 1 /* 存活 */,
    "redirect" VARCHAR(100)   /* 重定向 */
);
CREATE INDEX IF NOT EXISTS "idx_menu_created_b6922b" ON "menu" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_menu_updated_e6b0a1" ON "menu" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_menu_name_b9b853" ON "menu" ("name");
CREATE INDEX IF NOT EXISTS "idx_menu_path_bf95b2" ON "menu" ("path");
CREATE INDEX IF NOT EXISTS "idx_menu_order_606068" ON "menu" ("order");
CREATE INDEX IF NOT EXISTS "idx_menu_parent__bebd15" ON "menu" ("parent_id");
CREATE TABLE IF NOT EXISTS "role" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(20) NOT NULL UNIQUE /* 角色名称 */,
    "desc" VARCHAR(500)   /* 角色描述 */
);
CREATE INDEX IF NOT EXISTS "idx_role_created_7f5f71" ON "role" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_role_updated_5dd337" ON "role" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_role_name_e5618b" ON "role" ("name");
CREATE TABLE IF NOT EXISTS "script_category" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(50) NOT NULL  /* 分类名称 */,
    "parent_id" INT NOT NULL  DEFAULT 0 /* 父分类ID */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */
) /* 运维脚本分类表 */;
CREATE INDEX IF NOT EXISTS "idx_script_cate_created_305b14" ON "script_category" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_script_cate_updated_3aac44" ON "script_category" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_script_cate_name_57ba4e" ON "script_category" ("name");
CREATE INDEX IF NOT EXISTS "idx_script_cate_parent__849fb7" ON "script_category" ("parent_id");
CREATE INDEX IF NOT EXISTS "idx_script_cate_order_5333bc" ON "script_category" ("order");
CREATE INDEX IF NOT EXISTS "idx_script_cate_is_acti_638da4" ON "script_category" ("is_active");
CREATE TABLE IF NOT EXISTS "script" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "title" VARCHAR(100) NOT NULL  /* 脚本标题 */,
    "requirements" JSON   /* 安装要求列表 */,
    "steps" JSON NOT NULL  /* 安装步骤（键值对） */,
    "features" TEXT   /* 主要功能描述 */,
    "reference_links" JSON   /* 参考资料链接 */,
    "order" INT NOT NULL  DEFAULT 0 /* 排序 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */,
    "category_id" BIGINT NOT NULL REFERENCES "script_category" ("id") ON DELETE CASCADE
) /* 运维脚本表 */;
CREATE INDEX IF NOT EXISTS "idx_script_created_a1aaed" ON "script" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_script_updated_20fb93" ON "script" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_script_title_fcb8e4" ON "script" ("title");
CREATE INDEX IF NOT EXISTS "idx_script_order_9a56d8" ON "script" ("order");
CREATE INDEX IF NOT EXISTS "idx_script_is_acti_916c8e" ON "script" ("is_active");
CREATE TABLE IF NOT EXISTS "script_run_logs" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "time" TIMESTAMP NOT NULL  /* 执行时间 */,
    "level" VARCHAR(20) NOT NULL  /* 日志级别 */,
    "info" TEXT NOT NULL  /* 日志信息 */,
    "cmd" TEXT   /* 执行的命令\/脚本 */,
    "ip" VARCHAR(45) NOT NULL  /* IP地址 */,
    "os" VARCHAR(100)   /* 操作系统 */,
    "kernel" VARCHAR(100)   /* 内核版本 */,
    "mac" VARCHAR(17)   /* MAC地址 */,
    "username" VARCHAR(64)   /* 用户名 */
) /* 脚本执行日志表 */;
CREATE INDEX IF NOT EXISTS "idx_script_run__created_c47711" ON "script_run_logs" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_script_run__updated_b6c5dc" ON "script_run_logs" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_script_run__time_bfdb19" ON "script_run_logs" ("time");
CREATE INDEX IF NOT EXISTS "idx_script_run__level_40fa5a" ON "script_run_logs" ("level");
CREATE INDEX IF NOT EXISTS "idx_script_run__ip_bd6467" ON "script_run_logs" ("ip");
CREATE INDEX IF NOT EXISTS "idx_script_run__mac_711bfb" ON "script_run_logs" ("mac");
CREATE INDEX IF NOT EXISTS "idx_script_run__usernam_9c5b74" ON "script_run_logs" ("username");
CREATE TABLE IF NOT EXISTS "blog_tag" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(30) NOT NULL UNIQUE /* 标签名称 */,
    "slug" VARCHAR(30) NOT NULL UNIQUE /* 标签别名 */,
    "color" VARCHAR(20)   /* 标签颜色 */,
    "article_count" INT NOT NULL  DEFAULT 0 /* 文章数量 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否启用 */
) /* 博客标签表 */;
CREATE INDEX IF NOT EXISTS "idx_blog_tag_created_425a8c" ON "blog_tag" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_blog_tag_updated_6313ea" ON "blog_tag" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_blog_tag_name_86cbce" ON "blog_tag" ("name");
CREATE INDEX IF NOT EXISTS "idx_blog_tag_slug_760b3c" ON "blog_tag" ("slug");
CREATE INDEX IF NOT EXISTS "idx_blog_tag_is_acti_308ca2" ON "blog_tag" ("is_active");
CREATE TABLE IF NOT EXISTS "uploaded_file" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "filename" VARCHAR(255) NOT NULL  /* 文件名 */,
    "original_filename" VARCHAR(255) NOT NULL  /* 原始文件名 */,
    "display_name" VARCHAR(255)   /* 显示名称\/关联文件名 */,
    "file_path" VARCHAR(500) NOT NULL UNIQUE /* 文件相对路径 */,
    "file_size" BIGINT NOT NULL  DEFAULT 0 /* 文件大小（字节） */,
    "file_type" VARCHAR(50)   /* 文件类型\/扩展名 */,
    "mime_type" VARCHAR(100)   /* MIME类型 */,
    "uploaded_by" INT   /* 上传者ID */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否有效 */,
    "script_id" BIGINT REFERENCES "script" ("id") ON DELETE SET NULL /* 关联的脚本 */
) /* 上传文件元数据表 */;
CREATE INDEX IF NOT EXISTS "idx_uploaded_fi_created_164f68" ON "uploaded_file" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_uploaded_fi_updated_25b6d2" ON "uploaded_file" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_uploaded_fi_filenam_a95482" ON "uploaded_file" ("filename");
CREATE INDEX IF NOT EXISTS "idx_uploaded_fi_file_pa_28d5b8" ON "uploaded_file" ("file_path");
CREATE INDEX IF NOT EXISTS "idx_uploaded_fi_is_acti_db0341" ON "uploaded_file" ("is_active");
CREATE TABLE IF NOT EXISTS "user" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "username" VARCHAR(20) NOT NULL UNIQUE /* 用户名称 */,
    "alias" VARCHAR(30)   /* 姓名 */,
    "email" VARCHAR(255) NOT NULL UNIQUE /* 邮箱 */,
    "phone" VARCHAR(20)   /* 电话 */,
    "password" VARCHAR(128)   /* 密码 */,
    "is_active" INT NOT NULL  DEFAULT 1 /* 是否激活 */,
    "is_superuser" INT NOT NULL  DEFAULT 0 /* 是否为超级管理员 */,
    "last_login" TIMESTAMP   /* 最后登录时间 */,
    "dept_id" INT   /* 部门ID */,
    "oauth_access_token" VARCHAR(512)   /* OAuth access token */
);
CREATE INDEX IF NOT EXISTS "idx_user_created_b19d59" ON "user" ("created_at");
CREATE INDEX IF NOT EXISTS "idx_user_updated_dfdb43" ON "user" ("updated_at");
CREATE INDEX IF NOT EXISTS "idx_user_usernam_9987ab" ON "user" ("username");
CREATE INDEX IF NOT EXISTS "idx_user_alias_6f9868" ON "user" ("alias");
CREATE INDEX IF NOT EXISTS "idx_user_email_1b4f1c" ON "user" ("email");
CREATE INDEX IF NOT EXISTS "idx_user_phone_4e3ecc" ON "user" ("phone");
CREATE INDEX IF NOT EXISTS "idx_user_is_acti_83722a" ON "user" ("is_active");
CREATE INDEX IF NOT EXISTS "idx_user_is_supe_b8a218" ON "user" ("is_superuser");
CREATE INDEX IF NOT EXISTS "idx_user_last_lo_af118a" ON "user" ("last_login");
CREATE INDEX IF NOT EXISTS "idx_user_dept_id_d4490b" ON "user" ("dept_id");
CREATE INDEX IF NOT EXISTS "idx_user_oauth_a_1a39d6" ON "user" ("oauth_access_token");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "role_menu" (
    "role_id" BIGINT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE,
    "menu_id" BIGINT NOT NULL REFERENCES "menu" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_role_menu_role_id_90801c" ON "role_menu" ("role_id", "menu_id");
CREATE TABLE IF NOT EXISTS "role_api" (
    "role_id" BIGINT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE,
    "api_id" BIGINT NOT NULL REFERENCES "api" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_role_api_role_id_ba4286" ON "role_api" ("role_id", "api_id");
CREATE TABLE IF NOT EXISTS "user_role" (
    "user_id" BIGINT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "role_id" BIGINT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_user_role_user_id_d0bad3" ON "user_role" ("user_id", "role_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
