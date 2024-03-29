# -*- coding: utf-8 -*-
from distutils.core import setup
import setup_translate

pkg = 'Extensions.merlininfo'
setup(name='enigma2-plugin-extensions-merlininfo',
       version='2.1',
       description='Plugin to show useful information in enigma2.',
       packages=[pkg],
       package_dir={pkg: 'plugin'},
       package_data={pkg: ['plugin.png', '*/*.png', 'locale/*/LC_MESSAGES/*.mo']},
       cmdclass=setup_translate.cmdclass, # for translation
      )
