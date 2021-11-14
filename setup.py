from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='milight_ibox2',
    version='0.1',
    description='MiLight iBox2 Control with Python',
    long_description=readme(),
    author='Erriez',
    author_email='erriez@users.noreply.github.com',
    url='https://github.com/Erriez/milight_ibox2_control_python',
    license='MIT',
    packages=find_packages(exclude=('tests'))
)
