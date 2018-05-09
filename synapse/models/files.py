import base64
import hashlib

import synapse.exc as s_exc
import synapse.common as s_common
import synapse.lib.types as s_types
import synapse.lib.module as s_module
from synapse.common import addpref, guid

class FileBase(s_types.Type):

    def postTypeInit(self):
        self.setNormFunc(str, self._normPyStr)
        self.indxcmpr['^='] = self.indxByPref

    def indxByPref(self, valu):
        valu = valu.strip().lower().replace('\\', '/')
        indx = valu.encode('utf8')
        return (
            ('pref', indx),
        )

    def _normPyStr(self, valu):

        norm = valu.strip().lower().replace('\\', '/')
        if norm.find('/') != -1:
            mesg = 'file:base may not contain /'
            raise s_exc.BadTypeValu(name=self.name, valu=valu, mesg=mesg)

        subs = {}
        if norm.find('.') != -1:
            subs['ext'] = norm.rsplit('.', 1)[1]

        return norm, {'subs': subs}

    def indx(self, norm):
        return norm.encode('utf8')

class FilePath(s_types.Type):

    def postTypeInit(self):
        self.setNormFunc(str, self._normPyStr)
        self.indxcmpr['^='] = self.indxByPref

    def indxByPref(self, valu):
        valu = value.strip().lower().replace('\\', '/')
        indx = valu.encode('utf8')
        return (
            ('pref', indx),
        )

    def _normPyStr(self, valu):

        lead = ''
        if valu[0] == '/':
            lead = '/'

        valu = valu.strip().lower().replace('\\', '/').strip('/')
        if not valu:
            return ''

        path = []

        for part in valu.split('/'):

            if part == '.':
                continue

            if part == '..':
                if len(path):
                    path.pop()

                continue

            path.append(part)

        fullpath = lead + '/'.join(path)

        subs = {'base': path[-1]}
        if len(path) > 1:
            subs['dir'] = lead + '/'.join(path[:-1])

        return fullpath, {'subs': subs}

    def indx(self, norm):
        return norm.encode('utf8')

class FileBytes(s_types.Type):

    def postTypeInit(self):
        self.setNormFunc(str, self._normPyStr)
        self.setNormFunc(bytes, self._normPyBytes)

    def indx(self, norm):
        return norm.encode('utf8')

    def _normPyStr(self, valu):

        if valu == '*':
            guid = s_common.guid()
            norm = f'guid:{guid}'
            return norm, {}

        if valu.find(':') == -1:
            raise s_exc.BadTypeValu(name=self.name, valu=valu)

        kind, valu = valu.split(':')

        if kind == 'base64':
            byts = base64.b64decode(valu)
            return self._normPyBytes(byts)

        valu = valu.lower()

        if kind == 'hex':
            byts = s_common.uhex(valu)
            return self._normPyBytes(byts)

        if kind == 'guid':

            valu = valu.lower()
            if not s_common.isguid(valu):
                raise s_exc.BadTypeValu(name=self.name, valu=valu)

            return f'guid:{valu}', {}

        if kind == 'sha256':

            if len(valu) != 64:
                raise s_exc.BadTypeValu(name=self.name, valu=valu)

            s_common.uhex(valu)
            return f'sha256:{valu}', {}

        raise s_exc.BadTypeValu(name=self.name, valu=valu)

    def _normPyBytes(self, valu):

        sha256 = hashlib.sha256(valu).hexdigest()

        norm = f'sha256:{sha256}'

        subs = {
            'md5': hashlib.md5(valu).hexdigest(),
            'sha1': hashlib.sha1(valu).hexdigest(),
            'sha256': sha256,
            'sha384': hashlib.sha384(valu).hexdigest(),
            'sha512': hashlib.sha512(valu).hexdigest(),
            'size': len(valu),
        }
        return norm, {'subs': subs}

class FileModule(s_module.CoreModule):

    _mod_name = 'syn:files'

    def initCoreModule(self):
        pass
        #self.core.addSeedCtor('file:bytes:md5', self.seedFileMd5)
        #self.core.addSeedCtor('file:bytes:sha1', self.seedFileSha1)
        # sha256 / sha512 are good enough for now
        #self.core.addSeedCtor('file:bytes:sha256', self.seedFileGoodHash)
        #self.core.addSeedCtor('file:bytes:sha512', self.seedFileGoodHash)

    def getModelDefs(self):
        return (

            ('files', {

                'ctors': (

                    ('file:bytes', 'synapse.models.files.FileBytes', {}, {
                        'doc': 'The file bytes type with SHA256 based primary property.'}),

                    ('file:base', 'synapse.models.files.FileBase', {}, {
                        'doc': 'A file name with no path.',
                        'ex': 'woot.exe'}),

                    ('file:path', 'synapse.models.files.FilePath', {}, {
                        'doc': 'A normalized file path.',
                        'ex': 'c:/windows/system32/calc.exe'}),
                ),

                'types': (
                ),

                'forms': (

                    ('file:bytes', {}, (

                        ('size', ('int', {}), {
                            'doc': 'The file size in bytes.'}),

                        ('md5', ('hash:md5', {}), {'ro': 1,
                            'doc': 'The md5 hash of the file.'}),

                        ('sha1', ('hash:sha1', {}), {'ro': 1,
                            'doc': 'The sha1 hash of the file.'}),

                        ('sha256', ('hash:sha256', {}), {'ro': 1,
                            'doc': 'The sha256 hash of the file.'}),

                        ('sha512', ('hash:sha512', {}), {'ro': 1,
                            'doc': 'The sha512 hash of the file.'}),

                        ('name', ('file:base', {}), {
                              'doc': 'The best known base name for the file.'}),

                        ('mime', ('str', {'lower': 1}), {'defval': '??',
                              'doc': 'The MIME type of the file.'}),

                        ('mime:x509:cn', ('str', {}), {
                            'doc': 'The Common Name (CN) attribute of the x509 Subject.'}),

                        ('mime:pe:size', ('int', {}), {
                            'doc': 'The size of the executable file according to the PE file header.'}),

                        ('mime:pe:imphash', ('guid', {}), {
                            'doc': 'The PE import hash of the file as calculated by Vivisect; this method excludes '
                                'imports referenced as ordinals and may fail to calculate an import hash for files '
                                'that use ordinals.'}),

                        ('mime:pe:compiled', ('time', {}), {
                            'doc': 'The compile time of the file according to the PE header.'}),

                    )),

                    ('file:base', {}, (
                        ('ext', ('str', {}), {'ro': 1,
                            'doc': 'The file extension (if any).'}),
                    )),

                    ('file:path', {}, (
                        ('dir', ('file:path', {}), {'ro': 1,
                            'doc': 'The parent directory.'}),

                        ('base', ('file:path', {}), {'ro': 1,
                            'doc': 'The file base name.'}),

                        ('base:ext', ('str', {}), {'ro': 1,
                            'doc': 'The file extension.'}),
                    )),

                ),

            }),
        )


###############################################################################

    def seedFileGoodHash(self, prop, valu, **props):
        '''
        Hashes that we consider "cardinal enough" to pivot.
        '''
        name = prop.rsplit(':', 1)[-1]
        # Normalize the valu before we go any further
        valu, _ = self.core.getPropNorm(prop, valu)
        props[name] = valu

        # FIXME could we update additional hashes here and
        # maybe (gasp) update the primary property if we
        # finally have enough, then update all other known
        # records that reference this file guid?

        tufo = self.core.getTufoByProp(prop, valu)
        if tufo is not None:
            # add more hashes if we know them...
            tufo = self.core.setTufoProps(tufo, **props)
            return tufo

        iden = self.core.getTypeCast('make:guid', valu)
        tufo = self.core.formTufoByProp('file:bytes', iden, **props)
        # update with any additional hashes we have...
        tufo = self.core.setTufoProps(tufo, **props)
        return tufo

    def seedFileMd5(self, prop, valu, **props):
        valu, _ = self.core.getPropNorm('file:bytes:md5', valu)
        props['md5'] = valu
        return self.core.formTufoByProp('file:bytes', valu, **props)

    def seedFileSha1(self, prop, valu, **props):
        valu, _ = self.core.getPropNorm('file:bytes:sha1', valu)
        props['sha1'] = valu
        valu = guid(valu)
        return self.core.formTufoByProp('file:bytes', valu, **props)

    @staticmethod
    def getBaseModels():
        modl = {
            'types': (
                ('file:bytes', {
                    'subof': 'guid',
                    'doc': 'A unique file identifier'}),

                ('file:sub', {
                    'subof': 'sepr',
                    'sep': '/',
                    'fields': 'parent,file:bytes|child,file:bytes',
                    'doc': 'A parent file that fully contains the specified child file.'}),

                ('file:rawpath', {
                    'ctor': 'synapse.models.files.FileRawPathType',
                    'doc': 'A raw file path in its default (non-normalized) form. Can consist of a directory '
                        'path, a path and file name, or a file name.'}),

                ('file:base', {
                    'ctor': 'synapse.models.files.FileBaseType',
                    'doc': 'A file or directory name (without a full path), such as system32 or foo.exe.'}),

                ('file:path', {
                    'ctor': 'synapse.models.files.FilePathType',
                    'doc': 'A file path that has been normalized by Synapse. Can consist of a directory path, '
                        'a path and file name, or a file name.'}),

                ('file:imgof', {
                    'subof': 'xref',
                    'source': 'file,file:bytes',
                    'doc': 'A file that contains an image of the specified node.'}),

                ('file:txtref', {
                    'subof': 'xref',
                    'source': 'file,file:bytes',
                    'doc': 'A file that contains a reference to the specified node.'}),
            ),

            'forms': (

                ('file:imgof', {}, [
                    ('file', {'ptype': 'file:bytes', 'doc': 'The guid of the file containing the image.', 'ro': 1}),
                    ('xref', {'ptype': 'propvalu', 'ro': 1,
                         'doc': 'The form=valu of the object referenced in the image, e.g., geo:place=<guid_of_place>.'}),
                    ('xref:prop', {'ptype': 'str', 'ro': 1,
                         'doc': 'The property (form) of the referenced object, as specified by the propvalu.'}),
                    ('xref:intval', {'ptype': 'int', 'ro': 1,
                         'doc': 'The value of the property of the referenced object, as specified by the propvalu, if '
                             'the value is an integer.'}),
                    ('xref:strval', {'ptype': 'str', 'ro': 1,
                          'doc': 'The value of the property of the referenced object, as specified by the propvalu, if '
                              'the value is a string.'}),
                ]),

                ('file:txtref', {}, [
                    ('file', {'ptype': 'file:bytes', 'ro': 1,
                        'doc': 'The guid of the file containing the reference.'}),
                    ('xref', {'ptype': 'propvalu', 'ro': 1,
                         'doc': 'The form=valu of the object referenced in the file, e.g., inet:fqdn=foo.com.'}),
                    ('xref:prop', {'ptype': 'str', 'ro': 1,
                         'doc': 'The property (form) of the referenced object, as specified by the propvalu.'}),
                    ('xref:intval', {'ptype': 'int', 'ro': 1,
                         'doc': 'The value of the property of the referenced object, as specified by the propvalu, if '
                             'the value is an integer.'}),
                    ('xref:strval', {'ptype': 'str', 'ro': 1,
                         'doc': 'The value of the property of the referenced object, as specified by the propvalu, '
                             'if the value is a string.'}),
                ]),


                ('file:subfile', {'ptype': 'file:sub'}, (
                    ('parent', {'ptype': 'file:bytes', 'ro': 1,
                        'doc': 'The guid of the parent file.'}),
                    ('child', {'ptype': 'file:bytes', 'ro': 1,
                        'doc': 'The guid of the child file.'}),
                    ('name', {'ptype': 'file:base',
                          'doc': 'The name of the child file. Because a given set of bytes can have any '
                              'number of arbitrary names, this field is used for display purposes only.'}),
                    # TODO others....
                )),
            ),
        }
        name = 'file'
        return ((name, modl), )
