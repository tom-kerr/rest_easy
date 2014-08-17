from distutils.core import setup

setup(name='rest_easy',
      author='Tom Kerr',
      author_email='thomkerr@gmail.com',
      url='https://github.com/reklaklislaw/rest_easy',
      description='A python module that dynamically creates wrappers for RESTful APIs from YAML markup.',
      packages=['rest_easy', 'rest_easy.core'],
      package_data={'rest_easy.core': ['sources/*.yaml']},
      requires=['lxml', 'yaml', 'xmltodict', 'dicttoxml'])
