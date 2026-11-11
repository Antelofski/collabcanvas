"""Chapter seeking requires correct HTTP byte-range responses."""
import tempfile,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import server
import test_workflow as _workflow

class VideoRanges(unittest.TestCase):
 setUpClass=classmethod(_workflow.WorkflowIntegration.setUpClass.__func__)
 tearDownClass=classmethod(_workflow.WorkflowIntegration.tearDownClass.__func__)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=server.ROOT,prefix='.media-test-');self.path=Path(self.tmp.name)/'sample.mp4';self.path.write_bytes(b'0123456789')
  self.url=self.base+'/'+str(self.path.relative_to(server.ROOT))
 def tearDown(self):self.tmp.cleanup()
 def get(self,range_value=None):
  req=Request(self.url,headers={'Range':range_value} if range_value else {})
  try:r=urlopen(req)
  except HTTPError as error:r=error
  with r:return r.status,dict(r.headers),r.read()
 def test_whole_video_advertises_seek_support(self):
  code,headers,body=self.get();self.assertEqual((code,body),(200,b'0123456789'));self.assertEqual(headers['Accept-Ranges'],'bytes')
 def test_partial_and_open_ended_ranges(self):
  code,headers,body=self.get('bytes=2-5');self.assertEqual((code,body),(206,b'2345'));self.assertEqual(headers['Content-Range'],'bytes 2-5/10');self.assertEqual(headers['Content-Length'],'4')
  self.assertEqual(self.get('bytes=7-')[2],b'789')
 def test_suffix_and_end_clamping(self):
  self.assertEqual(self.get('bytes=-3')[2],b'789');self.assertEqual(self.get('bytes=7-99')[2],b'789')
 def test_invalid_or_unsatisfiable_ranges(self):
  for value in ['bytes=100-','bytes=5-2','bytes=-0','bytes=a-b']:
   code,headers,body=self.get(value);self.assertEqual(code,416);self.assertEqual(headers['Content-Range'],'bytes */10');self.assertEqual(body,b'')
