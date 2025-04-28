#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

# GitHub存储编译后.so文件的仓库信息
GITHUB_USERNAME = "metwhale"
REPO_NAME = "Vorto_Loader"
BRANCH = "main"
MODULE_NAME = "sgxw"
ENTRY_FUNCTION = "main"  # 模块入口函数名

# 代理设置
PROXY_ENABLED = False  # 使用Python的布尔值
PROXY_URL = "https://gh.885666.xyz/"

# 安全设置
VERIFY_SSL = False  # 设置为False可以绕过SSL证书验证

def get_platform_info():
    """获取平台信息"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    return system, machine, python_version

def download_module_file():
    """从GitHub下载模块文件"""
    # 创建本地目录
    module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
    os.makedirs(module_dir, exist_ok=True)
    
    # 检查本地目录中是否已有该模块的文件
    if platform.system().lower() == "windows":
        existing_modules = glob.glob(os.path.join(module_dir, f"{MODULE_NAME}*.pyd"))
    else:
        existing_modules = glob.glob(os.path.join(module_dir, f"{MODULE_NAME}*.so"))
    
    if existing_modules:
        print(f"使用本地模块: {existing_modules[0]}")
        return existing_modules[0]
    
    # 构建GitHub目录URL - 简化版，直接指向模块目录
    github_dir_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/{BRANCH}/{MODULE_NAME}/"
    
    # 获取当前平台信息，用于记录
    system, machine, python_version = get_platform_info()
    print(f"当前平台: {system}, 架构: {machine}, Python版本: {python_version}")
    
    # 确定要尝试下载的文件名模式
    if system == "windows":
        # Windows上的文件名模式
        filename_pattern = f"{MODULE_NAME}.cp{python_version.replace('.', '')}-win_amd64.pyd"
    else:
        # Linux上的文件名模式
        filename_pattern = f"{MODULE_NAME}.cpython-{python_version.replace('.', '')}-{machine}-linux-gnu.so"
    
    # 构建下载URL
    download_url = github_dir_url + filename_pattern
    
    # 如果启用代理，添加代理前缀
    if PROXY_ENABLED and PROXY_URL:
        download_url = PROXY_URL + download_url
        print(f"使用代理下载模块: {download_url}")
    else:
        print(f"直接从GitHub下载模块: {download_url}")
    
    # 创建SSL上下文，可选择是否验证证书
    if not VERIFY_SSL:
        ssl_context = ssl._create_unverified_context()
        print("注意: SSL证书验证已禁用")
    else:
        ssl_context = ssl.create_default_context()
    
    try:
        # 下载到临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        # 使用自定义SSL上下文的请求
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
        
        # 尝试使用不同方法重试
        print("尝试使用备用方法下载...")
        try:
            # 等待一秒后重试
            time.sleep(1)
            
            # 如果使用代理失败，尝试直接下载
            if PROXY_ENABLED and PROXY_URL:
                direct_url = download_url.replace(PROXY_URL, '')
                print(f"尝试直接下载: {direct_url}")
                with urllib.request.urlopen(direct_url, context=ssl_context) as response, open(temp_path, 'wb') as out_file:
                    data = response.read()
                    out_file.write(data)
            else:
                # 如果之前是直接下载，尝试通过curl或wget下载
                print("尝试使用系统命令下载...")
                if system == "windows":
                    # Windows上可能有curl
                    os.system(f'curl -k -L "{download_url}" -o "{temp_path}"')
                else:
                    # Linux/Mac上尝试wget或curl
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
        
        print("所有下载尝试均失败，请手动下载文件并放入modules目录")
        print(f"下载URL: {download_url}")
        print(f"目标路径: {module_dir}")
        sys.exit(1)

def import_and_run_module(module_path):
    """导入并运行加密模块"""
    try:
        # 从文件名中提取模块名（去除扩展名和路径）
        module_filename = os.path.basename(module_path)
        module_name_parts = module_filename.split(".")
        actual_module_name = module_name_parts[0]  # 取第一部分作为模块名
        
        print(f"导入模块: {actual_module_name} (文件: {module_filename})")
        
        spec = importlib.util.spec_from_file_location(actual_module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 尝试调用指定的入口函数
        if hasattr(module, ENTRY_FUNCTION):
            print(f"正在执行模块的{ENTRY_FUNCTION}函数...")
            entry_func = getattr(module, ENTRY_FUNCTION)
            result = entry_func()
            return result
        else:
            print(f"警告: 模块{actual_module_name}中没有找到{ENTRY_FUNCTION}函数")
            
            # 如果没有找到指定的入口函数，尝试找出所有可调用的公共函数
            public_functions = [name for name in dir(module) 
                               if callable(getattr(module, name)) 
                               and not name.startswith('_')]
            
            if public_functions:
                print(f"可用的公共函数: {', '.join(public_functions)}")
                
                # 如果找到了main函数但不是指定的入口函数，询问是否要执行它
                if 'main' in public_functions and ENTRY_FUNCTION != 'main':
                    print(f"找到'main'函数，尝试执行...")
                    result = module.main()
                    return result
            
            return None
    except Exception as e:
        print(f"运行模块时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print(f"准备运行加密模块: {MODULE_NAME}")
    
    # 下载并运行模块
    module_path = download_module_file()
    result = import_and_run_module(module_path)
    
    if result is not None:
        print(f"\n执行结果: {result}")
    
    print("\n程序执行完毕")
