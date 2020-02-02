from setuptools import setup

install_requires = [
      "numpy"
]

extras_require = {
      "docs": ["pdoc3"]
}

setup(name="pynvx",
      version="0.3",
      description="NVX dll wrapper for python",
      url="https://github.com/andreasxp/pynvx",
      author="Andrey Zhukov",
      author_email="andres.zhukov@gmail.com",
      license="MIT",
      install_requires=install_requires,
      extras_require=extras_require
)