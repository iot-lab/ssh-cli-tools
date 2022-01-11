Changelog
=========

1.0.3
-----

+ fix parallel-ssh version in setup.py (equal to 2.5.4) due to run command error
+ fix tox and lint errors

1.0.2
-----

+ allow to flash binary firmwares on co-controller

1.0.1
-----

+ load IPv6 environment variables before run script

1.0.0
-----

+ bump parallel-ssh to version 2
+ renaming for Open Linux nodes

0.2.3
-----

+ Force parallel-ssh to 1.5.5 because of a breaking refactoring introduced in
  1.6.0

0.2.2
-----

+ Fix --jmespath and --format options not taken into account
+ Remove remaining occurences of old cli-tools names

0.2.0
-----

- deprecate open-a8-cli command
+ add iotlab-ssh command
+ use pytest
+ bump parallelssh version (>= 1.2)

0.1.0
-----

+ add run-cmd, copy-file commands
+ add run-on-frontend option to run-cmd and run-script commands
+ setup Travis CI and Codecov
+ add run-script, wait-for-boot, flash-m3, reset-m3 commands
