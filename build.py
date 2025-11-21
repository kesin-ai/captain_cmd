import os
import sys
import shutil
import platform
import subprocess

# 设置标准输出为 UTF-8（Windows 兼容性）
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')  # type: ignore
    except AttributeError:
        # Python < 3.7
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clean():
    """清理之前的构建文件"""
    print("[*] Cleaning up previous builds...")
    dirs_to_remove = [".build", "build", "main.build", "main.dist", "main.onefile-build"]
    for d in dirs_to_remove:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"    Removed {d}")
            except Exception as e:
                print(f"    Failed to remove {d}: {e}")

def get_os_specific_flags():
    """获取特定操作系统的 Nuitka 参数"""
    system = platform.system()
    flags = []
    
    if system == "Windows":
        # Windows 特定参数
        # 如果有图标文件，取消下面注释并修改文件名
        # flags.append("--windows-icon-from-ico=icon.ico")
        pass
    elif system == "Linux":
        # Linux 特定参数
        pass
    elif system == "Darwin":
        # MacOS 特定参数
        flags.append("--macos-create-app-bundle")
    
    return flags

def build():
    """执行 Nuitka 构建"""
    print("[+] Starting Nuitka build...")
    
    output_dir = ".build"
    
    # 基础命令
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",           # 独立环境，不依赖系统 Python
        "--onefile",              # 打包成单文件 (如果想文件夹形式，注释掉这一行)
        "--assume-yes-for-downloads", # 自动下载必要的编译器/依赖
        f"--output-dir={output_dir}", # 输出目录
        "--remove-output",        # 构建后删除临时文件
        "--show-progress",        # 显示进度条
        "--show-memory",          # 显示内存使用
    ]

    # 包含的关键包 (防止动态导入丢失)
    packages_to_include = [
        "langchain",
        "langgraph",
        "deepagents",
        "langchain_core",
        "langchain_mcp_adapters",
        "mcp",
        "rich",
        "prompt_toolkit",
        "pydantic",
        "aiosqlite",
        "utils", # 本地包
        "chat",  # 本地包
    ]
    
    for package in packages_to_include:
        cmd.append(f"--include-package={package}")

    # 排除不必要的标准库以减小体积
    cmd.append("--noinclude-pytest-mode=nofollow")
    cmd.append("--noinclude-setuptools-mode=nofollow")
    # cmd.append("--enable-plugin=anti-bloat") # 启用防膨胀插件

    # 添加系统特定参数
    cmd.extend(get_os_specific_flags())

    # 指定入口文件
    cmd.append("main.py")

    # 打印并执行命令
    print(f"[>] Command: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("[SUCCESS] Build finished successfully!")
    except subprocess.CalledProcessError as e:
        print("[ERROR] Build failed!")
        sys.exit(1)

def post_build():
    """构建后处理：复制配置文件等"""
    print("[*] Running post-build tasks...")
    
    dist_dir = ".build"
    
    # 查找示例配置文件
    # 找 config.example.toml
    possible_configs = "config.example.toml"
    source_config = None
    
    if os.path.exists(possible_configs):
        source_config = possible_configs
            
    if source_config:
        # 目标文件名 config.toml
        target_config = os.path.join(dist_dir, "config.toml")
        try:
            shutil.copy2(source_config, target_config)
            print(f"    Copied template '{source_config}' to '{target_config}'")
        except Exception as e:
            print(f"    Failed to copy config file: {e}")
    else:
        print(f"    [WARNING] No example config file found: {possible_configs}")

    print(f"\n[DONE] All done! executable is in '{dist_dir}' folder.")

if __name__ == "__main__":
    # 确保安装了 Nuitka
    try:
        import nuitka
    except ImportError:
        print("[*] Nuitka not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "nuitka", "zstandard"])

    clean()
    build()
    post_build()

