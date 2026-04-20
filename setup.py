from setuptools import setup, find_packages

setup(
    name="furever-match",
    version="0.1.0",
    description="An app to match forever homes for pets",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/furever_match",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Add your dependencies here
    ],
    entry_points={
        "console_scripts": [
            "furever-match=furever_match.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
