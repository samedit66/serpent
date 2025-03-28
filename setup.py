import os
from setuptools.command.build_py import build_py as _build_py
from setuptools import setup, find_packages
import subprocess


class build_py(_build_py):
    def run(self):
        current_dir = os.path.abspath(os.path.dirname(__file__))
        subprocess.run(["make"], cwd=current_dir, check=True)
        super().run()


setup(
    name="serpent",
    version="0.1",
    packages=find_packages(),
    install_requires=[],
    extras_require={
        "tqdm": ["tqdm"]
    },
    include_package_data=True,
    package_data={
        "serpent": [
            "resources/build/*",
            "resources/stdlib/*",
            "resources/rtl/*",
        ],
    },
    entry_points={
        "console_scripts": [
            "serpent=serpent.cmd:main",
        ],
    },
    cmdclass={
        "build_py": build_py
    },
    author="samedit66",
    author_email="samedit66@yandex.ru",
    description="Serpent Eiffel Compiler CLI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13",
)
