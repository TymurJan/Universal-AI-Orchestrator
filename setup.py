from setuptools import setup, find_packages

setup(
    name="universal-ai-orchestrator",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "anthropic>=0.18.0",
        "openai>=1.10.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "orchestrator=orchestrator:main",
        ],
    },
    author="TymurJan & ГО Талан UA",
    description="Elite AI Governance and Orchestration Framework",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/TymurJan/Universal-AI-Orchestrator",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
