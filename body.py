import re
import json

CLIENT = 'INFO [nova.tests.integrated.api.client] '

URL_MATCHER = re.compile('Doing (GET|POST|PUT|DELETE|HEAD) on (.*)$')

def main():
  fp = open('new_stripped.log')

  o = []

  collecting = False
  current_url = None
  current_collect = []

  for line in fp:
    line = line.strip('\n')
    if collecting:
      if line.startswith('INFO') or line.startswith('DEBUG'):
        collecting = False
        o.append((current_url, '\n'.join(current_collect)))
        current_collect = []
        current_url = None
      else:
        current_collect.append(line)
    if line.startswith(CLIENT):
      line = line[len(CLIENT):]
      if line in ['Doing GET on /v2', 'Doing GET on /v3', 'Doing GET on /']:
        continue
      if line.startswith('Doing'):
        current_url = URL_MATCHER.match(line).groups()
        if current_url[0] in ('GET', 'DELETE', 'HEAD'):
          o.append((current_url, ''))
      if line.startswith('Body:'):
        current_collect = [line[len('Body: '):]]
        collecting = True

  return o

def normalize(l):
  o = []
  for call, body in l:
    method, path = call
    d = {'method': method,
         'path': path,
         'body': body}

    if path.startswith('/v2'):
      d['version'] = 'v2'
    elif path.startswith('/v3'):
      d['version'] = 'v3'

    if body.startswith('{'):
      d['content_type'] = 'json'
    elif body.startswith('<'):
      d['content_type'] = 'xml'
    else:
      d['content_type'] = 'text'

    o.append(d)
  return o


if __name__ == '__main__':
  o = main()
  o = normalize(o)

  import pprint
  #pprint.pprint(o)
  print json.dumps(o, indent=2)

