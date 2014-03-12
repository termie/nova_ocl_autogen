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

  # Some random stats
  total_calls_num = len(calls['calls'].keys())
  action_calls = [x for x in calls['calls'].values()
                  if x[0]['action'] == 'action']
  action_calls_num = len(action_calls)
  action_calls_percent = '%.2f' % ((float(action_calls_num) / float(total_calls_num)) * 100)

  camel_calls = [x for x in calls['calls'].keys()
                 if UPPERCASE.search(x)]
  camel_calls_num = len(camel_calls)
  camel_calls_percent = '%.2f' % ((float(camel_calls_num) / float(total_calls_num)) * 100)


  # Module only has "Controller" class
  controller_only_calls = [x for x in calls['calls'].values()
                           if x[0]['class_name'] == 'Controller']

  # Controller Endswith Controller
  controller_endswith_calls = [x for x in calls['calls'].values()
                               if x[0]['class_name'].endswith('Controller')]
  not_controller_endswith_calls = [
      x[0] for x in calls['calls'].values()
      if not x[0]['class_name'].endswith('Controller')]

  # Figure out which module, and how many, have multiple controllers
  multiple_controller_calls = {}
  module_controllers = {}
  for call in calls['calls'].values():
    m_set = module_controllers.get(call[0]['module_name'], set())
    for inst in call:
      m_set.add(inst['class_name'])
    module_controllers[call[0]['module_name']] = m_set

  for module, m_set in module_controllers.iteritems():
    count_list = multiple_controller_calls.get(str(len(m_set)), [])
    count_list.append(module)
    multiple_controller_calls[str(len(m_set))] = count_list


  print 'Total calls:', total_calls_num
  print 'Action calls: %s (%s%%)' % (action_calls_num,
                                     action_calls_percent)

  print 'camelCase calls: %s (%s%%)' % (camel_calls_num,
                                        camel_calls_percent)
  pprint.pprint(camel_calls)
  print '"Controller" only:', len(controller_only_calls)
  print 'Endswith "Controller":', len(controller_endswith_calls)
  print 'Not endswith "Controller:'
  pprint.pprint(not_controller_endswith_calls)
  print 'Number of controllers:'
  pprint.pprint(multiple_controller_calls)


