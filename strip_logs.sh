#!/bin/sh

cat $1 \
  | grep -v "^AUDIT" \
  | grep -v "^ERROR" \
  | grep -v "^WARNING" \
  | grep -v "^tags:" \
  | grep -v "^time:" \
  | grep -v "^successful:" \
  | grep -v "^Content-Type:" \
  | grep -v "^pythonlogging:" \
  | grep -v "^0" \
  | grep -v "^stderr$" \
  | grep -v "^stdout$" \
  | grep -v "^]$" \
  | grep -v "\[migrate" \
  | grep -v "\[nova.api" \
  | grep -v "\[nova.cells" \
  | grep -v "\[nova.compute" \
  | grep -v "\[nova.network" \
  | grep -v "\[nova.objects" \
  | grep -v "\[nova.openstack.common" \
  | grep -v "\[nova.osapi_compute.wsgi.server" \
  | grep -v "\[nova.quota" \
  | grep -v "\[nova.service" \
  | grep -v "\[nova.utils" \
  | grep -v "\[nova.wsgi" \
  | grep -v "\[stevedore" \
  | grep -v ".driver]" \
  | grep -v "SAWarning:"