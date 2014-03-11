#from nova.cmd import api_os_compute

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


def main():
    args = sys.argv
    args.append('--config-dir=etc/nova')
    config.parse_args(args)
    logging.setup("nova")
    utils.monkey_patch()
    should_use_ssl = 'osapi_compute' in CONF.enabled_ssl_apis
    server = service.WSGIService('osapi_compute', use_ssl=should_use_ssl)
    print server
    return server
    #service.serve(server, workers=server.workers)
    #service.wait()


def apirouter(server, v='/v2'):
  v_ref = server.app[(None, v)]
  apirouter = v_ref.application.application.application.application
  return apirouter


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


if __name__ == '__main__':
  calls = json.load(open('calls_from_logs.json'))
  server = main()
  ar_v2 = apirouter(server)
  #ar_v3 = apirouter(server, '/v3')

  #sys.exit()
  o = {}

  for call in calls:
    if call['content_type'] == 'xml':
      continue

    method, path = call['method'], call['path']
    # normalize weird images
    path = path.replace('//', '/')
    #print path


    #if call['version'] == 'v2':
    path = path[3:]
    #print path
    qs = ''
    if '?' in path:
      path, qs = path.split('?')

    try:
      if call['version'] == 'v2':
        match, route = ar_v2.map.routematch(path,
                                            environ={'REQUEST_METHOD': method,
                                                     'QUERY_STRING': qs})
      elif call['version'] == 'v3':
        # v3 is doing something weird still ?
        continue
        match, route = ar_v3.map.routematch(path,
                                            environ={'REQUEST_METHOD': method,
                                                     'QUERY_STRING': qs})
      else:
        continue
    except Exception:
      log.exception('Probably got no route for: %s' % path)
      continue

    controller = match['controller'].controller
    class_name = controller.__module__
    if class_name.startswith('nova.api.openstack.compute.contrib'):
      class_name = '.'.join(class_name.split('.')[5:])
    elif class_name.startswith('nova.api.openstack.compute'):
      class_name = '.'.join(class_name.split('.')[4:])


    class_name = class_name.replace('.', '_')
    params = [(k, 'string') for k,v in match.iteritems()
              if k not in ('action', 'controller')]

    action = match['action']
    real_action = None

    if call['content_type'] == 'json':
      try:
        orig_body = json.loads(call['body'])
        # it appears that all resource bodies look the same, so skip
        # to the second level
        if action == 'action':
          real_action = orig_body.items()[0][0]
          #print orig_body

        body = orig_body.items()[0][1]
        if body and hasattr(body, 'iteritems'):
          for k, v in body.iteritems():
            params.append((k, 'string'))
      except Exception:
        log.exception("failed to parse")
        print call['body']
        body = ''
        sys.exit()
    else:
      body = ''

    if action == 'index':
      name = 'list_%s' % class_name
      schema = to_schema(name, orig_body)
    elif action == 'detail':
      name = 'list_%s_detail' % class_name
      schema = to_schema(name, orig_body)
    elif action == 'action':
      name = '%s_%s' % (real_action, class_name)
      schema = to_schema(name, orig_body)
    else:
      name = '%s_%s' % (action, class_name)
      schema = to_schema(name, orig_body)

    d = {method.lower(): params,
         'path': route.regpath,
         'request': schema}

    #print name
    #pprint.pprint(d)
    o[name] = d
    #print match, route.regpath

  #pprint.pprint(o)
  yaml.safe_dump(o,
            stream=open('nova_test.yaml', 'w'),
            default_flow_style=False,
            indent=2,
            width=72)
  #ar.map.routematch

