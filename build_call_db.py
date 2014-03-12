#!/usr/bin/env python

"""This file builds up an intermediate database of the calls.

It parses the list of calls output by parse_logs.py and uses the Nova API
to match them to controllers.

A bunch of the code to get the nova api is copied directly from the
nova.cmd.api_os_compute code.
"""

import json
import logging
import pprint
import sys

from oslo.config import cfg

from nova import config
from nova.openstack.common import log as logging
from nova import service
from nova import utils
import yaml


CONF = cfg.CONF
CONF.import_opt('enabled_ssl_apis', 'nova.service')


log = logging.getLogger()


def get_server():
  """Get the Nova API server."""
  args = sys.argv
  args.append('--config-dir=etc/nova')
  config.parse_args(args)
  logging.setup("nova")
  utils.monkey_patch()
  should_use_ssl = 'osapi_compute' in CONF.enabled_ssl_apis
  server = service.WSGIService('osapi_compute', use_ssl=should_use_ssl)
  return server


def apirouter(server, v='/v2'):
  """Return the ApiRouter app for the v2 api."""
  v_ref = server.app[(None, v)]
  apirouter = v_ref.application.application.application.application
  return apirouter


def build_call_db(calls, router):
  """Gather up all our json calls, associate them with their controller."""
  failures = []
  o = {}

  for call in calls:
    # we don't care about xml
    if call['content_type'] == 'xml':
      continue

    # v3 does something weird that doesn't work with this approach
    if call['version'] != 'v2':
      continue

    # There are some paths with extra /'s in them
    path = call['path'].replace('//', '/')
    # Strip the "/v2"
    path = path[3:]

    # Separate our query string
    qs = ''
    if '?' in path:
      path, qs = path.split('?')

    method = call['method']

    match, route = match_route(method, path, qs, router)
    if not match:
      failures.append(('Could not match route', call))
      continue

    call_ref = normalize_call(call, match, route)
    if not call_ref:
      failures.append(('Could not parse call', call))
      continue

    call_ref['raw_path'] = call['path']
    call_ref['path'] = path
    call_ref['qs'] = qs

    call_list = o.get(call_ref['name'], [])
    call_list.append(call_ref)
    o[call_ref['name']] = call_list

  return o, failures


def _normalize_controller_name(controller):
  """For now just replace dots."""
  module_name = controller.__module__

  if module_name.startswith('nova.api.openstack.compute.contrib'):
    module_name = '.'.join(module_name.split('.')[5:])
  elif module_name.startswith('nova.api.openstack.compute'):
    module_name = '.'.join(module_name.split('.')[4:])
  elif module_name.startswith('nova.api.openstack'):
    module_name = '.'.join(module_name.split('.')[3:])

  return module_name.replace('.', '_'), controller.__class__.__name__


def match_route(method, path, qs, router):
  environ = {'REQUEST_METHOD': method,
             'QUERY_STRING': qs}

  try:
    match, route = router.map.routematch(path, environ=environ)
  except Exception:
    log.exception('Got no route for (%s, %s, %s)' % (method, path, qs))
    return None, None

  return match, route


def normalize_call(call, match, route):
  call = dict([(str(k), str(v)) for k, v in call.iteritems()])
  controller = match['controller'].controller
  module_name, class_name = _normalize_controller_name(controller)

  body = call['body']
  if call['content_type'] == 'json':
    try:
      body = json.loads(call['body'])
    except Exception:
      log.exception('Failed to parse body')
      return None

  action = match['action']
  if action == 'index':
    real_action = 'list'
    name = 'list_%s' % (module_name,)
  elif action == 'detail':
    real_action = 'list_detail'
    name = 'list_%s_detail' % (module_name,)
  elif action == 'action':
    # The real action is the only key in the top-level dict
    real_action = body.keys()[0]
    name = '%s_%s' % (real_action, module_name)
  else:
    real_action = action
    name = '%s_%s' % (action, module_name)

  route_params = [(k, v) for k, v in match.iteritems()
                  if k not in ('action', 'controller')]

  o = {'body': body,
       'action': action,
       'regpath': route.regpath,
       'route_params': route_params,
       'real_action': real_action,
       'name': name,
       'raw_module': controller.__module__,
       'module_name': module_name,
       'class_name': class_name}
  call.update(o)
  return call


if __name__ == '__main__':
  calls = json.load(open('calls_from_logs.json'))
  server = get_server()
  router = apirouter(server)
  #ar_v3 = apirouter(server, '/v3')

  call_db, failures = build_call_db(calls, router)
  o = {'failures': failures, 'calls': call_db}
  json.dump(o, sys.stdout, indent=2)
