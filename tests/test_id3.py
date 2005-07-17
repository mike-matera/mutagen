from os.path import join
from unittest import TestCase
from tests import registerCase
from mutagen.id3 import ID3, BitPaddedInt

try: from sets import Set as set
except ImportError: pass

class _ID3(dict): pass
_23 = _ID3(); _23.version = (2,3,0)
_24 = _ID3(); _24.version = (2,4,0)

class ID3Loading(TestCase):

    empty = join('tests', 'data', 'emptyfile.mp3')
    silence = join('tests', 'data', 'silence-44-s.mp3')

    def test_empty_file(self):
        name = self.empty
        self.assertRaises(ValueError, ID3, filename=name)
        #from_name = ID3(name)
        #obj = open(name, 'rb')
        #from_obj = ID3(fileobj=obj)
        #self.assertEquals(from_name, from_explicit_name)
        #self.assertEquals(from_name, from_obj)

    def test_nonexistent_file(self):
        name = join('tests', 'data', 'does', 'not', 'exist')
        self.assertRaises(EnvironmentError, ID3, name)

    def test_header_empty(self):
        id3 = ID3()
        id3._ID3__fileobj = file(self.empty, 'rb')
        self.assertRaises(EOFError, id3.load_header)

    def test_header_silence(self):
        id3 = ID3()
        id3._ID3__fileobj = file(self.silence, 'rb')
        id3.load_header()
        self.assertEquals(id3.version, (2,3,0))
        self.assertEquals(getattr(id3, '_ID3__size'), 1304)

class ID3Tags(TestCase):
    def setUp(self):
        self.silence = join('tests', 'data', 'silence-44-s.mp3')

    def test_None(self):
        id3 = ID3(self.silence, known_frames={})
        self.assertEquals(0, len(id3.keys()))
        self.assertEquals(9, len(id3.unknown_frames))

    def test_23(self):
        id3 = ID3(self.silence)
        self.assertEquals(8, len(id3.keys()))
        self.assertEquals(0, len(id3.unknown_frames))
        self.assertEquals('Quod Libet Test Data', id3['TALB'])
        self.assertEquals('Silence', str(id3['TCON']))
        self.assertEquals('Silence', str(id3['TIT1']))
        self.assertEquals('Silence', str(id3['TIT2']))
        self.assertEquals(3000, +id3['TLEN'])
        self.assertNotEquals(['piman','jzig'], id3['TPE1'])
        self.assertEquals('02/10', id3['TRCK'])
        self.assertEquals(2, +id3['TRCK'])
        self.assertEquals('2004', id3['TYER'])
        self.assertEquals(2004, +id3['TYER'])

    def test_23_multiframe_hack(self):
        class ID3hack(ID3):
            "Override 'correct' behavior with desired behavior"
            def loaded_frame(self, name, tag):
                if name == 'TXXX' or name == 'WXXX':
                    name += ':' + tag.desc
                if name in self: self[name].extend(tag[:])
                else: self[name] = tag

        id3 = ID3hack(self.silence)
        self.assertEquals(8, len(id3.keys()))
        self.assertEquals(0, len(id3.unknown_frames))
        self.assertEquals('Quod Libet Test Data', id3['TALB'])
        self.assertEquals('Silence', str(id3['TCON']))
        self.assertEquals('Silence', str(id3['TIT1']))
        self.assertEquals('Silence', str(id3['TIT2']))
        self.assertEquals(3000, +id3['TLEN'])
        self.assertEquals(['piman','jzig'], id3['TPE1'])
        self.assertEquals('02/10', id3['TRCK'])
        self.assertEquals(2, +id3['TRCK'])
        self.assertEquals('2004', id3['TYER'])
        self.assertEquals(2004, +id3['TYER'])

class ID3v1Tags(TestCase):
    silence = join('tests', 'data', 'silence-44-s-v1.mp3')
    id3 = ID3(silence)

    def test_album(self):
        self.assertEquals('Quod Libet Test Data', self.id3['TALB'])
    def test_genre(self):
        self.assertEquals('Darkwave', self.id3['TCON'].genres[0])
    def test_title(self):
        self.assertEquals('Silence', str(self.id3['TIT2']))
    def test_artist(self):
        self.assertEquals(['piman'], self.id3['TPE1'])
    def test_track(self):
        self.assertEquals('2', self.id3['TRCK'])
        self.assertEquals(2, +self.id3['TRCK'])
    def test_year(self):
        self.assertEquals('2004', self.id3['TYER'])
        self.assertEquals(2004, +self.id3['TYER'])

    def test_nonascii(self):
        from mutagen.id3 import ParseID3v1
        s = 'TAG%(title)30s%(artist)30s%(album)30s%(year)4s%(cmt)29s\x01\x01'
        s = s % dict(artist='abcd\xe9fg', title='hijklmn\xf3p',
                    album='qrst\xfcv', cmt='wxyz', year='1234')
        tags = ParseID3v1(s)
        self.assertEquals('abcd\xe9fg'.decode('latin1'), tags['TPE1'])
        self.assertEquals('hijklmn\xf3p'.decode('latin1'), tags['TIT2'])
        self.assertEquals('qrst\xfcv'.decode('latin1'), tags['TALB'])
        self.assertEquals('wxyz', tags['COMM'].text)
        self.assertEquals(1234, +tags['TYER'])


def TestReadTags():
    tests = [
    ['TALB', '\x00a/b', 'a/b', '', dict(encoding=0)],
    ['TBPM', '\x00120', '120', 120, dict(encoding=0)],
    ['TCOM', '\x00a/b', 'a/b', '', dict(encoding=0)],
    ['TCON', '\x00(21)Disco', '(21)Disco', '', dict(encoding=0)],
    ['TCOP', '\x001900 c', '1900 c', '', dict(encoding=0)],
    ['TDAT', '\x00a/b', 'a/b', '', dict(encoding=0)],
    ['TDEN', '\x001987', '1987', '', dict(encoding=0, year=[1987])],
    ['TDOR', '\x001987-12', '1987-12', '', dict(encoding=0, year=[1987], month=[12])],
    ['TDRL', '\x001987\x001988', '1987,1988', '', dict(encoding=0, year=[1987,1988])],
    ['TDTG', '\x001987', '1987', '', dict(encoding=0, year=[1987])],
    ['TDLY', '\x001205', '1205', 1205, dict(encoding=0)],
    ['TENC', '\x00a b/c d', 'a b/c d', '', dict(encoding=0)],
    ['TEXT', '\x00a b\x00c d', ['a b', 'c d'], '', dict(encoding=0)],
    ['TFLT', '\x00MPG/3', 'MPG/3', '', dict(encoding=0)],
    ['TIME', '\x001205', '1205', '', dict(encoding=0)],
    ['TIPL', '\x02\x00a\x00\x00\x00b', 'a\x00b', '', dict(encoding=2)],
    ['TIT1', '\x00a/b', 'a/b', '', dict(encoding=0)],
    # TIT2 checks misaligned terminator '\x00\x00' across crosses utf16 chars
    ['TIT2', '\x01\xff\xfe\x38\x00\x00\x38', u'8\u3800', '', dict(encoding=1)],
    ['TIT3', '\x00a/b', 'a/b', '', dict(encoding=0)],
    ['TKEY', '\x00A#m', 'A#m', '', dict(encoding=0)],
    ['TLAN', '\x006241', '6241', '', dict(encoding=0)],
    ['TLEN', '\x006241', '6241', 6241, dict(encoding=0)],
    ['TMED', '\x00med', 'med', '', dict(encoding=0)],
    ['TMOO', '\x00moo', 'moo', '', dict(encoding=0)],
    ['TOAL', '\x00alb', 'alb', '', dict(encoding=0)],
    ['TOFN', '\x0012 : bar', '12 : bar', '', dict(encoding=0)],
    ['TOLY', '\x00lyr', 'lyr', '', dict(encoding=0)],
    ['TOPE', '\x00own/lic', 'own/lic', '', dict(encoding=0)],
    ['TORY', '\x001923', '1923', 1923, dict(encoding=0)],
    ['TOWN', '\x00own/lic', 'own/lic', '', dict(encoding=0)],
    ['TPE1', '\x00ab', ['ab'], '', dict(encoding=0)],
    ['TPE2', '\x00ab\x00cd\x00ef', ['ab','cd','ef'], '', dict(encoding=0)],
    ['TPE3', '\x00ab\x00cd', ['ab','cd'], '', dict(encoding=0)],
    ['TPE4', '\x00ab\x00', ['ab'], '', dict(encoding=0)],
    ['TPOS', '\x0008/32', '08/32', 8, dict(encoding=0)],
    ['TPRO', '\x00pro', 'pro', '', dict(encoding=0)],
    ['TPUB', '\x00pub', 'pub', '', dict(encoding=0)],
    ['TRCK', '\x004/9', '4/9', 4, dict(encoding=0)],
    ['TRDA', '\x00Sun Jun 12', 'Sun Jun 12', '', dict(encoding=0)],
    ['TRSN', '\x00ab/cd', 'ab/cd', '', dict(encoding=0)],
    ['TRSO', '\x00ab', 'ab', '', dict(encoding=0)],
    ['TSIZ', '\x0012345', '12345', 12345, dict(encoding=0)],
    ['TSOA', '\x00ab', 'ab', '', dict(encoding=0)],
    ['TSOP', '\x00ab', 'ab', '', dict(encoding=0)],
    ['TSOT', '\x00ab', 'ab', '', dict(encoding=0)],
    ['TSRC', '\x0012345', '12345', '', dict(encoding=0)],
    ['TSSE', '\x0012345', '12345', '', dict(encoding=0)],
    ['TSST', '\x0012345', '12345', '', dict(encoding=0)],
    ['TYER', '\x002004', '2004', 2004, dict(encoding=0)],

    ['TXXX', '\x00usr\x00a/b', 'a/b', '', dict(encoding=0, desc='usr')],

    ['WCOM', 'http://foo', 'http://foo', '', {}],
    ['WCOP', 'http://bar', 'http://bar', '', {}],
    ['WOAF', 'http://baz', 'http://baz', '', {}],
    ['WOAR', 'http://bar', 'http://bar', '', {}],
    ['WOAS', 'http://bar', 'http://bar', '', {}],
    ['WORS', 'http://bar', 'http://bar', '', {}],
    ['WPAY', 'http://bar', 'http://bar', '', {}],
    ['WPUB', 'http://bar', 'http://bar', '', {}],

    ['IPLS', '\x00a\x00A\x00b\x00B\x00', [['a','A'],['b','B']], '',
        dict(encoding=0)],

    ['MCDI', '\x01\x02\x03\x04', '\x01\x02\x03\x04', '', {}],
    
    #'ETCO', '\x01\x12\x00\x00\x7f\xff', [(18,32767)], '', dict(format=1)],

    ['COMM', '\x00ENUT\x00Com', 'Com', '',
        dict(desc='T', lang='ENU', encoding=0)],
    ['APIC', '\x00-->\x00\x03cover\x00cover.jpg', 'cover.jpg', '',
        dict(mime='-->', type=3, desc='cover', encoding=0)],
    ['USER', '\x00ENUCom', 'Com', '', dict(lang='ENU', encoding=0)],
    ]

    load_tests = {}
    repr_tests = {}
    write_tests = {}
    for i, (tag, data, value, intval, info) in enumerate(tests):
        info = info.copy()

        def test_tag(self, tag=tag, data=data, value=value, intval=intval, info=info):
            from operator import pos
            id3 = __import__('mutagen.id3', globals(), locals(), [tag])
            TAG = getattr(id3, tag)
            tag = TAG.fromData(_23, 0, data)
            self.assertEquals(value, tag)
            if 'encoding' not in info:
                self.assertRaises(AttributeError, getattr, tag, 'encoding')
            for attr, value in info.iteritems():
                t = tag
                if not isinstance(value, list):
                    value = [value]
                    t = [t]
                for value, t in zip(value, iter(t)):
                    self.assertEquals(value, getattr(t, attr))

                    if isinstance(intval, (int,long)):
                        self.assertEquals(intval, pos(t))
                    else:
                        self.assertRaises(TypeError, pos, t)

        load_tests['test_%s_%d' % (tag, i)] = test_tag

        def test_tag_repr(self, tag=tag, data=data):
            from mutagen.id3 import ID3TimeStamp
            id3 = __import__('mutagen.id3', globals(), locals(), [tag])
            TAG = getattr(id3, tag)
            tag = TAG.fromData(_23, 0, data)
            tag2 = eval(repr(tag), {TAG.__name__:TAG,
                    'ID3TimeStamp':ID3TimeStamp})
            self.assertEquals(type(tag), type(tag2))
            for spec in TAG._framespec:
                attr = spec.name
                self.assertEquals(getattr(tag, attr), getattr(tag2, attr))
        repr_tests['test_repr_%s_%d' % (tag, i)] = test_tag_repr

        def test_tag_write(self, tag=tag, data=data):
            id3 = __import__('mutagen.id3', globals(), locals(), [tag])
            TAG = getattr(id3, tag)
            tag = TAG.fromData(_24, 0, data)
            towrite = tag._writeData()
            tag2 = TAG.fromData(_24, 0, towrite)
            for spec in TAG._framespec:
                attr = spec.name
                self.assertEquals(getattr(tag, attr), getattr(tag2, attr))
        write_tests['test_write_%s_%d' % (tag, i)] = test_tag_write

    testcase = type('TestReadTags', (TestCase,), load_tests)
    registerCase(testcase)
    testcase = type('TestReadReprTags', (TestCase,), repr_tests)
    registerCase(testcase)
    testcase = type('TestReadWriteTags', (TestCase,), write_tests)
    registerCase(testcase)
TestReadTags()
del TestReadTags

class BitPaddedIntTest(TestCase):

    def test_zero(self):
        self.assertEquals(BitPaddedInt('\x00\x00\x00\x00'), 0)

    def test_1(self):
        self.assertEquals(BitPaddedInt('\x00\x00\x00\x01'), 1)

    def test_1l(self):
        self.assertEquals(BitPaddedInt('\x01\x00\x00\x00', bigendian=False), 1)

    def test_129(self):
        self.assertEquals(BitPaddedInt('\x00\x00\x01\x01'), 0x81)

    def test_129b(self):
        self.assertEquals(BitPaddedInt('\x00\x00\x01\x81'), 0x81)

    def test_65(self):
        self.assertEquals(BitPaddedInt('\x00\x00\x01\x81', 6), 0x41)

    def test_s0(self):
        self.assertEquals(BitPaddedInt.to_str(0), '\x00\x00\x00\x00')

    def test_s1(self):
        self.assertEquals(BitPaddedInt.to_str(1), '\x00\x00\x00\x01')

    def test_s1l(self):
        self.assertEquals(
            BitPaddedInt.to_str(1, bigendian=False), '\x01\x00\x00\x00')

    def test_s129(self):
        self.assertEquals(BitPaddedInt.to_str(129), '\x00\x00\x01\x01')

    def test_s65(self):
        self.assertEquals(BitPaddedInt.to_str(0x41, 6), '\x00\x00\x01\x01')

    def test_w129(self):
        self.assertEquals(BitPaddedInt.to_str(129, width=2), '\x01\x01')

    def test_w129l(self):
        self.assertEquals(
            BitPaddedInt.to_str(129, width=2, bigendian=False), '\x01\x01')

    def test_wsmall(self):
        self.assertRaises(ValueError, BitPaddedInt.to_str, 129, width=1)

    def test_as_to(self):
        self.assertEquals(BitPaddedInt(238).as_str(), BitPaddedInt.to_str(238))

class FrameSanityChecks(TestCase):

    def test_TF(self):
        from mutagen.id3 import TextFrame
        self.assert_(isinstance(TextFrame(text='text'), TextFrame))

    def test_UF(self):
        from mutagen.id3 import UrlFrame
        self.assert_(isinstance(UrlFrame('url'), UrlFrame))

    def test_WXXX(self):
        from mutagen.id3 import WXXX
        self.assert_(isinstance(WXXX(url='durl'), WXXX))

    def test_NTF(self):
        from mutagen.id3 import NumericTextFrame
        self.assert_(isinstance(NumericTextFrame(text='1'), NumericTextFrame))

    def test_NTPF(self):
        from mutagen.id3 import NumericPartTextFrame
        self.assert_(isinstance(NumericPartTextFrame(text='1/2'), NumericPartTextFrame))

    def test_MTF(self):
        from mutagen.id3 import MultiTextFrame
        self.assert_(isinstance(MultiTextFrame(texts=['a','b']), MultiTextFrame))

    def test_TXXX(self):
        from mutagen.id3 import TXXX
        self.assert_(isinstance(TXXX(desc='d',text='text'), TXXX))

    def test_zlib_latin1(self):
        from mutagen.id3 import TPE1
        tag = TPE1.fromData(_23, 0x80,
                'x\x9cc(\xc9\xc8,V\x00\xa2D\xfd\x92\xd4\xe2\x12\x00&\x7f\x05%')
        self.assertEquals(tag.encoding, 0)
        self.assertEquals(tag, ['this is a/test'])

    def test_utf8(self):
        from mutagen.id3 import TPE1
        tag = TPE1.fromData(_23, 0x00, '\x03this is a test')
        self.assertEquals(tag.encoding, 3)
        self.assertEquals(tag, 'this is a test')

    def test_zlib_utf16(self):
        from mutagen.id3 import TPE1
        tag = TPE1.fromData(_23, 0x80, 'x\x9cc\xfc\xff\xaf\x84!\x83!\x93'
                '\xa1\x98A\x01J&2\xe83\x940\xa4\x02\xd9%\x0c\x00\x87\xc6\x07#')
        self.assertEquals(tag.encoding, 1)
        self.assertEquals(tag, ['this is a/test'])

    def test_unsync_encode(self):
        from mutagen.id3 import unsynch as un
        for d in ('\xff\xff\xff\xff', '\xff\xf0\x0f\x00', '\xff\x00\x0f\xf0'):
            self.assertEquals(d, un.decode(un.encode(d)))
            self.assertNotEqual(d, un.encode(d))

    def test_unsync_decode(self):
        from mutagen.id3 import unsynch as un
        self.assertRaises(ValueError, un.decode, '\xff\xff\xff\xff')
        self.assertRaises(ValueError, un.decode, '\xff\xf0\x0f\x00')

    def test_load_write(self):
        from mutagen.id3 import TPE1, Frames
        from cStringIO import StringIO
        artists= [s.decode('utf8') for s in ['\xc2\xb5', '\xe6\x97\xa5\xe6\x9c\xac']]
        artist = TPE1(encoding=3, text=artists)
        id3 = ID3()
        id3.version = _24.version
        id3._ID3__fileobj = StringIO(id3.save_frame(artist))
        name, tag = id3.load_frame(Frames)
        self.assertEquals('TPE1', name)
        self.assertEquals(artist.text, tag.text)

    def skip_test_harsh(self):
        from os import walk
        from traceback import print_exc
        from mutagen.id3 import ID3NoHeaderError, ID3UnsupportedVersionError
        total = 0
        unsynch = 0
        failures = {}
        missing = []
        for path, dirs, files in walk('/vault/music'):
            for fn in files:
                if not fn.lower().endswith('.mp3'): continue
                ffn = join(path, fn)
                try:
                    total += 1
                    if not total & 0xFF: print total
                    #print ffn
                    id3 = ID3(ffn)
                    for frame, val in id3.iteritems():
                        pass #print frame, str(val)
                except KeyboardInterrupt: raise
                except ID3NoHeaderError:
                    missing.append(ffn)
                except ID3UnsupportedVersionError, err:
                    failures.setdefault(err.__class__, []).append(fn)
                except Exception, err:
                    if err.__class__ not in failures:
                        print_exc()
                    failures.setdefault(err.__class__, []).append(ffn)
                else:
                    if id3.f_unsynch: unsynch += 1

        #for ffn in missing: print ffn
        failcount = 0
        for fail, files in failures.iteritems():
            failcount += len(files)
            print fail, len(files)

        print total-failcount, '/', total, 'success (%d unsynch)' % unsynch

class Genres(TestCase):
    from mutagen.id3 import TCON
    from mutagen._constants import GENRES

    def _g(self, s): return self.TCON(text=s).genres

    def test_empty(self): self.assertEquals(self._g(""), [])

    def test_num(self):
        for i in range(len(self.GENRES)):
            self.assertEquals(self._g("%02d" % i), [self.GENRES[i]])

    def test_parened_num(self):
        for i in range(len(self.GENRES)):
            self.assertEquals(self._g("(%02d)" % i), [self.GENRES[i]])

    def test_unknown(self):
        self.assertEquals(self._g("(255)"), ["Unknown"])
        self.assertEquals(self._g("199"), ["Unknown"])

    def test_parened_multi(self):
        self.assertEquals(self._g("(00)(02)"), ["Blues", "Country"])

    def test_coverremix(self):
        self.assertEquals(self._g("CR"), ["Cover"])
        self.assertEquals(self._g("(CR)"), ["Cover"])
        self.assertEquals(self._g("RX"), ["Remix"])
        self.assertEquals(self._g("(RX)"), ["Remix"])

    def test_parened_text(self):
        self.assertEquals(
            self._g("(00)(02)Real Folk Blues"),
            ["Blues", "Country", "Real Folk Blues"])

    def test_escape(self):
        self.assertEquals(self._g("(0)((A genre)"), ["Blues", "(A genre)"])
        self.assertEquals(self._g("(10)((20)"), ["New Age", "(20)"])

    def test_nullsep(self):
        self.assertEquals(self._g("0\x00A genre"), ["Blues", "A genre"])

    def test_nullsep_empty(self):
        self.assertEquals(self._g("\x000\x00A genre"), ["Blues", "A genre"])

    def test_crazy(self):
        self.assertEquals(
            self._g("(20)(CR)\x0030\x00\x00Another\x00(51)Hooray"),
             ['Alternative', 'Cover', 'Fusion', 'Another',
              'Techno-Industrial', 'Hooray'])

    def test_repeat(self):
        self.assertEquals(self._g("(20)Alternative"), ["Alternative"])
        self.assertEquals(
            self._g("(20)\x00Alternative"), ["Alternative", "Alternative"])

    def test_set_genre(self):
        gen = self.TCON(encoding=0, text="")
        self.assertEquals(gen.genres, [])
        gen.genres = ["a genre", "another"]
        self.assertEquals(gen.genres, ["a genre", "another"])

class BrokenButParsed(TestCase):
    def test_missing_encoding(self):
        from mutagen.id3 import TIT2
        tag = TIT2.fromData(_23, 0x00, 'a test')
        self.assertEquals(0, tag.encoding)
        self.assertEquals('a test', tag)
        self.assertEquals(['a test'], tag)
        self.assertEquals(['a test'], tag.text)

    def test_zerolength_framedata(self):
        from mutagen.id3 import Frames
        id3 = ID3()
        from cStringIO import StringIO
        tail = '\x00' * 6
        for head in 'WOAR TENC TCOP TOPE WXXX'.split():
            data = head + tail
            sio = StringIO(data)
            id3._ID3__fileobj = sio
            name, tag = id3.load_frame(Frames)
            self.assertEquals(name, head)
            self.assertEquals(tag, data)

class TimeStamp(TestCase):
    from mutagen.id3 import ID3TimeStamp as Stamp

    def test_Y(self):
        s = self.Stamp('1234')
        self.assertEquals(s.year, 1234)
        self.assertEquals(s.text, '1234')

    def test_yM(self):
        s = self.Stamp('1234-56')
        self.assertEquals(s.year, 1234)
        self.assertEquals(s.month, 56)
        self.assertEquals(s.text, '1234-56')

    def test_ymD(self):
        s = self.Stamp('1234-56-78')
        self.assertEquals(s.year, 1234)
        self.assertEquals(s.month, 56)
        self.assertEquals(s.day, 78)
        self.assertEquals(s.text, '1234-56-78')

    def test_ymdH(self):
        s = self.Stamp('1234-56-78T12')
        self.assertEquals(s.year, 1234)
        self.assertEquals(s.month, 56)
        self.assertEquals(s.day, 78)
        self.assertEquals(s.hour, 12)
        self.assertEquals(s.text, '1234-56-78T12')

    def test_ymdhM(self):
        s = self.Stamp('1234-56-78T12:34')
        self.assertEquals(s.year, 1234)
        self.assertEquals(s.month, 56)
        self.assertEquals(s.day, 78)
        self.assertEquals(s.hour, 12)
        self.assertEquals(s.minute, 34)
        self.assertEquals(s.text, '1234-56-78T12:34')

    def test_ymdhmS(self):
        s = self.Stamp('1234-56-78T12:34:56')
        self.assertEquals(s.year, 1234)
        self.assertEquals(s.month, 56)
        self.assertEquals(s.day, 78)
        self.assertEquals(s.hour, 12)
        self.assertEquals(s.minute, 34)
        self.assertEquals(s.second, 56)
        self.assertEquals(s.text, '1234-56-78T12:34:56')

    def test_Ymdhms(self):
        s = self.Stamp('1234-56-78T12:34:56')
        s.month = None
        self.assertEquals(s.text, '1234')

    def test_order(self):
        s = self.Stamp('1234')
        t = self.Stamp('1233-12')
        u = self.Stamp('1234-01')

        self.assert_(t < s < u)
        self.assert_(u > s > t)

registerCase(ID3Loading)
registerCase(BitPaddedIntTest)
registerCase(ID3Tags)
registerCase(ID3v1Tags)
registerCase(BrokenButParsed)
registerCase(FrameSanityChecks)
registerCase(Genres)
registerCase(TimeStamp)