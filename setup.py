from setuptools import setup, find_packages


setup(
    name="serpent",
    version="0.1",
    packages=find_packages(),
    install_requires=[],
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
    author="samedit66",
    description="Serpent Eiffel Compiler CLI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.13",
)
