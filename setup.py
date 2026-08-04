from setuptools import find_packages, setup

setup(
    name="ree-lang",
    version="0.2.0",
    description="REE — لغة وصفية متقدمة (متغيرات، شروط، حلقات، دوال، استيراد) لتوليد الامتدادات والمسارات والتشفير والضغط",
    packages=find_packages(include=["ree_lang", "ree_lang.*"]),
    python_requires=">=3.9",
    extras_require={
        "crypto": ["cryptography>=42.0"],
        "img": ["Pillow>=10.0"],
        "compression": ["brotli", "zstandard"],
        "all": ["cryptography>=42.0", "Pillow>=10.0", "brotli", "zstandard"],
        "dev": ["pytest>=8.0"],
    },
    entry_points={
        "console_scripts": [
            "ree=ree_lang.cli:main",
        ],
    },
)
