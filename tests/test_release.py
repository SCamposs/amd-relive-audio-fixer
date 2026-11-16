import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from mediafix import engine

def run(args):
    return subprocess.check_output(args, stderr=subprocess.PIPE, **engine.options())

class MediaTests(unittest.TestCase):
    def test_real_operations(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'original.mp4'
            run([engine.tool('ffmpeg'), '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=128x72:rate=10:duration=1', '-f', 'lavfi', '-i', 'anullsrc=channel_layout=7.1:sample_rate=48000', '-t', '1', '-c:v', 'libx264', '-c:a', 'aac', '-metadata', 'title=private test', str(source)])
            outputs = []
            for mode in range(4):
                outputs.append(engine.execute(source, root, mode, 'FLAC', False, lambda _: None, lambda: False))
            for output in outputs:
                run([engine.tool('ffmpeg'), '-v', 'error', '-i', str(output), '-f', 'null', '-'])
            data = json.loads(run([engine.tool('ffprobe'), '-v', 'error', '-show_streams', '-of', 'json', str(outputs[0])]))
            self.assertEqual(next(s for s in data['streams'] if s['codec_type']=='audio')['channels'], 2)
            tags = json.loads(run([engine.tool('ffprobe'), '-v', 'error', '-show_format', '-of', 'json', str(outputs[1])]))
            self.assertNotIn('title', tags['format'].get('tags', {}))
            def digest(path, stream):
                return hashlib.sha256(run([engine.tool('ffmpeg'), '-v', 'error', '-i', str(path), '-map', stream, '-c', 'copy', '-f', 'data', '-'])).hexdigest()
            for stream in ['0:v:0', '0:a:0']:
                self.assertEqual(digest(source, stream), digest(outputs[1], stream))
            original = source.read_bytes()
            with self.assertRaises(InterruptedError):
                engine.execute(source, root, 3, 'FLAC', False, lambda _: None, lambda: True)
            self.assertEqual(source.read_bytes(), original)
            self.assertFalse(list(root.glob('.mediafix-*')))

if __name__ == '__main__':
    unittest.main()
