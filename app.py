from flask import Flask
from flask import render_template
from flask import request
from flask_cors import CORS, cross_origin
from networkx.readwrite import json_graph
import networkx as nx
import requests
from bs4 import BeautifulSoup
from collections import defaultdict

app=Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy   dog'
app.config['CORS_HEADERS'] = 'Content-Type'

cors = CORS(app, resources={r"/json": {"origins": "http://localhost:5000"}})
HEADERS = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
    "Accept-Encoding":"gzip, deflate",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}

@app.route('/')
def render_index():
    return render_template('index.html')

@app.route('/json', methods=['GET'])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def get_json():
    url = request.args.get('jsdata')
    return w2json(url)

def w2json(url):
  """fetch DOM elements from a URL and return a networkx graph as JSON"""
  # create an empty graph
  wg = nx.Graph()
  # get response from url
  response = requests.get(url, headers=HEADERS)
  # get soup
  soup = BeautifulSoup(response.content, "lxml")
  # remove garbage
  for script in soup.select('script'):
    script.extract()
  # create an empty node dictionary
  node_dict = {}
  # traverse through soup -> get graph
  _traverse_html(soup, wg, defaultdict(int), _node_dict=node_dict)
  return g2json(wg, node_dict)

def _traverse_html(_soup, _graph, _counter, _parent=None, _node_dict=None):
  """Traverse the DOM elements in a HTML soup and create a networkx graph"""
  for i in _soup.contents:
     if i.name is not None:
       try:
         _name_count = _counter.get(i.name)
         if _parent is not None:
           _graph.add_node(_parent)
           _c_name = i.name if not _name_count else f'{i.name}_{_name_count}'
           _graph.add_edge(_parent, _c_name)
           _node_dict[_c_name] = i
         _counter[i.name] += 1
         _traverse_html(i, _graph, _counter, i.name, _node_dict=_node_dict)
       except AttributeError:
         pass


def g2json(g, node_dict):
  """Convert a networkx graph to JSON format"""
  # make unique tags
  tags = [ parse_tag(key) for key in list(node_dict.keys()) ]
  tag_id = { tag: i for i, tag in enumerate(sorted(set(tags))) }
  # include html tag
  tag_id.update({'html' : len(tag_id) })
  json_g = json_graph.node_link_data(g)
  for i, node in enumerate(json_g['nodes']):
    json_g['nodes'][i]['label'] = tag_id[parse_tag(node['id'])]
    if node['id'] in node_dict:
      json_g['nodes'][i]['attrs'] = node_dict[node['id']].attrs
    else:
      json_g['nodes'][i]['attrs'] = {}
  return json_g


def parse_tag(tag):
  """Parse node id into a HTML tag
  
  eg: div_134 -> div
  """
  return tag[:tag.find('_')] if '_' in tag else tag 


if __name__=="__main__":
    app.run(debug=True)