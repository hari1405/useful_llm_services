from setuptools import find_packages, setup

setup(
    name="decision-council",
    version="0.2.0",
    description="Stress-test your decisions with a panel of AI critics before the room does.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Hariprasad Rengarajan",
    url="https://github.com/hari1405/useful_llm_services",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.40.0",
        "google-genai>=0.5.0",
        "openai>=1.0.0",
        "rich>=13.7.0",
        "typer>=0.12.0",
    ],
    entry_points={
        "console_scripts": [
            "council=council.main:app",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
