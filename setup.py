from setuptools import setup, find_packages

setup(
    name="furever-match",
    version="0.1.0",
    description="A bilingual adoption matching app that helps dogs and people find better-fit forever homes.",
    author="DataHackIL",
    url="https://github.com/DataHackIL/furever_match",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "beautifulsoup4>=4.12.0",
        "flask>=3.0.3",
        "flask-cors>=5.0.0",
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "supabase>=2.0.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={"dev": ["pytest>=8.0.0"]},
    entry_points={
        "console_scripts": [
            "furever-match=furever_match.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
