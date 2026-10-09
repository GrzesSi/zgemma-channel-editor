import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from KanalowyEditor.channel_types import channel_genre
from KanalowyEditor.core import model,pack,unpack

class PublicTests(unittest.TestCase):
 def test_genres(self):
  for name,genre in [('TVN 24 HD_','Wiadomości'),('Polsat Seriale HD','Seriale'),('KINO POLSKA HD','Filmy'),('Polsat HD','Ogólny'),('CANAL+ EXTRA 4','Sport'),('New Station','Typ nieokreślony')]:
   with self.subTest(name=name): self.assertEqual(channel_genre(name),genre)
 def test_synthetic_archive_and_markers(self):
  files={'lamedb':b'eDVB services /4/\ntransponders\n00000001:0001:0001\n s 1:1:0:0:0:0:0\n/\nend\nservices\n0001:00000001:0001:0001:1:0\nTVN 24 HD\np:Synthetic\nend\n', 'bouquets.tv':b'#NAME TV\n#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.example.tv" ORDER BY bouquet\n','bouquets.radio':b'#NAME Radio\n','userbouquet.example.tv':b'#NAME Synthetic\n#SERVICE 1:0:1:1:1:1:1:0:0:0:\n#SERVICE 1:64:0:0:0:0:0:0:0:0:\n#DESCRIPTION Separator\n'}
  data,blocks=model(files)
  channels=[x for x in data['catalog'].values() if x['type']=='channel']
  markers=[x for x in data['catalog'].values() if x['type']=='marker']
  self.assertEqual(channels[0]['genre'],'Wiadomości')
  self.assertEqual(markers[0]['genre'],'')
  restored=unpack(pack(files))
  for name,value in files.items(): self.assertEqual(restored[name],value)

if __name__=='__main__': unittest.main()
