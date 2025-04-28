#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
sgxw 启动器
自动下载并运行加密模块

原始文件: sgxw.py
加密模块: sgxw_e122031e
"""

import os
import sys
import importlib.util
import urllib.request
import platform
import tempfile
import shutil
import glob
import ssl
import time
import ctypes
import traceback

# GitHub存储编译后.so文件的仓库信息
GITHUB_USERNAME = "metwhale"
REPO_NAME = "Vorto_Loader"
BRANCH = "main"
MODULE_NAME = "sgxw_e122031e"
ENTRY_FUNCTION = "main"
ORIGINAL_FILENAME = "sgxw.py"

# 代理设置
PROXY_ENABLED = False
PROXY_URL = "https://gh.885666.xyz/"

# 安全设置
VERIFY_SSL = False

def get_platform_info():
    """获取平台信息"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    return system, machine, python_version

def download_module_file():
    """从GitHub下载模块文件"""
    # 创建本地目录
    module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules", MODULE_NAME)
    os.makedirs(module_dir, exist_ok=True)
    
    # 检查本地目录中是否已有该模块的文件
    if platform.system().lower() == "windows":
        existing_modules = glob.glob(os.path.join(module_dir, f"{MODULE_NAME}*.pyd"))
    else:
        existing_modules = glob.glob(os.path.join(module_dir, f"{MODULE_NAME}*.so"))
    
    if existing_modules:
        print(f"使用本地模块: {existing_modules[0]}")
        return existing_modules[0]
    
    # 获取当前平台信息
    system, machine, python_version = get_platform_info()
    print(f"当前平台: {system}, 架构: {machine}, Python版本: {python_version}")
    
    # 确定要下载的文件名模式
    if system == "windows":
        filename_pattern = f"{MODULE_NAME}.cp{python_version.replace('.', '')}-win_amd64.pyd"
    else:
        filename_pattern = f"{MODULE_NAME}.cpython-{python_version.replace('.', '')}-{machine}-linux-gnu.so"
    
    # 构建GitHub目录URL
    github_dir_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/{BRANCH}/{MODULE_NAME}/"
    download_url = github_dir_url + filename_pattern
    
    # 如果启用代理，添加代理前缀
    if PROXY_ENABLED and PROXY_URL:
        download_url = PROXY_URL + download_url
        print(f"使用代理下载模块: {download_url}")
    else:
        print(f"直接从GitHub下载模块: {download_url}")
    
    # 创建SSL上下文
    ssl_context = ssl._create_unverified_context() if not VERIFY_SSL else ssl.create_default_context()
    
    # 下载文件
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        # 下载文件
        request = urllib.request.Request(download_url)
        with urllib.request.urlopen(request, context=ssl_context) as response, open(temp_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        
        # 本地模块路径
        local_path = os.path.join(module_dir, filename_pattern)
        
        # 移动到目标目录
        shutil.move(temp_path, local_path)
        
        print(f"模块下载成功: {local_path}")
        return local_path
    except Exception as e:
        print(f"下载失败: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        
        # 尝试备用下载方法
        try:
            time.sleep(1)
            
            # 如果使用代理失败，尝试直接下载
            if PROXY_ENABLED and PROXY_URL:
                direct_url = download_url.replace(PROXY_URL, '')
                print(f"尝试直接下载: {direct_url}")
                with urllib.request.urlopen(direct_url, context=ssl_context) as response, open(temp_path, 'wb') as out_file:
                    data = response.read()
                    out_file.write(data)
            else:
                # 如果之前是直接下载，尝试使用系统命令
                print("尝试使用系统命令下载...")
                if system == "windows":
                    os.system(f'curl -k -L "{download_url}" -o "{temp_path}"')
                else:
                    os.system(f'wget --no-check-certificate -O "{temp_path}" "{download_url}" || ' +
                              f'curl -k -L "{download_url}" -o "{temp_path}"')
            
            # 检查文件是否下载成功
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                # 移动到目标目录
                shutil.move(temp_path, local_path)
                print(f"使用备用方法下载成功: {local_path}")
                return local_path
            else:
                print("备用下载方法失败：文件为空或不存在")
        except Exception as e2:
            print(f"备用下载方法也失败: {e2}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
        
        print("所有下载尝试均失败")
        print(f"下载URL: {download_url}")
        print(f"目标路径: {module_dir}")
        sys.exit(1)

def import_and_run_module(module_path):
    """导入并运行加密模块"""
    try:
        # 从文件名中提取模块名
        module_filename = os.path.basename(module_path)
        module_name_parts = module_filename.split(".")
        actual_module_name = module_name_parts[0]
        
        print(f"导入模块: {actual_module_name} (文件: {module_filename})")
        
        # 方法1: 使用importlib导入
        try:
            spec = importlib.util.spec_from_file_location(actual_module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查看模块中的所有属性
            print("模块属性:")
            all_attributes = dir(module)
            for attr in all_attributes:
                if not attr.startswith("__"):
                    print(f" - {attr}")
            
            # 查找特殊导出函数
            export_function = f"__pyx_export_{ENTRY_FUNCTION}"
            if hasattr(module, export_function):
                print(f"使用导出函数: {export_function}")
                result = getattr(module, export_function)()
                return result
            
            # 查找标准入口函数
            if hasattr(module, ENTRY_FUNCTION):
                print(f"使用标准入口函数: {ENTRY_FUNCTION}")
                entry_func = getattr(module, ENTRY_FUNCTION)
                result = entry_func()
                return result
            
            # 尝试常见的入口函数名
            common_entries = ["main", "run", "__main__", "start", "execute"]
            for entry_name in common_entries:
                if hasattr(module, entry_name):
                    print(f"使用替代入口函数: {entry_name}")
                    entry_func = getattr(module, entry_name)
                    result = entry_func()
                    return result
            
            print("未找到可识别的入口函数，尝试方法2")
            raise ImportError("未找到入口函数")
            
        except Exception as e:
            print(f"方法1导入失败: {e}")
            
            # 方法2: 使用ctypes直接加载
            try:
                print("尝试使用ctypes加载模块")
                if platform.system().lower() == "windows":
                    lib = ctypes.WinDLL(module_path)
                else:
                    lib = ctypes.CDLL(module_path)
                
                # 查看库中的所有函数
                print("库中可用函数:")
                for item in dir(lib):
                    if not item.startswith("_"):
                        print(f" - {item}")
                
                # 查找并调用特殊导出函数
                export_function = f"__pyx_export_{ENTRY_FUNCTION}"
                if hasattr(lib, export_function):
                    print(f"使用ctypes调用: {export_function}")
                    func = getattr(lib, export_function)
                    result = func()
                    return result
                
                print("无法使用ctypes找到导出函数，尝试方法3")
                raise ImportError("无可用函数")
                
            except Exception as e2:
                print(f"方法2也失败: {e2}")
                
                # 方法3: 尝试exec运行代码
                try:
                    print("尝试方法3: 使用exec执行代码")
                    # 使用普通字符串并format而不是f-string嵌套，避免语法错误
                    exec_code = """
import sys
import os

# 将模块目录添加到路径
module_dir = os.path.dirname("0")
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

# 导入模块并执行
try:
    import 1
    
    # 尝试不同的入口函数
    entry_points = ["2", "main", "run", "__main__", "start"]
    for entry in entry_points:
        if hasattr(1, entry):
            print(f"执行入口函数: {entry}")
            result = getattr(1, entry)()
            print(f"执行结果: {result}")
            break
    else:
        print("未找到可执行的入口函数")
        
        # 列出所有可调用的函数
        callables = [name for name in dir(1) if callable(getattr(1, name)) and not name.startswith("_")]
        if callables:
            print(f"可用函数: {callables}")
            # 尝试第一个可用函数
            func_name = callables[0]
            print(f"尝试执行: {func_name}")
            result = getattr(1, func_name)()
            print(f"执行结果: {result}")
except Exception as e:
    print(f"方法3执行出错: {e}")
    import traceback
    traceback.print_exc()
""".format(module_path, actual_module_name, ENTRY_FUNCTION)
                    exec(exec_code)
                    print("方法3执行完成")
                except Exception as e3:
                    print(f"所有方法都失败: {e3}")
                    traceback.print_exc()
    except Exception as e:
        print(f"整体导入过程失败: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print(f"==================================================")
    print(f"准备运行 sgxw 加密模块")
    print(f"==================================================")
    
    # 下载并运行模块
    module_path = download_module_file()
    result = import_and_run_module(module_path)
    
    if result is not None:
        print(f"\n执行结果: {result}")
    
    print("\n程序执行完毕")
