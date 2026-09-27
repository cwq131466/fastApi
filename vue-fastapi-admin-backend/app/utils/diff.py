"""差异对比工具函数"""


def compute_diff(old_data: dict, new_data: dict) -> dict:
    """计算两个字典的差异
    
    Args:
        old_data: 旧数据字典
        new_data: 新数据字典
        
    Returns:
        差异字典，格式为 {key: {"old": old_value, "new": new_value}}
    """
    diff = {}
    all_keys = set(list(old_data.keys()) + list(new_data.keys()))
    
    for key in all_keys:
        old_val = old_data.get(key)
        new_val = new_data.get(key)
        if old_val != new_val:
            diff[key] = {"old": old_val, "new": new_val}
    
    return diff


def generate_change_summary(diff: dict) -> str:
    """根据差异生成变更摘要
    
    Args:
        diff: 差异字典
        
    Returns:
        变更摘要字符串
    """
    field_names = {
        "title": "标题",
        "content": "内容",
        "summary": "摘要",
        "cover": "封面",
        "category_id": "分类",
        "view_roles": "查看权限",
        "edit_roles": "编辑权限",
        "tag_ids": "标签",
        "status": "状态",
        "is_top": "置顶",
        "is_recommend": "推荐",
    }
    
    changed_fields = [field_names.get(k, k) for k in diff.keys()]
    
    if not changed_fields:
        return "无变更"
    
    return f"修改了{', '.join(changed_fields)}"
