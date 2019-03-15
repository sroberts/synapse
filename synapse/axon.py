import asyncio
import hashlib
import logging
import tempfile

import synapse.exc as s_exc
import synapse.common as s_common
import synapse.telepath as s_telepath

import synapse.lib.cell as s_cell
import synapse.lib.base as s_base
import synapse.lib.const as s_const
import synapse.lib.share as s_share
import synapse.lib.lmdbslab as s_lmdbslab
import synapse.lib.slabseqn as s_slabseqn

logger = logging.getLogger(__name__)

CHUNK_SIZE = 16 * s_const.mebibyte

tenmegs = 10 * s_const.mebibyte

class UpLoad(s_base.Base):

    async def __anit__(self, axon):

        await s_base.Base.__anit__(self)

        self.axon = axon
        self.fd = tempfile.SpooledTemporaryFile(max_size=tenmegs)

        self.size = 0
        self.sha256 = hashlib.sha256()

    async def write(self, byts):
        self.size += len(byts)
        self.sha256.update(byts)
        self.fd.write(byts)

    async def save(self):

        sha256 = self.sha256.digest()

        if await self.axon.has(sha256):
            return self.size, sha256

        def genr():

            self.fd.seek(0)

            while True:

                if self.isfini:
                    raise s_exc.IsFini()

                byts = self.fd.read(CHUNK_SIZE)
                if not byts:
                    return

                yield byts

        await self.axon.save(sha256, genr())

        return self.size, sha256

class UpLoadShare(UpLoad, s_share.Share):
    typename = 'upload'
    async def __anit__(self, axon, link):
        await UpLoad.__anit__(self, axon)
        await s_share.Share.__anit__(self, link, None)

class AxonApi(s_cell.CellApi, s_share.Share):

    async def __anit__(self, cell, link, user):
        await s_cell.CellApi.__anit__(self, cell, link, user)
        await s_share.Share.__anit__(self, link, None)

    async def get(self, sha256):
        self.user.allowed(('axon:get',))
        async for byts in self.cell.get(sha256):
            yield byts

    async def has(self, sha256):
        self.user.allowed(('axon:has',))
        return await self.cell.has(sha256)

    async def hashes(self, offs):
        self.user.allowed(('axon:has',))
        async for item in self.cell.hashes(offs):
            yield item

    async def history(self, tick, tock=None):
        self.user.allowed(('axon:has',))
        async for item in self.cell.history(tick, tock=tock):
            yield item

    async def wants(self, sha256s):
        self.user.allowed(('axon:has',))
        return await self.cell.wants(sha256s)

    async def upload(self):
        self.user.allowed(('axon:upload',))
        return await UpLoadShare.anit(self.cell, self.link)

    async def metrics(self):
        self.user.allowed(('axon:has',))
        return await self.cell.metrics()

class Axon(s_cell.Cell):

    cellapi = AxonApi
    confdefs = ()

    async def __anit__(self, dirn, conf=None):

        await s_cell.Cell.__anit__(self, dirn)

        path = s_common.gendir(self.dirn, 'axon.lmdb')
        self.axonslab = await s_lmdbslab.Slab.anit(path)
        self.sizes = self.axonslab.initdb('sizes')
        self.onfini(self.axonslab.fini)

        self.axonhist = s_lmdbslab.Hist(self.axonslab, 'history')

        path = s_common.gendir(self.dirn, 'blob.lmdb')
        self.blobslab = await s_lmdbslab.Slab.anit(path)
        self.blobs = self.blobslab.initdb('blobs')
        self.onfini(self.blobslab.fini)

        self.axonseqn = s_slabseqn.SlabSeqn(self.axonslab, 'axonseqn')

        node = await self.hive.open(('axon', 'metrics'))
        self.axonmetrics = await node.dict()
        self.axonmetrics.setdefault('size:bytes', 0)
        self.axonmetrics.setdefault('file:count', 0)

    def _addSyncItem(self, item):
        self.axonhist.add(item)
        self.axonseqn.add(item)

    async def history(self, tick, tock=None):
        for item in self.axonhist.carve(tick, tock=tock):
            yield item

    async def hashes(self, offs):
        for item in self.axonseqn.iter(offs):
            yield item

    async def get(self, sha256):

        if not await self.has(sha256):
            raise s_exc.NoSuchFile(sha256=s_common.ehex(sha256))

        for lkey, byts in self.blobslab.scanByPref(sha256, db=self.blobs):
            yield byts

    async def put(self, byts):
        sha256 = hashlib.sha256(byts).digest()
        await self.save(sha256, [byts])
        return len(byts), sha256

    async def puts(self, files):
        return [await self.put(b) for b in files]

    async def upload(self):
        return await UpLoad.anit(self)

    async def has(self, sha256):
        return self.axonslab.get(sha256, db=self.sizes) is not None

    async def metrics(self):
        return dict(self.axonmetrics.items())

    async def save(self, sha256, genr):

        byts = self.axonslab.get(sha256, db=self.sizes)
        if byts is not None:
            return int.from_bytes(byts, 'big')

        size = 0
        for i, byts in enumerate(genr):
            size += len(byts)
            lkey = sha256 + i.to_bytes(8, 'big')
            self.blobslab.put(lkey, byts, db=self.blobs)
            await asyncio.sleep(0)

        self._addSyncItem((sha256, size))

        await self.axonmetrics.set('file:count', self.axonmetrics.get('file:count') + 1)
        await self.axonmetrics.set('size:bytes', self.axonmetrics.get('size:bytes') + size)

        self.axonslab.put(sha256, size.to_bytes(8, 'big'), db=self.sizes)

        return size

    async def wants(self, sha256s):
        '''
        Given a list of sha256 bytes, returns a list of the hashes we want bytes for.
        '''
        return [s for s in sha256s if not await self.has(s)]
