import os.path
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, "README.md")) as fid:
    README = fid.read()

setup(
    name='ptcompletion',
    version='0.1',
    description='Parallel Tasks Completion for OpenAI API, and more.',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Phantivia',
    author_email='phantivia@gmail.com',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.10',
    install_requires=[
        'openai'
    ],
)