[![Build Status](https://travis-ci.org/VICSES/sms-page-pager.svg?branch=master)](https://travis-ci.org/VICSES/sms-page-pager)
[![Coverage Status](https://coveralls.io/repos/github/VICSES/sms-page-pager/badge.svg?branch=master)](https://coveralls.io/github/VICSES/sms-page-pager?branch=master)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FVICSES%2Fsms-page-pager.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2FVICSES%2Fsms-page-pager?ref=badge_shield)

# Introduction

This project provides a bridge between incoming [Twilio](https://www.twilio.com/) SMS messages and the [VICSES](https://www.ses.vic.gov.au/) online paging interface, Viper. It is a component of the larger [sms-page](https://github.com/VICSES/sms-page) project.

Interactions with Viper interface are managed using the [python-viper](https://github.com/VICSES/python-viper) project.

It is designed to be deployed to an AWS Lambda instance using [zappa](https://github.com/Miserlou/Zappa). 

# Installation

Zappa requires the use of Python 3.6 and a virtual environment.

On a Debian system this can be achieved with the python3.6 package.

```
$ python3.6 -m venv env
$ source env/bin/activate
(env) $ pip3.6 -rrequirements.txt
(env) $ zappa init
(env) $ vim zappa_settings.json
(env) $ zappa deploy prod
```

`zappa_settings.json` must be edited to set the `environment_variables` and ``extra_permissions` as shown in `zappa_settings.example.json`.

# Supporting infrastructure

This project is one component of the [sms-page](https://github.com/VICSES/sms-page) project. It relies on the dynamodb databases provided by [sms-page-rest](https://github.com/VICSES/sms-page-rest).


## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FVICSES%2Fsms-page-pager.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2FVICSES%2Fsms-page-pager?ref=badge_large)