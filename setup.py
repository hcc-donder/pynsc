import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='studentclearinghouse',
    version='0.1',
    description="A module for creating requests for and processing responses from the National Student Clearinghouse",
    url='https://github.com/hcc-donder/studentclearinghouse',
    author='David Onder',
    author_email='donder@haywood.edu',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='GNU GENERAL PUBLIC LICENSE v3.0',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "studentclearinghouse"},
    packages=setuptools.find_packages(where="studentclearinghouse"),
    python_requires=">=3.9",
    zip_safe=False
)