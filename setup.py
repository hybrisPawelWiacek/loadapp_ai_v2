from setuptools import setup, find_packages

setup(
    name="loadapp",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'streamlit',
        'requests',
        'plotly',
        'openai',
        'pytest',
    ],
)
