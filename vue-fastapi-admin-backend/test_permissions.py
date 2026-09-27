"""
运维脚本权限系统测试脚本
运行前请确保后端服务已启动
"""
import requests
import json

BASE_URL = "http://127.0.0.1:9099/api/v1"

def test_script_permissions():
    print("=" * 60)
    print("运维脚本权限系统测试")
    print("=" * 60)

    # 1. 登录获取token
    print("\n1. 登录获取token...")
    login_response = requests.post(
        f"{BASE_URL}/base/access_token",
        data={"username": "admin", "password": "123456"}
    )
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.text}")
        return

    token = login_response.json()["data"]["access_token"]
    print(f"✓ 登录成功，token: {token[:20]}...")

    headers = {"token": token, "Content-Type": "application/json"}

    # 2. 获取分类列表
    print("\n2. 获取分类列表...")
    cat_response = requests.get(f"{BASE_URL}/script/category/tree", headers=headers)
    if cat_response.status_code == 200:
        categories = cat_response.json()["data"]
        if categories:
            category_id = categories[0]["id"]
            print(f"✓ 获取到分类，使用第一个分类ID: {category_id}")
        else:
            print("✗ 没有可用分类")
            return
    else:
        print(f"✗ 获取分类失败: {cat_response.text}")
        return

    # 3. 创建脚本（自动设置created_by）
    print("\n3. 创建测试脚本...")
    create_data = {
        "title": "权限测试脚本",
        "category_id": category_id,
        "steps": {"step1": "echo 'hello world'"},
        "features": "测试权限控制功能",
        "viewer_roles": []  # 空表示所有角色可见
    }
    create_response = requests.post(
        f"{BASE_URL}/script/create",
        headers=headers,
        json=create_data
    )
    if create_response.status_code == 200:
        script_id = create_response.json()["data"]["id"]
        created_by = create_response.json()["data"].get("created_by")
        viewer_roles = create_response.json()["data"].get("viewer_roles", [])
        print(f"✓ 脚本创建成功!")
        print(f"  - 脚本ID: {script_id}")
        print(f"  - 创建者ID: {created_by}")
        print(f"  - 查看权限角色: {viewer_roles}")
    else:
        print(f"✗ 创建脚本失败: {create_response.text}")
        return

    # 4. 获取脚本详情（检查creator_info）
    print("\n4. 获取脚本详情...")
    detail_response = requests.get(
        f"{BASE_URL}/script/get",
        headers=headers,
        params={"script_id": script_id}
    )
    if detail_response.status_code == 200:
        script_detail = detail_response.json()["data"]
        creator_info = script_detail.get("creator_info")
        if creator_info:
            print(f"✓ 获取到创建者信息:")
            print(f"  - 用户名: {creator_info.get('username')}")
            print(f"  - 姓名: {creator_info.get('alias')}")
        else:
            print("✗ 未获取到创建者信息")
    else:
        print(f"✗ 获取详情失败: {detail_response.text}")

    # 5. 获取脚本列表（检查权限过滤）
    print("\n5. 获取脚本列表（管理员应看到所有脚本）...")
    list_response = requests.get(
        f"{BASE_URL}/script/list",
        headers=headers,
        params={"category_id": category_id, "page": 1, "page_size": 10}
    )
    if list_response.status_code == 200:
        scripts = list_response.json()["data"]
        total = list_response.json()["total"]
        print(f"✓ 获取到 {total} 个脚本")
        for s in scripts:
            print(f"  - ID: {s['id']}, 标题: {s['title']}, 创建者: {s.get('creator_info', {}).get('username', 'N/A')}")
    else:
        print(f"✗ 获取列表失败: {list_response.text}")

    # 6. 更新脚本的viewer_roles
    print("\n6. 更新脚本查看权限...")
    update_data = {
        "id": script_id,
        "viewer_roles": [2, 3]  # 假设只有角色2和3可以查看
    }
    update_response = requests.post(
        f"{BASE_URL}/script/update",
        headers=headers,
        json=update_data
    )
    if update_response.status_code == 200:
        updated_roles = update_response.json()["data"].get("viewer_roles", [])
        print(f"✓ 更新成功，新的查看权限角色: {updated_roles}")
    else:
        print(f"✗ 更新失败: {update_response.text}")

    # 7. 删除测试脚本
    print("\n7. 清理：删除测试脚本...")
    delete_response = requests.delete(
        f"{BASE_URL}/script/delete",
        headers=headers,
        params={"id": script_id}
    )
    if delete_response.status_code == 200:
        print("✓ 测试脚本已删除")
    else:
        print(f"✗ 删除失败: {delete_response.text}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_script_permissions()
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
