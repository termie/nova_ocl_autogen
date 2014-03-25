#!/usr/bin/env python

import json
import re
import sys

def to_schema(name, raw):
  if type(raw) == type({}):
    o = {'name': name,
         'type': 'object',
         'properties': {}
         }
    props = o['properties']
    for k, v in raw.iteritems():
      props[k] = to_schema(k, v)
  elif type(raw) in (type(tuple()), type([])):
    o = {'type': 'array',
         'items': to_schema(name, raw[0])}
  elif type(raw) == str or type(raw) == unicode:
    o = {'type': 'string'}
  elif type(raw) == int:
    o = {'type': 'integer'}
  elif type(raw) == float:
    o = {'type': 'float'}
  elif type(raw) == bool:
    o = {'type': 'bool'}
  elif raw is None:
    o = {'type': 'null'}
  else:
    print name, raw
    return None
  return o


UPPERCASE = re.compile('[A-Z]')


# Notable weird stuff
#
#   update_services
#     multiple different calls in the same call
#     ID field used as the call action


if __name__ == '__main__':
  calls = json.load(open(sys.argv[1]))

  import pprint
  pprint.pprint(calls)

  create_servers = calls['calls']['create_servers']

  params_all = set()
  params_req = set()
  call_count = 0
  calls_with_param = {}

  print
  print
  print
  print "Scanning tests"
  first = True
  for call in create_servers:
    call_count += 1
    call_params = set(call['body']['server'].keys())
    params_all = params_all | call_params
    if first:
      params_req = params_req | call_params
      first = False

    params_req = params_req & call_params
    if 'flavorRef' not in call_params:
      pprint.pprint(call)
    for param in call_params:
      count = calls_with_param.get(param, 0)
      count += 1
      calls_with_param[param] = count

  print "All"
  pprint.pprint(sorted(list(params_all)))
  print "Required"
  pprint.pprint(sorted(list(params_req)))
  print "Optional"
  pprint.pprint(sorted(list(params_all - params_req)))
  print 'Calls:', call_count
  pprint.pprint(calls_with_param)


