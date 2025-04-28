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

# GitHub存储编译后.so文件的仓库信息
GITHUB_USERNAME = "metwhale"
REPO_NAME = "Vorto_Loader"
BRANCH = "main"
MODULE_NAME = "jhky"

# 代理设置
PROXY_ENABLED = false
PROXY_URL = "https://ghproxy.com/"

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
    github_dir_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/{BRANCH}/build/{MODULE_NAME}/"
    
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
    
    try:
        # 下载到临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        urllib.request.urlretrieve(download_url, temp_path)
        
        # 本地模块路径
        local_path = os.path.join(module_dir, filename_pattern)
        
        # 移动到目标目录
        shutil.move(temp_path, local_path)
        
        print(f"模块下载成功: {local_path}")
        return local_path
    except Exception as e:
        print(f"下载失败: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # 尝试使用/不使用代理的方式重试一次
        if PROXY_ENABLED and PROXY_URL:
            print("尝试不使用代理直接下载...")
            try:
                download_url = download_url.replace(PROXY_URL, "")
                urllib.request.urlretrieve(download_url, temp_path)
                shutil.move(temp_path, local_path)
                print(f"不使用代理下载成功: {local_path}")
                return local_path
            except Exception as e2:
                print(f"重试下载失败: {e2}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        print("无法下载模块文件，请检查网络连接和GitHub仓库是否可访问")
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
        
        # 尝试调用main函数
        if hasattr(module, 'main'):
            print("正在执行模块的main函数...")
            result = module.main()
            return result
        else:
            print(f"警告: 模块{actual_module_name}中没有找到main函数")
            
            # 如果没有main函数，尝试找出所有可调用的公共函数
            public_functions = [name for name in dir(module) 
                               if callable(getattr(module, name)) 
                               and not name.startswith('_')]
            
            if public_functions:
                print(f"可用的公共函数: {', '.join(public_functions)}")
            
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
